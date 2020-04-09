import dask.array as da
import glob
import h5py
import numpy as np
import os
from argparse import ArgumentParser
from collections import defaultdict
from numpy.lib.recfunctions import stack_arrays, append_fields, drop_fields
from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import RandomizedPCA
from sklearn.externals.joblib import dump as jdump, load as jload
from sklearn.linear_model import LogisticRegression

from kate_masks import get_kate_mask
from superman.baseline import ALS
from superman.preprocess import libs_norm3
from superman.utils import ALAMOS_MASK


class WebModel(object):
    def __init__(self):
        raise NotImplementedError(
            'Cannot instantiate the abstract class: WebModel')

    def write_model(self, fname=None):
        if fname is None:
            fname = self.name + '.pkl'
        jdump(self.__dict__, os.path.join(self.output_dir, fname), compress=3)

    def load_model(self, fname=None):
        if fname is None:
            fname = self.name + '.pkl'
        members = jload(os.path.join(self.output_dir, fname))
        # prevent loading a stale filepath
        for key in ('output_dir', 'ccs_dir', 'lanl_file', 'moc_dir',
                    'libs_mix_file'):
            members.pop(key, None)
        self.__dict__.update(members)

    def _load_big_mars(self):
        file_pattern = os.path.join(self.ccs_dir, 'ccs.%03d.hdf5')
        f = h5py.File(file_pattern, mode='r', driver='family', libver='latest')
        return da.from_array(f['/spectra'], chunks=(1000, 6144),
                             name='mars_big')

    def _load_big_mars_meta(self):
        file_pattern = os.path.join(self.ccs_dir, 'ccs_meta.npz')
        return np.load(file_pattern)

    def predict_new_mars(self):
        pred_fname = self.name + '_mars_preds.npz'
        pred_file = os.path.join(self.output_dir, pred_fname)
        try:
            predictions = np.load(pred_file)
            # Get only the un-predicted spectra
            num_preds = len(predictions[predictions.files[0]])
        except IOError as e:
            print 'Warning: unable to read preds file'
            print e
            predictions = defaultdict(list)
            num_preds = 0
        spectra = self._load_big_mars()[num_preds:]
        if spectra.shape[0] == 0:
            print 'No spectra to predict'
            return
        all_predictions = {}
        if self.multitask:
            print 'Predicting all elements...'
            multi_preds = self.predict(spectra)
            print 'Done'
            elements = self.elements
        else:
            elements = self.model.keys()
        for i, element in enumerate(elements):
            if self.multitask:
                new_pred = multi_preds[:,i]
            else:
                print 'Predicting element %s...' % element
                new_pred = self.predict(spectra, element)
                print 'Done'
            old_pred = predictions[element]
            all_predictions[element] = np.append(old_pred, new_pred)
        print 'Saving results to', pred_file
        np.savez(pred_file, **all_predictions)

    def train(self):
        # Load New Los Alamos data for fitting
        print 'Loading LANL data for fitting...'
        lanl = h5py.File(self.lanl_file, mode='r', libver='latest')
        lanl_spectra = lanl['/spectra']
        lanl_comps = lanl['/composition']
        if self.multitask:
            print 'Training multitask model...'
            comp = np.array(lanl_comps.values()).T
            self.fit(lanl_spectra, comp, lanl_comps.keys())
        else:
            for element, comp in lanl_comps.iteritems():
                print 'Training model for %s...' % element
                self.fit(lanl_spectra, comp, element)
        self.write_model()

    def predict_all_mars(self):
        pred_fname = self.name + '_mars_preds.npz'
        # Load Mars data for predicting
        print 'Loading Mars data...'
        msl_spectra = self._load_big_mars()
        if self.multitask:
            print 'Predicting Mars Big...'
            pred = self.predict(msl_spectra)
            predictions = dict(zip(self.elements, pred.T))
        else:
            predictions = self.predict_all(msl_spectra, verbose=True)
        outfile = os.path.join(self.output_dir, pred_fname)
        np.savez(outfile, **predictions)
        return predictions


