#!/bin/sh

pip install --upgrade pip


# The superman package from PyPI is missing a file; this is the easiest way to install.
cd ~
git clone git@github.com:all-umass/superman.git
cd superman
pip install -e .
