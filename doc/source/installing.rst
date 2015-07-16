.. _installing:

Installing fitz
================


To install fitz, you can run

    pip install fitz

This will install the stable version. To get the development version, you
should run

   pip install git+git://github.com/kastman/fitz.git#egg=fitz

Installing through pip should install all required depencies, but shout if
any were missed.

Dependencies
------------

Fitz requires Python 2.7, and does not run on Python 3. We strongly recommend
using the `Anaconda <https://store.continuum.io/cshop/anaconda/>`_
distribution, which ships with the majority of the Python packages needed to
run fitz. The rest can be easily installed with pip.


Non-Python Software
~~~~~~~~~~~~~~~~~~~

Fitz is a high-level process manager and doesn't do any of the hard work itself!

However, that means that you will have to install separate neuroimaging packages
yourself. The pipelines you choose to use will likely require you to install
packages yourself, like FSL, AFNI, or SPM.

For the time being, listing supported non-python software is done in the
documentation pages of each individual pipeline, but we may add a more formal
way of listing which tools are required in a future release.


Python Packages
~~~~~~~~~~~~~~~

- Python 2.7

- IPython 2.0

- numpy 1.7

- scipy 0.12

- matplotlib 1.3

- nipype > 0.8

- nibabel 1.3

- pandas 0.12
