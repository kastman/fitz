Tutorial
=========

1. ``fitz setup`` directories and paths.

2. Copy source behavioral logs ``cp logfiles`` & download data with ``ArcGet.py``.

3. Create design file.

4. Setup ``experiment.py`` with experiment processing parameters.

5. Tell fitz which subs to run with ``subjects.txt``

5. ``fitz run -w workflows``

The following instructions will help you get tutorial data, setup and run
one subject from our tutorial experiment.

Setup Directories and **project.py**
-------------------------------------

Fitz includes a script to create the FITZ_DIR/project.py file to specify
directories and some project options.

First, create a directory for your project.

.. code-block:: bash

    cd /ncf/jwb/studies/PrisonReward/Active/Analyses
    mkdir spmFMRI
    mkdir spmFMRI/fitz
    cd spmFMRI/fitz
    fitz setup
    *answer questions or accept defaults*


Copy source data to the *data* directory
-----------------------------------------

For this tutorial, you will download dicom data from the CBSCentral server.

.. code-block:: bash

    cd ../data

    # Use ArcGet.py to download T1 & BOLD dicoms
    ArcGet.py -s M87100094 -s MEMPRAGE,task

    # Also copy logfiles
    cp /ncf/jwb/studies/PrisonReward/Subject_Data/


Create Design File
-------------------

onset_creator.py -s


Setup Experiment File **DD.py**
--------------------------------

Change directories back to the *FITZ_DIR*.

.. code-block:: bash

    cd ../fitz

Edit DD.py to include the following options:

.. code-block:: python

    workflow = ""
    source_template = "{subject_id}/"
    anat_template = "{subject_id}/"

Setup subjects.txt
-------------------

A subjects.txt file in the fitz directory is used to list all the subjects
that should be included. Since we're only processing a single subject you can
skip this step and use the "-r sub001" option, or create a text file with
one line by typing ``echo sub001 > subjects.txt``.


Install Workflows
------------------

Install the workflows requested by the experiment file.

.. code-block:: bash

    fitz install

Run Workflows
--------------

.. code-block:: bash

    fitz run -w convert onsets preproc model -s sub001


Bonus: Alternative Models
--------------------------

.. code-block:: bash

    cp DD.py DD-Model2.py
