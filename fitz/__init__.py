from frontend import *
import tools
import os.path as op

with open(op.join(op.dirname(__file__), 'VERSION')) as version_file:
    version = version_file.read().strip()
__version__ = version
