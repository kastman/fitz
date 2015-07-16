.. _config_file_glossary:

Glossary of Configuration Files
================================

All required configuration files are plaintext python or csv, and store various
information.

Project - fitz_dir/project.py
  * Data locations (e.g. *data_dir*, *analysis_dir*) and some global
    options.

Experiment - fitz_dir/{experiment_name}.py
  * Pipeline source url & version
  * Processing options for each workflow.
