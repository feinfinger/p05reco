"""
Development python package for P05 CT data handling.
"""

from .main import recoObject
import p05reco.lib
import os
import p05reco


__version__ = '0.4'
__date__ = '$Date: 2017 / 12 / 12'
__author__ = 'fwilde'
__all__ = ['lib']
__configfile__ = (os.path.dirname(p05reco.__file__) + os.sep
                  + 'lib' + os.sep + 'reco_configspec.ini')
