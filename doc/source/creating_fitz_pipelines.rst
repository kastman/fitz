.. _creating_fitz_pipelines:

Creating New Fitz Pipelines
============================

Fitz allows for pipelines to be easily created and updated by handling some of
the more redundant boilerplate that arises. Pipelines are simply directories
(ideally checked into git) that follow a certain structure, which can be shared
and easily downloaded into place. The ``fitz new workflow`` command creates
workflow files containing common boilerplate code that can be executed (with
some proper configuration) by ``fitz run``:

.. code-block:: bash

  fitz new workflow pipeline_name workflow_name

This will create a directory for your pipeline in the **FITZ_DIR** named
*pipeline_name* (if it doesn't exist already) and a file named
*workflows/workflow_name.py* inside it with a standard workflow file. The new
template file has two important methods: ``workflow_manager`` and
``workflow_spec``:

Each pipeline contains a ``workflows`` directory, containing a .py file for
each set of steps, or workflow. For example, in a standard fMRI **pipeline**,
there are separate workflows for preprocessing (realign, slice-time correction,
smoothing), onset preparation, and modeling.

Workflow File Requirements
---------------------------

Each workflow **must** define a ``workflow_manager`` method that takes the following
inputs and returns the following outputs:

``def workflow_manager(project, exp, args, subj_source)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The workflow method handles a lot of boilerplate code that sets workflow
directories and settings. It usually doesn't change much from workflow to
workflow (you may never need to change this from what is copied by
``fitz new workflow``).

Inputs:

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

Outputs:

workflow
  The workflow returns a fully configured nipype method that is ready to
  ``.run()``

``def workflow_spec(exp, name):``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Additionally, a workflow should also specify a ``workflow_spec`` method as well.
The spec (in contrast to the manager) contains very little boilerplate and will
be more or less unique depending on the actual processing steps requested.
method where the actual processing steps (nipype Nodes and connections) are
specified. It doesn't know or care about how to find data or where to save it
at the end of processing, but only specifies what to do with the inputs it
receives.

Inputs:

exp
  This is the experiment dictionary that contains options for the processing.

name
  This is the name that the experiment will have in the nipype hierarchy.
  Something similar (usually the name of the workflow file) is good.

Example
---------

Let's say we want to add a simple diffusion pipeline provided as part of
nipype and hook it up with our experiment files. For ease of discussion,
let's use the determinisitc "compute tensor" half of this `basic FSL dti`_
example to get FDT fractional anisotropy (FA) and mean diffusivity (MD) maps.

First, create a pipeline directory and dti workflow:

.. code-block:: bash

  fitz new workflow DTI_Pipeline dti

This will create a new pipeline in the FITZ_DIR::

  FITZ_DIR
  └── DTI_Pipeline
      ├── README.rst
      └── workflows
          └── dti.py

Take a look at DTI_Pipeline/workflows/dti.py. You'll see that there are some
examples for a simple SPM fMRI pipeline. Let's edit them so that they refelct
DTI.

In FITZ, unprocessed data are put in the **data** directory, so let's
specify that we want to grab some raw dti nifti images:

.. code-block:: python

  def workflow_manager(project, exp, args, subj_source):
    ...
    # Define Input Templates
    templates = dict(
        dti=exp['dti_template'],
        bvecs=exp['bvecs_template'],
        bvals=exp['bvals_template']
    )

    # Create Datasource
    source = Node(SelectFiles(templates, base_directory=project["data_dir"]),
                  "dti_source")

Every key in the exp dictionary is a variable in a FITZ experiment file, so
let's start that Experiment file and fill it in as we go. Create a new file in
the FITZ_DIR called dti.py, and put in the following:

.. code-block:: python

  # Workflow Parameters
  # --------------------
  workflow = "DTI_Pipeline"
  workflow_src = ""
  workflow_version = ""

  # DTI Options
  # -------------
  dwi_template = "{subject_id}/images/*.nii"
  bvecs_template = "{subject_id}/images/bvecs.txt"
  bvals_template = "{subject_id}/images/bvals.txt"

This says that you want to use the "DTI_Pipeline" that you've just created,
although the ``workflow_src`` and ``workflow_version`` are empty because this
is a local workflow. (Don't forget to check in and publicize your workflow!)
It also provides instructions on how to load the raw diffusion images for each
subject. For example, this template would be correct if the dti data for the
first subject was in: data/sub001/images/DTI.nii

``project["data_dir"]`` is the value set in project.py, so you won't need to
change this.

The rest of the ``workflow_manager`` method can be left entirely alone! It is
setting up connections to various directories, and as long as follow the
standard fitz setup everything is already correct. Skip down to the
``workflow_spec`` method to specify exactly what the workflow should do.

The next thing we have to do is specify that we're inputting a dti image and
values / vectors text files:

.. code-block :: python

  def workflow_spec(name="dti", exp_info=None):
    ...
    # Define the inputs for the preprocessing workflow
    in_fields = ["dwi", "bvecs", "bvals"]

Then we can pretty-much copy paste the deterministic parts of the pipeline
from our example:

.. code-block:: python

  fslroi = pe.Node(interface=fsl.ExtractROI(),name='fslroi')
  fslroi.inputs.t_min=0
  fslroi.inputs.t_size=1

  bet = pe.Node(interface=fsl.BET(),name='bet')
  bet.inputs.mask=True
  bet.inputs.frac=0.34

  eddycorrect = create_eddy_correct_pipeline('eddycorrect')
  eddycorrect.inputs.inputnode.ref_num=0

  dtifit = pe.Node(interface=fsl.DTIFit(),name='dtifit')

  workflow.connect([
    (fslroi, bet, [('roi_file','in_file')]),
    (eddycorrect, dtifit, [('outputnode.eddy_corrected','dwi')]),
    (infosource, dtifit, [['subject_id','base_name']]),
    (bet, dtifit, [('mask_file','mask')])
  ])

Finally, we want to specify what data we want to save and connect it to our
outputnode.

.. code-block:: python

  output_fields = ["FA", "L1", "L2", "L3", "MD", "MO", "S0",
                         "V1", "V2", "V3", "tensor"]

  outputnode = Node(IdentityInterface(output_fields), "outputs")

  workflow.connect([
    (dtifit, outputnode, [
            ('FA', 'FA'),
            ('L1', 'L1'),
            ('L2', 'L2'),
            ('L3', 'L3'),
            ('MD', 'MD'),
            ('MO', 'MO'),
            ('S0', 'S0'),
            ('V1', 'V1'),
            ('V2', 'V2'),
            ('V3', 'V3'),
            ('tensor', 'tensor')]),
  ])

  return workflow, inputnode, outputnode

The overhead for this basic example is pretty high so you'd likely be developing
a much more complex pipeline. Nonetheless, the ability to run the pipeline
with new data just by creating a handful of configuration files is hopefully
worth the time.

Don't forget to make your pipeline a repository, commit it and share it when
you've got it working how you want so that others can easily ``fitz install``
it!

.. _`basic FSL dti` : http://nipy.org/nipype/users/examples/dmri_fsl_dti.html
