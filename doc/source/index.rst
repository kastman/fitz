Fitz: Modern Nipype Workflow Management
========================================

Fitz provides an interface to efficiently manage and execute custom nipype
workflows for the analysis of neuroimaging experiments. It expands on the
`Lyman`_ "ecosystem" to allow workflows to be easily plugged into the lyman
configuration / execution study processing experience.

There is a general progression of steps that comprise an analysis.

Step 1 - Setup Configuration Files
-----------------------------------

At a very high level, configuration of the pipeline is stored in several
plain-text .py and .csv configuration files. More info on all the available
options can be found at defining project parameters, defining experiment
parameters, and the general :doc:`config_file_glossary`, but in general you
will need to specify:

* Where or how to find source data and where to save analysis files -
  **project.py**
* Processing options, e.g. the size of the smoothing kernel, whether or not
  to perform optional steps... - **{experiment_name}.py**
* Source url and version of the pipeline to use - also **{experiment_name}.py**
* Other config files for the pipeline (fMRI Onset Times, Diffusion Directions)
  and how to load them for each subject. -
  **data/{subject_id}/design/{model_name}.csv**, other miscellaneous files per
  pipeline


Step 2 - Prepare the data
--------------------------

Subject-specific files live in a **data** directory, and some setup is often
required. This consists of downloading data and creating appropriate files to
speicfy fMRI models, diffusion directions, etc. This step changes a lot
depending on the pipeline, and different pipelines will have information on
exactly what information they require. For an example, see the
:doc:`tutorial for a standard fMRI SPM pipe <tutorial_nwlabs>` or see the specific
:doc:`documentation for the standard fMRI SPM pipe`.


Step 3 - Process the data
--------------------------

Once fitz is configured and necessary data is in place, you can simply call
``fitz run`` to carry out processing. See ``fitz run -h`` or the
:doc:`command line help page <commandline>` for more information on options.


Documentation Contents
----------------------

For an example of running fitz with an existing pipeline, check out the
:doc:`tutorial for a standard fMRI SPM pipe <tutorial_nwlabs>`.

For info on creating your own pipelines to use with fitz, check out the
[incomplete] guide on :doc:`creating_fitz_pipelines`.

.. toctree::
   :maxdepth: 2

   installing
   releases
   tutorial_nwlabs
   creating_fitz_pipelines
   config_file_glossary
   commandline

.. _Lyman : http://stanford.edu/~mwaskom/software/lyman
