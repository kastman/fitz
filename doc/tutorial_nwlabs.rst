.. _tutorial_nwlabs:

Tutorial
=========

The following instructions will help you access images and logfiles from our
tutorial data, and configure and run our basic fMRI processing and modelling.

1. Choose directories and paths in **project.py** with ``fitz setup``.

2. Specify experiment processing parameters in **{experiment_name}.py**.

3. Download the requested workflow(s) with ``fitz install``

4. Specify which subjects to run with **subjects.txt**

5. Download and prepare images. (``fitz run -w xnatrecon`` or with ``ArcGet.py`` and ``dcmstack``)

6. Add preproc and common model options to **{experiment_name}.py**

7. Copy logfiles and create design file **{experiment_name}-{model_name}.csv**.

8. Run workflows:  ``fitz run -w preproc onset model``

.. note:: In this tutorial, files to create are **bold**, important directories
          are *italicized*, and commands to run are ``in monospace`` or large
          code blocks.

Setup Directories and **project.py**
-------------------------------------

There are 3 important directories in a standard project:

fitz dir
  Configuration files and some scripts.

data dir
  Raw data and logfiles.

analysis dir
  Outputs of the workflows and processed data.

To begin, create a directory for your project and a config directory inside it
called "fitz" to hold configuration and any scripts you want to write. Then cd
into it run ``fitz setup``. Open a Terminal and type:

.. code-block:: bash

    cd /ncf/jwb/studies/PrisonReward/Active/Analyses
    mkdir -p spmFMRI/fitz
    cd spmFMRI/fitz
    fitz setup

The script will ask questions to help you get started. You can just type enter
after each one to accept the defaults::

    Let's set up your project.

    Please enter values for the following settings (just press Enter to
    accept a default value, if one is given in brackets).

    Please use relative paths.

    > Project name: PrisonReward
    > Default experiment: DD
    > Data tree path [../data]:
    > Analysis tree path [../analysis]:
    > Working tree path [../analysis/workingdir]:
    > Crashdump path [../analysis/niypype-kastman-crashes]:
    > Remove working directory after execution? (Y/n) [y]:

Finally, set an environment variable to tell fitz where to look for
configurations::

    export FITZ_DIR=`pwd`

.. note:: From here on out, the tutorial assumes you are running commands from
          the FITZ_DIR.


Setup Experiment File **DD.py**
--------------------------------

Experiments are configured by creating a file called ``{experiment_name}.py``.
This is just a regular python file that defines options and variables used
by the workflows.

Use a text editor to edit the file `DD.py`. On linux, this might look like:

.. code-block:: bash

    cd ../../fitz
    gedit DD.py

Paste the following setting options into DD.py to tell fitz the name, version
and path to the workflow you want this experiment to use:

.. code-block:: python

    # Workflow Parameters
    # --------------------
    workflow_src = "git@ncfgit.rc.fas.harvard.edu:kastman/nwlabs_fitz.git"
    workflow_version = "0.0.1-dev"


Install Workflows
------------------

Install the workflows requested by the experiment file. This downloads the
exact version of the workflow as specified in {experiment}.py and copies it into
the fitz directory. You only have to do this once at the start (or any time that
the workflow changes, which should ideally be never).

.. code-block:: bash

    fitz install

**TODO** make fitz clone to the FITZ_DIR (instead of pwd) and make it read pipelines
there (instead of the fitz install dir)


Setup **subjects.txt**
-----------------------

A subjects.txt file in the fitz directory is used to list all the subjects
that should be included. Since we're only processing a single subject you can
skip this step now and use the "-r sub001" option on the command line, or
create a text file with one line::

    echo M87100094 > subjects.txt

.. note:: If desired, other groups of subjects may also be specified by creating
          **subjects-{group_name}.txt** files that may be used in
          ``fitz run --group group_name``.


Prepare images in the *data* directory
--------------------------------------------

For this tutorial, you will download dicom data from the CBS Central `xnat`_
server.  We're going to use one real subject from the PrisonReward study as an
example.

Image download and conversion to nifti is a special type of workflow - the
output files are put into *data*/{subject_id}/images directory instead of
*analysis*, because the converted niftis are really more like inputs that
processing steps.

To configure the xnatconvert workflow to know which server to connect to,
add the following lines to the experiment file DD.py::

    # Xnat Download and Convert
    # --------------------------
    xnat_project = 'Buckholtz_RSA'
    struct_pattern = 'mprage%RMS'
    func_pattern = 'ddt%'
    server = 'https://cbscentral.rc.fas.harvard.edu'

**Don't forget this!** Run the fitz workflow to download data::

    fitz run -w xnatconvert

Aside: CBSCentral Tools
~~~~~~~~~~~~~~~~~~~~~~~~

If you just want to quickly grab data, and look at it, you can use ArcGet.py
to download it and dicomstack to convert it to nifti format. This does the
same thing as the fitz workflow, but is (for better or worse) a little more
flexible.

