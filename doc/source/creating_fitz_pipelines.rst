.. _creating_fitz_pipelines:

Creating New Fitz Pipelines
============================

Fitz allows for pipelines to be easily created and updated by handling some of
the more redundant boilerplate that arises. Here is an example of slotting in
an existing nipype pipeline within the Fitz ecosystem.

Let's say we want to add a simple diffusion pipeline provided as part of
nipype and hook it up with our experiment files.

Fitz pipelines are separate git repositories that can be shared and cloned.

The requirements for a pipeline are:

1. They must contain a workflows folder containing a separate python file for
   each main workflow. For example, in standard fMRI workflows preprocessing
   and modelling are good "chunks" of processing.

2. Each .py file should define a **workflow** method that takes the following
   options and returns a nipype workflow to execute:
   *def workflow(project,exp, args, subj_source)*:

project
  A dictionary containing information about the directories in the project (e.g.
  working_dir, analysis_dir, data_dir)

exp
  A dictionary containing information from the experiment config file, (e.g.
  options regarding slice-time correction, model contrasts)

args
  An ``argparse.Parser`` instance containing command line options from
  ``fitz run``.

subj_source
  A nipype node containing the IdentityInterface iterable for subjects, with
  the subject label stored as the output {subject_id}.
