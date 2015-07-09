Tutorial
=========

The following instructions will help you get tutorial data, setup and run
one subject from our tutorial experiment.

1. ``fitz setup`` directories and paths.

2. Copy logfiles and create design file.

3. Setup ``experiment.py`` with experiment processing parameters.

4. Tell fitz which subs to run with ``subjects.txt``

5. Have fitz download the requested workflow with ``fitz install``

6. Download and prepare prepare images. (with ``ArcGet.py`` and ``dcmstack`` or ``fitz run -w xnatrecon``)

7. Run workflows:  ``fitz run -w preproc onset model``


Setup Directories and **project.py**
-------------------------------------

There are 3 important directories in a standard project:

1. **fitz** dir: Configuration files and some scripts.
2. **data** dir: Raw data and logfiles.
3. **analysis** dir: Outputs of the workflows and processed data.

The first setup file to create is the *FITZ_DIR*/project.py, which lists the
paths to each of these directories.

First, create a directory for your project and a fitz dir (config dir) inside
it, then run ```fitz setup`` from the new *FITZ_DIR* directory.

.. code-block:: bash

    cd /ncf/jwb/studies/PrisonReward/Active/Analyses
    mkdir -p spmFMRI/fitz
    cd spmFMRI/fitz
    fitz setup

Then answer questions or accept defaults::

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


For this DD task, we will map the following columns from the logfiles:

+---------------------+-----------+----------+--------------+----------------+
| design column name  | condition |  onset   | duration     | pmod-ChoiceInt |
+=====================+===========+==========+==============+================+
| logfile column name | choice    | cuesTime | trialResp.rt | choiceInt      |
+---------------------+-----------+----------+--------------+----------------+

.. code-block:: bash

    # Make folders for the logfiles and design files
    mkdir logfiles design

    # Copy the logfiles for the tutorial subject to the data directory
    cp /ncf/jwb/studies/PrisonReward/Active/Subject_Data/RSA_DD_Active/1819_2012_Aug_22_????.* logfiles/

    # Create the design files using the textOnsets2long script (or do it yourself)
    textOnsets2long.py logfiles/*.csv --out design/DD-Model1.csv --condition-col choice --onset-col cuesTime --duration-col trialResp.rt --pmods-col choiceInt

Waskom's `Lyman Documentation`_ also has more info on the design file.


Setup Experiment File **DD.py**
--------------------------------

Experiments are configured by creating a file called ``<experiment_name>.py``.
This is just a regular python file that defines options and variables used
by the workflows.

Change directories back to the *FITZ_DIR*, and use a text editor to edit the
file `DD.py`.

.. code-block:: bash

    cd ../../fitz
    gedit DD.py

Paste the following settings in to DD.py:

.. code-block:: python

    # Workflow Parameters
    # --------------------
    workflow_src = "git@ncfgit.rc.fas.harvard.edu:kastman/nwlabs_fitz.git"
    workflow_version = "0.0.1.dev"


Setup subjects.txt
-------------------

A subjects.txt file in the fitz directory is used to list all the subjects
that should be included. Since we're only processing a single subject you can
skip this step and use the "-r sub001" option, or create a text file with
one line::

    echo M87100094 > subjects.txt


Install Workflows
------------------

Install the workflows requested by the experiment file. This downloads the
exact version of the workflow as specified and copies it into the scripts
directory. You only have to do this once at the start (or any time that the
workflow changes, which should ideally be never).

.. code-block:: bash

    ## TODO make sure fitz clones to the FITZ_DIR
    ##      and make sure that it reads pipelines there

    fitz install


Prepare images data in the *data* directory
--------------------------------------------

For this tutorial, you will download dicom data from the CBS Central xnat
server.  We're going to use one real subject from the PrisonReward study as an example.

There are two options:

1. Use the xnatconvert workflow to download them through fitz.

-- or --

2. Use the CBSCentral tools to download the images directly.

Option 1. Downloading images with Fitz xnatconvert workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Downloading the images is a relatively special case and belongs in the
category of setting up raw data, so the special xnatconvert workflow puts
its output in the data directory instead of the analysis directory.

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

Option 2. Downloading images with ArcGet.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you just want to quickly grab data, and look at it, you can use ArcGet.py
to download it and dicomstack to convert it to nifti format. This does the
same thing as the fitz workflow, but is (for better or worse) a little more
flexible.

.. code-block:: bash

    cd ../data

    # Use ArcGet.py to download T1 & BOLD dicoms from CBS Central
    ArcGet.py -a cbscentral -s M87100094 -r MPRAGE,BOLD

    # Change to the subject directory and create a folder for the .nii images
    cd M87100094
    mkdir images

    # Use dcmstack to convert images from DICOM to Nifti format
    dcmstack --embed-meta --dest-dir images --output-ext .nii RAW/


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

    ## TODO Move models to their own files and
    ##      inspect directory for them; no default file.
    ## How to have extra config files for different workflows?
    ## Just code that into the workflow of what to look for?

Models are defined in their own files, with the name of the experiment and the
name of the model.

Add the following options to a new file called DD-Model1.py:

.. code-block:: python

    design_file = 'Model1.csv'
    contrasts = [
      ('all trials', ['sooner', 'later'], [1, 1]),                # 1
      ('choice',     ['soonerxchoice^1', 'laterxchoice^1'], [1])  # 2
    ]


Run Workflows
--------------

* Prepoc workflow: performs slicetime correction, realignment,
  coregistration, normalization and smoothing.

* Onset workflow: Converts the design file to SPM *.mat multiple conditions
  files.

* Model: Calculates artifacts, specifies a model design and estimates the
  model and contrasts.

.. code-block:: bash

    fitz run -w onsets preproc model --model Model1

N.B. There is no default model, so you must specify which one you want to use
with the ``--model`` flag.


Bonus: Alternative Models
--------------------------

Exercise: Create a new design file with a differnet onset, and create a new
model file called DD-Model2.py that uses it.


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

.. _Lyman Documentation : http://stanford.edu/~mwaskom/software/lyman/experiments.html#the-design-file
