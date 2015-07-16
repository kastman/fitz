Tutorial for a standard fMRI SPM Pipeline
==========================================

The following instructions will help you access images and logfiles from our
tutorial data, and configure and run our basic fMRI processing and modelling.

1. Choose directories and paths in **project.py** with ``fitz setup``.

2. Specify experiment processing parameters in **{experiment_name}.py**.

3. Download the requested workflow(s) with ``fitz install``

4. Specify which subjects to run with **subjects.txt**

5. Download and prepare images. (``fitz run -w xnatrecon`` or (Harvard CBS) with
   ``ArcGet.py`` and ``dcmstack``)

6. Add preproc and common model options to **{experiment_name}.py**

7. Copy logfiles and create design file

8. Create model file **{experiment_name}-{model_name}.csv**

9. Run workflows:  ``fitz run -w preproc onset model``

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

To begin, create a directory for your project/study, and a config directory
inside it called "fitz"; this will hold configuration and any scripts you want
to write. You can create both of these at once by typing
``mkdir -p <study>/fitz``. Finally, cd into it run ``fitz setup`` to answer
some questions about where you want your studie's processing directories to
live. Open a Terminal and type:

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
project.py, <study>.py, etc... This will let you run ``fitz`` from any directory
and it will be able to find all the setup without you telling it::

    export FITZ_DIR=<path/to/study/fitz>

.. note:: From here on out, the tutorial assumes you are running commands from
          the FITZ_DIR.


Setup Experiment File **{experiment_name}.py**
------------------------------------------------

Experiments are configured by creating a file called ``{experiment_name}.py``.
This is just a regular python file that defines options and variables used
by the workflows.

In this tutorial we will be processing a simple Delay Discounting experiment,
so our Experiment Name will be DD. Use a text editor to create and edit the
file **DD.py**.

.. code-block:: bash

    # On linux, this might look like:
    gedit DD.py  # linux

    # Or on a mac
    open -a TextEdit DD.py  # Mac

The first thing to do is to specify which pipeline (group of workflows) we want
to use for this experiment. For this tutorial we're going to use a standard
SPM Pipeline found `here
<https://github.com/kastman/fitz_nwlabs_spm_pipeline>`_), which consists of four
workflows: xnatconvert, preproc, onset, and model. We'll get to each of those
workflows below, but first add the name, source URL and version for the pipeline
into the experiment file:

.. code-block:: python

    # Workflow Parameters
    # --------------------
    workflow_src = "https://github.com/kastman/fitz_nwlabs_spm_pipeline.git"
    workflow_version = "0.0.1.dev"


Install Workflows
------------------

You should now download the pipeline requested by the experiment file. This
goes out to the internet (a repository on github in this case) and grabs the
exact version of the workflow specified in {experiment}.py and copies it into
the fitz directory. You only have to do this once at the start of your
experiment (or any time that the pipeline changes, which should ideally be
never).

.. code-block:: bash

    fitz install

In theory you could wait until just before running your experiment to download
the pipeline, but downloading it now allows you to see the default options and
parameters that will be used for all of your workflows (how? ref) so it's best
to do it now.

Setup **subjects.txt**
-----------------------

A subjects.txt file in the fitz directory is used to list all the subjects
that should be included. For this tutorial we'll only process a single subject,
so create a text file with one line::

    M87100094

