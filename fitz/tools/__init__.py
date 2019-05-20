# from .commandline import run_parser
# from .graphutils import *
# from . import setup_project
from pkg_resources import DistributionNotFound, get_distribution
import os
from os.path import dirname, basename, isfile
import glob


try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    with open(os.path.join(os.path.dirname(__file__), 'VERSION')) as version_file:
        version = version_file.read().strip()
    __version__ = version
    del version
finally:
    del get_distribution, DistributionNotFound


modules = glob.glob(os.path.join(dirname(__file__), '*.py'))
__all__ = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
from . import *  # noqa