class MSLModel(WebModel):
    '''
    The current (single) PLS model used by the team
    PLS-10 w/ masking + norm3
    '''

    n_components = {'Al2O3': 1, 'TiO2': 4, 'Fe2O3': 7, 'SiO2': 7,
                    'MgO': 3, 'Na2O': 5, 'CaO': 2, 'K2O': 1, 'MnO': 7}

    def __init__(self, output_dir, ccs_dir, lanl_file, **kwargs):
        self.output_dir = output_dir
        self.ccs_dir = ccs_dir
        self.lanl_file = lanl_file

        self.model = {}
        self.multitask = False
        self.name = 'msl_model'

    def fit(self, data, composition, element, mask=ALAMOS_MASK):
        self.model[element] = PLSRegression(
            n_components=self.n_components[element], scale=False)
        data = libs_norm3(data)[:, mask]
        self.model[element].fit(data, composition)

    def predict(self, data, element, mask=ALAMOS_MASK, norm3=True, clip=True):
        if norm3:
            data = libs_norm3(data)[:, mask]
        else:
            data = data[:, mask]
        predictions = self.model[element].predict(data, copy=False).ravel()
        if clip:
            predictions = np.clip(predictions, 0, 100)
        else:
            predictions[predictions < 0] = 0
        return predictions

    def predict_all(self, data, verbose=False):
        predictions = {}
        data = libs_norm3(data)
        for element in self.model:
            if verbose:
                print 'Predicting %s...' % element
            predictions[element] = self.predict(data, element, norm3=False)
        return predictions


class MSLMultiModel(WebModel):
    ''' a Multitask version of MSLModel '''
    def __init__(self, output_dir, ccs_dir, lanl_file, n_components=10, **kwargs):
        self.output_dir = output_dir
        self.ccs_dir = ccs_dir
        self.lanl_file = lanl_file

        self.n_components = n_components
        self.model = PLSRegression(n_components=n_components, scale=False)
        self.multitask = True
        self.name = 'msl_multi_model'

    def fit(self, data, composition, elements):
        self.elements = elements  # order matters
        data = libs_norm3(data[:, ALAMOS_MASK])
        self.model.fit(data, composition)

    def predict(self, data, mask=ALAMOS_MASK, clip=True):
        data = libs_norm3(data[:, mask])
        predictions = self.model.predict(data, copy=False)
        if predictions:
            predictions = np.clip(predictions, 0, 100)
        else:
            predictions[predictions < 0] = 0
        return predictions


class MixedModel(MSLModel):
    ''' our current best in-house PLS model'''

    n_components = {'Al2O3': 3, 'Ni': 1, 'Zn': 2, 'Mn': 11, 'Co': 2,
                    'TiO2': 1, 'Fe2O3': 6, 'SiO2': 11, 'MgO': 3,
                    'Na2O': 2, 'CaO': 3, 'K2O': 4, 'MnO': 2, 'Cr': 6}

    def __init__(self, output_dir, ccs_dir, libs_mix_file, **kwargs):
        self.output_dir = output_dir
        self.ccs_dir = ccs_dir
        self.name = 'mixed_model'
        self.model = {}
        self.multitask = False
        try:
            data = np.load(libs_mix_file)
            self.spectra = data['data']
            self.channels = data['data_names']
            self.datasets = data['key']['dataset']
            self.compositions = data['target']
            self.elements = data['target_names']
            self.laserpowers = data['key']['laserpower']
            self.samples = data['key']['sample']
            self.targets = data['key']['target']
        except IOError as e:
            print 'Error: unable to load big mixed data file'
            print e

    def train(self):
        print 'Loading Big Multi File...'
        # non-BLR
        mhc_mask = (self.datasets=='MHC Big')
        lanl_mask = (self.datasets=='LANL 400')
        mixed_mask = (mhc_mask | lanl_mask)
        als = ALS(.01, 1e6)
        mixed_spectra = als.fit_transform(None, self.spectra[mixed_mask])
        mixed_comp = self.compositions[mixed_mask]
        # BLR already (CCS files)
        cal_mask = (self.datasets=='Cal Targets')
        cal_mask &= (self.targets!='TITANIUM')
        cal_mask &= (self.targets!='GRAPHITE')
        cal_mask &= (self.targets!='MACUSANITE')
        mixed_spectra = np.vstack((mixed_spectra, self.spectra[cal_mask]))
        mixed_comp = np.vstack((mixed_comp, self.compositions[cal_mask]))
        for eid, element in enumerate(self.elements):
            print 'Training model for %s...' % element
            nan_mask = ~np.isnan(mixed_comp[:, eid])
            self.fit(mixed_spectra[nan_mask], mixed_comp[nan_mask, eid],
                     element)
        self.write_model()

    def fit(self, data, composition, element):
        if element.lower() in ['ni', 'zn', 'mn', 'cr', 'co']:
            trace_mask = get_kate_mask(self.channels, element)
            MSLModel.fit(self, data, composition, element, mask=trace_mask)
        else:
            MSLModel.fit(self, data, composition, element)

    def predict(self, data, element, norm3=True):
        if element.lower() in ['ni', 'zn', 'mn', 'cr', 'co']:
            trace_mask = get_kate_mask(self.channels, element)
            return MSLModel.predict(self, data, element, mask=trace_mask,
                                    clip=False, norm3=norm3)
        else:
            return MSLModel.predict(self, data, element, norm3=norm3)


