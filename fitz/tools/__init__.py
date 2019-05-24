# from .commandline import run_parser
# from .graphutils import *
# from . import setup_project
import os
from os.path import dirname, basename, isfile
import glob

modules = glob.glob(os.path.join(dirname(__file__), '*.py'))
__all__ = [
    basename(f)[:-3] for f in modules
    if isfile(f) and not f.endswith('__init__.py')
]
from . import *  # noqa
