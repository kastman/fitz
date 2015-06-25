Tutorial
=========

1. ``fitz setup``

2. Copy data into data directory.

3. Setup your design file.

4. ``fitz run -w workflows``


Setup
------

Fitz includes a script to create the FITZ_DIR/project.py file to specify
directories and some project options.

First, create a directory for your project. For NW Labs this should be in
/ncf/jwb/studies/<StudyName>/Analyses).

.. code-block:: bash

    mkdir project
    mkdir project/fitz
    cd project/fitz
    fitz setup
    *answer questions or accept defaults*