By default ``fitz run`` will perform the processing on all subjects in the
subjects.txt file, but there are several subject-related options. You can use
``--subjects M87100094`` to specify which subjects to run (in case you need to
re-run just a few after making fixes, and you can also create other group files
called **subjects-{group_name}.txt** that can be run with the ``fitz run
--group group_name`` option.  You can see all the options for ``fitz run``
:ref:`here <commandline>`.

.. note:: When downloading from CBS Central, the subject id must be
          *exactly* the same as the "MR Session" id for the download to work
          correctly. I hope to fix this soon, but for the time being use the MR
          Session as your subject identifier.


Prepare images in the *data* directory
--------------------------------------------

For this tutorial, you will download dicom data from the CBS Central `xnat`_
server.  We're going to use one real subject from the RSA study as an
example.

Downloading from XNAT and converting images into nifti files in a single step
is the first workflow in the NWLabs SPM Pipeline, but you don't need to use
it - as long as you get nifti images into the data directory, you can use the
other pipelines (preproc, onset, model) without an xnat server.

Image download and conversion to nifti is a special type of workflow - the
output files are put into *data*/{subject_id}/images directory instead of
*analysis*, because the converted niftis are really more like inputs that
processing steps.

To configure the xnatconvert workflow to know which server to connect to,
add the following lines to the experiment file DD.py::

    # Xnat Download and Convert
    # --------------------------
    xnat_project = 'Buckholtz_RSA'
    download_patterns = ['mprage%RMS', 'ddt%']
    server = 'https://cbscentral.rc.fas.harvard.edu'

If you're working on your own study, you'll need to change and specify these
so that the patterns match up. The xnat_project is found on the main project
page next to "ID:".

.. image:: _static/images/XnatProject.png

The list of patterns search the "Series Description" of each image to
find datasets to download; any scan series that match any of the patterns in
the list will be downloaded. In the example above, the first pattern matches the
scan with a description of "mprage_3e_15 RMS" (this is the root mean square
anatomical T1) and the second pattern matches BOLD runs with "ddt" (the Delay
Discounting Task) in their description.

.. image:: _static/images/XnatPatterns.png

This is a database-style search so you use '%' for a wildcard instead of '*'.

You can now run the fitz workflow to download data::

    fitz run -w xnatconvert


.. note:: If you get a "No Images were downloaded" error you probably set up
   either the project's ID or the patterns incorrectly.

.. note:: If you get an authentication error, you need to setup your login info.
   See `xnat_auth info`_ for instructions.

Aside: CBSCentral NRG Tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you just want to quickly grab data and are using the Harvard
`Neuroinformatics Research Group`_ (NRG) xnat instances *CBSCentral* or
*GSPCentral*, you can use ArcGet.py to download it and dicomstack to convert it
to nifti format. This does the same thing as the fitz xnatconvert workflow, but
is (for better or worse) a little more flexible.

.. code-block:: bash

    # Change to the data directory
    cd ../data

    # Use ArcGet.py to download T1 & BOLD dicoms from CBS Central
    ArcGet.py -a cbscentral -s M87100094 -r MPRAGE,BOLD

    # Create a folder for the .nii images
    mkdir ../data/M87100094/images

    # Use dcmstack to convert images from DICOM to Nifti format
    dcmstack --embed-meta --dest-dir ../data/M87100094/images --output-ext .nii ../data/M87100094/RAW

    # don't forget to change back to the fitz directory when you're done
    cd ../fitz

.. note:: ArcGet.py is currently setup & available only on ncfnx / ncf
          workstations, not the Buckerville MacPro or laptops.

Setup Workflow Preprocessing Options
-------------------------------------

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

The func_template and struct_template must be set, even if options
for func_pattern and struct_pattern were set already for xnat_convert. This is
because the xnat_convert is not the only way to convert nifti files, and the
preproc workflow doesn't "know" about the xnat_convert workflow. It's important
to be able to set them separately, but I might add an option to compbine them
in a future release.

These "template" options are used to grab nifti images from the data
directory depending on how the file names were created - usually using the
series description from the dicom header. Check out your data directory to
look at the images and make sure you're grabbing the right ones.

TR is the Repetition Time, which should be specified in seconds (it is often
shown in scan parameter sheets in ms). The number of slices can be found on
the parameter sheet or by looking at the functional images with tools to view
the nifti header (``fslhd``, ``3dinfo``, or ``SPM --> Display Image``).

One additional caveat is that slice timing can be confusing - the scan parameter
sheets from our Siemans scanner always list a *Multi-slice mode* of
"Interleaved", even when slices are acquired sequentially. The correct value to
look at is the *Series* value directly below it, which will either be
"interleaved", "ascending" or "descending". Finally to completely convince
yourself, you can look at the Siemans DICOM header field
*CsaImage.MosaicRefAcqTimes* to see slice acquisition times.  Lots more helpful
info is at `Harvard CBS FAQ slice info`_.

Finally, set some default options for modeling. In this case we will use SPM
defaults for the hemodynamic response functions ('hrf') in our general linear
model, and will specify the unit for our design files will be in seconds (as
opposed to TRs).


Copy logfiles and create the Design File
-----------------------------------------

Copy Logfiles from study into your tutorial folder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For this tutorial, we will grab the original behavioral logfiles from their
current location on the cluster. Unfortunately logfiles are not downloaded from
CBSCentral automatically, and are copied around separately from the images.
In your own study you will be responsible for copying logfiles to the server
into your own StudyName/Subject_Data/Behavioral directory.

.. code-block:: bash

  # Make folders for the logfiles and design files
  mkdir ../data/M87100094/logfiles ../data/M87100094/design

  # Copy the logfiles for the tutorial subject to the data directory
  cp /ncf/jwb/studies/PrisonReward/Active/Subject_Data/RSA_DD_Active/1819_2012_Aug_22_????.* ../data/M87100094/logfiles/


There are two easy ways to specify the timing of fMRI information. One is to
create a separate csv for each model you want to run with columns named 'run',
'onset', and 'condition'. The other is to create one large design file
containing several columns, and specify in your model which column should be
used for which model. This essentially allows you to specify multiple
combinations or onset, duration, and modulation from the same file, and know
for sure that the model is specified correctly.

By default the design files live in a directory called "design" inside each
subject's data folder, i.e.
``<data_dir>/<subject_id>/design/<design_name>.csv``.
Each row in this file corresponds to an event, where the term “event” is used
broadly and can mean a “block” in a block design experiment.

For either method, the design file should contain a "run" column, and there
should be only one design file for the whole task (i.e. not "Model1_run1",
"Model1_run2"). Each row of your logfile should be a trial, and there
should be columns for each trial that list the trial type (condition), trial
time (onset). Additionally, there can be columns for trial duration (this
defaults to zero), and additional values to use for parametric modulators
(e.g. which option a participant chose, the value of their choice).

Depending on the method, design files may contain several different columns
for onset and duration that are specified as variables in the model file below
(Method 1), or they may have columns explicitly labelled "condition", "onset",
"duration" (Method 2).

Regardless of the method you choose, make sure that your logfiles sort
correctly when you list them with ``ls``, because the run column will be added
based on the filenames' alphabetical order.


Method 1: Single Large Design File for all Models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you plan to use the single large design file method of specifying onsets,
you can simply concatenate each of your existing csvs together. For example,
the following command will combine all the logfiles into a single csv that can
be used as a design file.

.. code-block:: bash

  cat ../data/M87100094/logfiles/*.csv > ../data/M87100094/design/DD.csv

When using Method 1, the model file below must contain variables for "onset-col"
and "condition-col", and may also optionally specify "duration-col" and
"pmod-cols" columns. If "duration-col" is set to an integer instead of a string
(i.e. 0 or 4) that value will be used for all events.

For the model below in this tutorial, we'll use method 1.


Method 2: ``log2design`` for separate, model-specific design files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some people prefer to have separate design files for each model - this is the
Lyman way and allows for exact model compatibility, and also lets you see
exactly what the onsets will look like.

For simple designs where most of what you want already exists in your logfiles,
fitz includes a simple script called ``log2design.py`` that will select
and split up your full logfile into a "long" style csv with appropriate
columns.

*If your logfiles don't have appropriate columns already, you won't be able to
use the script helper and will have to make your own design files, or create new
logfiles that include these columns.*

An extremely simple design file in the style of separate design files would
look like::

    run, condition, onset
    1, sooner, 0
    1, sooner, 12
    2, sooner, 0
    2, later, 12

For this DD task, we will map the following columns from the logfiles and
create a model file in *data*/{subject_id}/design/**DD-1.1.Choice.py**:

.. cssclass:: table-striped

  +---------------------+--------------------+
  | logfile column name | design column name |
  +=====================+====================+
  | choice              | condition          |
  +---------------------+--------------------+
  | cuesTime            | onset              |
  +---------------------+--------------------+
  | trialResp.rt        | duration           |
  +---------------------+--------------------+
  | choiceInt           | pmod-ChoiceInt     |
  +---------------------+--------------------+

.. code-block:: bash

  # Create the design files using the textOnsets2long script (or do it yourself)
  textOnsets2long.py ../data/M87100094/logfiles/*.csv --out ../data/M87100094/design/DD-Model1.csv --condition-col choice --onset-col cuesTime --duration-col trialResp.rt --pmods-col choiceInt

Models may be as complicated (or simple) as you want, and you should feel free
to create the csv yourself without the help of ``log2design.py``.

Waskom's `Lyman Documentation`_ also has more info on the design file and
additional regressors file where post-convolved regressors for each TR may also
be added to the model.

.. note:: Note that the 'pmod-' columns correspond *roughly* to 'value' columns
          in a standard lyman design file, but are not the same thing. See
          `Mumford, Poline and Poldrack 2015`_ for a discussion on how
          parametric regressors and orthogonalization are handled between
          different fMRI packages. (TL;DR, Fitz enters these columns as pmods in
          SPM, while Lyman enters values as amplitudes.)


Model Options (Design File and Contrasts)
------------------------------------------

Information about specific models are listed in their own python files
**<experiment_name>-<model_name>.py**. If you want a specific order of models
(for example you're creating models at different onset times) you should
list your model numbers explicitly.

Paste the following lines into a new file called DD-1.1.Choice.py to specify
two contrasts - one for the main effect of all trials and one for the
parametric modulator. The column names (e.g. 'sooner', 'later') must be values
in the

.. code-block:: python

    design_file = 'DD.csv'

    conditions = ['sooner', 'later']
    condition_col = 'choice'
    onset_col = 'cuesTime'
    duration_col = 'trialResp.rt'
    pmod_cols = ['choiceInt']

    contrasts = [
      ('all trials', ['sooner', 'later'], [1, 1]),                # 1
      ('choice',     ['soonerxchoice^1', 'laterxchoice^1'], [1])  # 2
    ]


Run Workflows
--------------

Preproc
  Performs slicetime correction, realignment, coregistration, normalization
  and smoothing.

Onsets
  Converts the design file to binary Matlab .mat SPM-style multiple conditions
  files.

Model
  Calculates artifacts, specifies a model design and estimates the model
  and contrasts.

.. code-block:: bash

    fitz run -w preproc onsets model --model 1.1.Choice

.. note:: N.B. There is no default model, so you must specify which one you
   want to use with the ``--model`` flag.


Bonus: Alternative Models
--------------------------

Exercise: Create a new design file with a different onset, and create a new
model file called DD-Model2.py that uses it.


.. _Lyman Documentation : http://stanford.edu/~mwaskom/software/lyman/experiments.html#the-design-file
.. _xnat : http://www.xnat.org
.. _Harvard CBS FAQ slice info : http://cbs.fas.harvard.edu/science/core-facilities/neuroimaging/information-investigators/scannerfaq#slice_order
.. _Mumford, Poline and Poldrack 2015 : http://journals.plos.org/plosone/article?id=10.1371/journal.pone.0126255
.. _Neuroinformatics Research Group : http://neuroinfo.org
.. _xnat_auth info : http://people.fas.harvard.edu/~kastman/nwlabs_pipeline/xnat_auth.html
