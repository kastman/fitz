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
  * Default model parameters

Model - fitz_dir/{experiment_name}-{model_name}.py
  * Model Name
  * Optional columns to use for condition/onset/duration
  * Contrasts

Subject Lists fitz_dir/subjects.txt or subjects-{group_name}.txt
  * List of subject IDs to run
  * Optionally use different groups of subjects with ``-g`` commandline option
