#! /usr/bin/env python
import os
from setuptools import setup, find_packages

descr = """Fitz: Workflow Mangement for neuroimaging data."""

DISTNAME = 'fitz'
DESCRIPTION = descr
AUTHOR = MAINTAINER = 'Erik Kastman'
AUTHOR_EMAIL = MAINTAINER_EMAIL = 'erik.kastman@gmail.com'
LICENSE = 'BSD (3-clause)'
URL = 'http://github.com/kastman/fitz'
DOWNLOAD_URL = ''

with open(os.path.join(os.path.dirname(
        __file__), 'fitz', 'VERSION')) as version_file:
    VERSION = version_file.read().strip()


INSTALL_REQUIRES_IMPORT = ["IPython", "numpy", "scipy", "matplotlib",
                           "pandas", "nibabel", "nipype", "pyxnat", "httplib2"]
INSTALL_REQUIRES = [s.lower() for s in INSTALL_REQUIRES_IMPORT]
INSTALL_REQUIRES = ['matplotlib', 'nipype', 'nibabel', 'pandas', 'pyxnat', 'scipy', 'httplib2']


def check_dependencies():

    # Just make sure dependencies exist, I haven't rigorously
    # tested what the minimal versions that will work are
    needed_deps = INSTALL_REQUIRES_IMPORT
    missing_deps = []
    for dep in needed_deps:
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(dep)

    if missing_deps:
        missing = (", ".join(missing_deps)
                   .replace("sklearn", "scikit-learn")
                   .replace("skimage", "scikit-image"))
        raise ImportError("Missing dependencies: %s" % missing)


if __name__ == "__main__":

    if os.path.exists('MANIFEST'):
        os.remove('MANIFEST')

    import sys
    if not (
            len(sys.argv) >= 2 and ('--help' in sys.argv[1:] or
                                    sys.argv[1] in ('--help-commands', '--version', 'egg_info', 'clean'))):
        check_dependencies()

    setup(name=DISTNAME,
          author=AUTHOR,
          author_email=AUTHOR_EMAIL,
          maintainer=MAINTAINER,
          maintainer_email=MAINTAINER_EMAIL,
          description=DESCRIPTION,
          license=LICENSE,
          version=VERSION,
          url=URL,
          download_url=DOWNLOAD_URL,
          install_requires=INSTALL_REQUIRES,
          packages=find_packages(exclude=['doc']),  # ['fitz', 'fitz.tools'],
          scripts=['scripts/fitz', 'scripts/log2design.py'],
          classifiers=[
              'Development Status :: 2 - Pre-Alpha',
              'Intended Audience :: Science/Research',
              'Programming Language :: Python :: 2.7',
              'License :: OSI Approved :: BSD License',
              'Operating System :: POSIX',
              'Operating System :: Unix',
              'Operating System :: MacOS'],
          keywords=['neuroimaging', 'workflows']
          )