class SafeLogisticRegression(LogisticRegression):
    def safe_predict(self, samples, min_prob):
        preds = LogisticRegression.predict(self, samples)
        probs = self.predict_proba(samples)
        preds[np.max(probs, 1) < min_prob] = 0
        return preds


class DustClassifier(MSLMultiModel):
    def __init__(self, output_dir, ccs_dir, n_pca_components=200,
                 min_prob=.9, regular=.1, **kwargs):
        self.output_dir = output_dir
        self.ccs_dir = ccs_dir
        self.name = 'dust_classifier'
        self.elements = ['Is dust?']
        self.multitask = True
        self.n_pca_components = n_pca_components
        self.min_prob = min_prob
        self.regular = regular

    def train(self):
        msl_spectra = self._load_big_mars()
        msl_meta = self._load_big_mars_meta()
        # no drill holes b/c no dust
        mask = np.array([name.lower().find('drill') < 0
                         for name in msl_meta['names']])
        # no calibration targets b/c shot too frequently
        mask &= np.array([name.find('Cal Target') < 0
                          for name in msl_meta['names']])
        dust_mask = mask & (msl_meta['numbers']==1)
        not_dust_mask = mask & (msl_meta['numbers']==30)
        spectra = np.vstack((msl_spectra[dust_mask,:],
                             msl_spectra[not_dust_mask,:]))
        labels = np.ones(spectra.shape[0])
        labels[np.count_nonzero(dust_mask):] = 0
        print 'Training dust classifier...'
        self.fit(spectra, labels)
        self.write_model()

    def fit(self, data, labels):
        self.model = SafeLogisticRegression(C=self.regular)
        self.pca = RandomizedPCA(n_components=self.n_pca_components)
        pca_data = self.pca.fit_transform(data)
        self.model.fit(pca_data, labels)

    def predict(self, data):
        pca_data = self.pca.transform(data)
        preds = self.model.safe_predict(pca_data, min_prob=self.min_prob)
        return preds.reshape((len(preds), 1))


