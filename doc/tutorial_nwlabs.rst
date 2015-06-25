Tutorial
=========

The following instructions will help you get tutorial data, setup and run
one subject from our tutorial experiment.

1. ``fitz setup`` directories and paths.

2. Download and prepare prepare images with ``ArcGet.py`` and ``dcmstack``.

3. Copy logfiles and create design file.

4. Setup ``experiment.py`` with experiment processing parameters.

5. Tell fitz which subs to run with ``subjects.txt``

6. Have fitz download the requested workflow with ``fitz install``

7. Do all the things.  ``fitz run -w workflows``


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



Prepare images data in the *data* directory
--------------------------------------------

For this tutorial, you will download dicom data from the CBS Central xnat
server.

We're going to use one real subject from the PrisonReward study as an example.

.. code-block:: bash

    cd ../data

    # Use ArcGet.py to download T1 & BOLD dicoms from CBS Central
    ArcGet.py -a cbscentral -s M87100094 -r MPRAGE,BOLD

    # Change to the subject directory and create a folder for the .nii images
    cd M87100094
    mkdir images

    # Use dcmstack to convert images from DICOM to Nifti format
    dcmstack --embed-meta --dest-dir images --output-ext .nii RAW/


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
    workflow = "nwlabs_spm"
    workflow_src = "git@ncfgit.rc.fas.harvard.edu:kastman/nwlabs_fitz.git"
    workflow_version = "0.0.1.dev"

    # Preproc Parameters
    # -------------------
    func_template = "{subject_id}/images/*dd*"
    anat_template = "{subject_id}/images/*mprage*"

    n_runs = 3
    TR = 2.5
    temporal_interp = True
    interleaved = False
    slice_order = 'up'
    num_slices = 33
    smooth_fwhm = 6
    hpcutoff = 120

    bases = {'hrf': {'derivs': [0, 0]}}
    estimation_method = 'Classical'

    # Default Model Parameters
    # -------------------------
    design_name = 'DD-Model1'
    input_units = output_units = 'secs'
    contrasts = [
      ('all trials', ['sooner', 'later'], [1, 1]),                # 1
      ('choice',     ['soonerxchoice^1', 'laterxchoice^1'], [1])  # 2
    ]


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

    fitz install

Run Workflows
--------------

.. code-block:: bash

    fitz run -w onsets preproc model


Bonus: Alternative Models
--------------------------

.. code-block:: bash

    cp DD.py DD-Model2.py


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
