Fitz: Modern Nipype Workflow Management
========================================

Fitz provides an interface to efficiently manage and execute custom nipype
workflows for the analysis of neuroimaging experiments. It expands on the
`Lyman`_ "ecosystem" to allow workflows to be easily plugged into the lyman
configuration / execution study processing experience.

Using fitz consists of two steps:

Step 1
-------

Create a few plain-text (.py and .csv)
:doc:`configuration files <config_file_glossary>` that specify:

* Where data lives and analysis files should go
* Processing options (e.g. the size of the smoothing kernel, whether or not
  to perform optional steps...)
* Source url and version of the pipeline to use
* Other config files for the pipeline (fMRI Onset Times, Diffusion Directions)
  and how to load them for each subject.

Step 2
-------

Automatically download the pipeline by running ``fitz setup``, and
run subjects with ``fitz run``.


Documentation Contents
----------------------

For an example of running fitz with an existing pipeline, check out the
:doc:`tutorial for a standard fMRI SPM pipe <tutorial_nwlabs>`.

For info on creating your own pipelines to use with fitz, check out the
[incomplete] guide on :doc:`creating_fitz_pipelines`.

.. toctree::
   :maxdepth: 2

   tutorial_nwlabs
   creating_fitz_pipelines
   config_file_glossary

.. _Lyman : http://stanford.edu/~mwaskom/software/lyman