class MOCModel(WebModel):
    def __init__(self, output_dir, ccs_dir, moc_dir, **kwargs):
        self.output_dir = output_dir
        self.ccs_dir = ccs_dir
        self.moc_dir = moc_dir
        self.name = 'moc_model'

    def _convert_Fe(self, moc):
        moc = append_fields(moc, 'Fe2O3', moc['FeOT'] * 1.11)
        moc = drop_fields(moc, 'FeOT')
        return moc

    def _compile_moc_data(self):
        # a bit of a hackosaurus-rex this one
        cols = (0,2,6,10,14,18,22,26,30)
        dtypes = 'S75'
        converters = {0: lambda x: x.strip('"')}
        for i in cols[1:]:
            dtypes += ',f8'
            converters[i] = lambda x: float(x.strip('"'))
        mocs = []
        for fname in glob.glob(os.path.join(self.moc_dir, 'moc_*.csv')):
            moc = np.genfromtxt(fname, dtype=dtypes, converters=converters,
                                delimiter=',', skip_header=6, usecols=cols,
                                names=True)
            mocs.append(self._convert_Fe(moc))
        return stack_arrays(mocs)

    def _predict_ids(self, ids):
        moc_data = self._compile_moc_data()
        moc_elements = [name for name in moc_data.dtype.names if name != 'File']
        moc_ids = np.array([loc_id.split('CCS')[0]
                            for loc_id in moc_data['File']])
        predictions = dict((elem, np.empty(ids.shape[0]))
                           for elem in moc_elements)
        for loc_id in np.unique(ids):
            moc_mask = moc_ids==loc_id
            loc_mask = ids==loc_id
            for elem, preds in predictions.iteritems():
                if moc_mask.any():
                    preds[loc_mask] = np.unique(moc_data[elem][moc_mask])
                else:
                    preds[loc_mask] = np.nan
        return predictions

    def predict_all_mars(self):
        msl_meta = self._load_big_mars_meta()
        predictions = self._predict_ids(msl_meta['ids'])
        pred_fname = self.name + '_mars_preds.npz'
        outfile = os.path.join(self.output_dir, pred_fname)
        np.savez(outfile, **predictions)
        return predictions

    def predict_new_mars(self):
        pred_fname = self.name + '_mars_preds.npz'
        pred_file = os.path.join(self.output_dir, pred_fname)
        try:
            predictions = np.load(pred_file)
            num_preds = len(predictions[predictions.files[0]])
        except IOError as e:
            print 'Warning: unable to read preds file'
            print e
            predictions = defaultdict(list)
            num_preds = 0
        ids = self._load_big_mars_meta()['ids'][num_preds:]
        if ids.shape[0] == 0:
            print 'No spectra to predict'
            return
        new_predictions = self._predict_ids(ids)
        all_predictions = {}
        for (elem, pred), new_pred in zip(predictions.iteritems(),
                                          new_predictions.values()):
            all_predictions[elem] = np.hstack((pred, new_pred))
        print 'Saving results to', pred_file
        np.savez(pred_file, **all_predictions)

    def train(self):
        pass

    def load_model(self):
        pass


def main():
    model_types = dict(standard=MSLModel, multitask=MSLMultiModel,
                       mixed=MixedModel, dust=DustClassifier, moc=MOCModel)
    ap = ArgumentParser()
    ap.add_argument('-o', '--output-dir', required=True,
                    help='Output directory of models and predictions.')
    ap.add_argument('--ccs-dir', required=True,
                    help='Directory of the MSL CCS HDF5\'s.')
    ap.add_argument('--lanl-file', default='',
                    help='Filepath for the (new) LANL LIBS HDF5.')
    ap.add_argument('--libs-mix-file', default='',
                    help='Filepath for the LANL/MHC mix LIBS HDF5.')
    ap.add_argument('--moc-dir', default='',
                    help='Directory of the MOC data.')
    ap.add_argument('--model', choices=model_types, default='standard')
    ap.add_argument('--retrain', action='store_true',
                    help='Re-train the specified model (implies --repredict)')
    ap.add_argument('--repredict', action='store_true',
                    help='Re-predict Mars data using the existing model')
    args = ap.parse_args()

    model = model_types[args.model](output_dir=args.output_dir,
                                    ccs_dir=args.ccs_dir,
                                    lanl_file=args.lanl_file,
                                    libs_mix_file=args.libs_mix_file,
                                    moc_dir=args.moc_dir,
                                    )
    if args.retrain:
        model.train()
        model.predict_all_mars()
        return

    model.load_model()
    if args.repredict:
        model.predict_all_mars()
    else:
        model.predict_new_mars()

if __name__ == "__main__":
    main()
    