.. code-block:: bash

    # Use ArcGet.py to download T1 & BOLD dicoms from CBS Central
    ArcGet.py -a cbscentral -s M87100094 -r MPRAGE,BOLD

    # Create a folder for the .nii images
    mkdir ../data/M87100094/images

    # Use dcmstack to convert images from DICOM to Nifti format
    dcmstack --embed-meta --dest-dir ../data/M87100094/images --output-ext .nii ../data/M87100094/RAW


Setup Workflow Options / Parameters
------------------------------------

Next, configure the pattern for choosing functional and structural images,
and add any other preprocessing options.

Add these config variables to your DD.py experiment file:

.. code-block:: python

    # Preproc Parameters
    # -------------------

    func_template = "{subject_id}/images/*dd*"
    anat_template = "{subject_id}/images/*mprage*"

    ## TODO Add sanity check that ensures these are true

    ## TODO Add motion_correct = True
    ## TODO Print default options

    n_runs = 3
    TR = 2.5
    temporal_interp = True
    interleaved = False
    slice_order = 'up'
    num_slices = 33
    smooth_fwhm = 6
    hpcutoff = 120
    frames_to_toss = 0

    # Default Model Parameters
    # -------------------------

    bases = {'hrf': {'derivs': [0, 0]}}
    estimation_method = 'Classical'
    input_units = output_units = 'secs'

Models are defined in their own files, with the name of the experiment and the
name of the model.

Add the following options to a new file called DD-Model1.py:

.. code-block:: python

    design_file = 'DD-Model1.csv'
    contrasts = [
      ('all trials', ['sooner', 'later'], [1, 1]),                # 1
      ('choice',     ['soonerxchoice^1', 'laterxchoice^1'], [1])  # 2
    ]

Copy logfiles and create the Design File
-----------------------------------------

Create a plain-text "design file" in `csv` format for all runs containing
columns for onset times, durations, conditions and parametric modulators.

At a minium the design file should contain columns for "run", "condition", and
"onset"; it may also have columns for duration and "pmod-" columns that will be
entered as parametric modulators.

An extremely simple design file would look like::

    run, condition, onset
    1, sooner, 0
    1, sooner, 12
    2, sooner, 0
    2, later, 12

For simple designs where most of what you want already exists in your logfiles,
fitz includes a simple script called ``textOnsets2Long.py`` that will select
and split up your full logfile into a "long" style csv with appropriate columns.
This assumes that each row of your logfile is a trial, and that there are
columns that list the trial type (condition), trial time (onset), and trial
duration (this defaults to zero), and additional values to use for parametric
modulators (i.e. which option a particpant chose, the value of their choice).

To use it, specify which of the column names in your logfile hold map to the
appropriate columns (condition, onset, duration, pmod) and list the logfiles.

For this DD task, we will map the following columns from the logfiles and
create a model file in *data*/{subject_id}/design/**DD-Model1.py**:

.. cssclass:: table-striped

  +---------------------+--------------------+
  | logfile column name | design column name |
  +=====================+====================+
  | immediacy           | condition          |
  +---------------------+--------------------+
  | cuesTime            | onset              |
  +---------------------+--------------------+
  | trialResp.rt        | duration           |
  +---------------------+--------------------+
  | choiceInt           | pmod-ChoiceInt     |
  +---------------------+--------------------+

.. code-block:: bash

    # Make folders for the logfiles and design files
    mkdir ../data/M87100094/logfiles ../data/M87100094/design

    # Copy the logfiles for the tutorial subject to the data directory
    cp /ncf/jwb/studies/PrisonReward/Active/Subject_Data/RSA_DD_Active/1819_2012_Aug_22_????.* ../data/M87100094/logfiles/

    # Create the design files using the textOnsets2long script (or do it yourself)
    textOnsets2long.py ../data/M87100094/logfiles/*.csv --out ../data/M87100094/design/DD-Model1.csv --condition-col choice --onset-col cuesTime --duration-col trialResp.rt --pmods-col choiceInt

Models may be as complicated (or simple) as you want, and you should feel free
to create the csv yourself without the help of ``textOnsets2long.py``.

Waskom's `Lyman Documentation`_ also has more info on the design file and
additional regressors file where post-convolved regressors for each TR may also
be added to the model.


Run Workflows
--------------

Preproc
  Performs slicetime correction, realignment, coregistration, normalization
  and smoothing.

Onset
  Converts the design file to binary Matlab .mat SPM-style multiple conditions
  files.

Model
  Calculates artifacts, specifies a model design and estimates the model
  and contrasts.

.. code-block:: bash

    fitz run -w onsets preproc model --model Model1

.. note:: N.B. There is no default model, so you must specify which one you
   want to use with the ``--model`` flag.


Bonus: Alternative Models
--------------------------

Exercise: Create a new design file with a differnet onset, and create a new
model file called DD-Model2.py that uses it.

.. cssclass:: table-striped

  +---------------------+-----------+----------+--------------+----------------+
  | design column name  | condition |  onset   | duration     | pmod-ChoiceInt |
  +=====================+===========+==========+==============+================+
  | logfile column name | choice    | cuesTime | trialResp.rt | choiceInt      |
  +---------------------+-----------+----------+--------------+----------------+

.. _Lyman Documentation : http://stanford.edu/~mwaskom/software/lyman/experiments.html#the-design-file
.. _xnat : http://www.xnat.org
