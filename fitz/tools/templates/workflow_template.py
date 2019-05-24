"""{pipe_name} {workflow_name} workflow"""
# import os
# import numpy as np
# import pandas as pd
# import nibabel as nib

from nipype import (Node, SelectFiles, Workflow, MapNode,
                    IdentityInterface, DataSink, logging)

from nipype.interfaces.base import (
    BaseInterface, BaseInterfaceInputSpec, File, traits,
    InputMultiPath, OutputMultiPath, TraitedSpec, isdefined)
# from nipype.utils.filemanip import split_filename
import fitz

# from nipype.interfaces import spm
# from nipype.interfaces import fsl


default_parameters = dict(
)


def workflow_manager(project, exp, args, subj_source):
    """
    # ---------------------- #
    # {workflow_name} Workflow #
    # ---------------------- #

    Each workflow.py file should define a **workflow** method that takes the
    following options and returns a nipype workflow to execute:
       *def workflow(project,exp, args, subj_source)*:

    project
      A dictionary containing information about the directories in the project
      (e.g. working_dir, analysis_dir, data_dir)

    exp
      A dictionary containing information from the experiment config file,
      (e.g. options regarding slice-time correction, model contrasts)

    args
      An ``argparse.Parser`` instance containing command line options from
      ``fitz run``.

    subj_source
      A nipype node containing an IdentityInterface iterable for subjects,
      with the subject label stored as the output {{subject_id}}.

    For more info, see: http://people.fas.harvard.edu/~kastman/fitz/creating_fitz_pipelines.html
    """

    # Define Input Templates
    templates = dict(
        # timeseries=exp['timeseries'],
    )

    # Create Datasource
    source = Node(SelectFiles(templates, base_directory=project["data_dir"]),
                  "{workflow_name}_source")

    # Create main workflow and grab input and output nodes.
    wf, input_node, output_node = workflow_spec(exp_info=exp)

    # Convenience class to handle some sterotyped connections
    # between run-specific nodes (defined here) and the inputs
    # to the prepackaged workflow returned above
    inwrap = fitz.tools.graphutils.InputWrapper(wf, subj_source, source, input_node)
    inwrap.connect_inputs()

    # Store workflow outputs to persistant location
    sink = Node(DataSink(base_directory=project['analysis_dir']),
                "{workflow_name}_sink")

    # Similar to above, class to handle sterotyped output connections
    outwrap = fitz.tools.graphutils.OutputWrapper(wf, subj_source, sink, output_node)
    outwrap.set_subject_container()
    # outwrap.set_mapnode_substitutions(exp["n_runs"])
    outwrap.sink_outputs('outdir')

    # Set the base for the possibly temporary working directory
    wf.base_dir = project['working_dir']

    return wf


def workflow_spec(name="{workflow_name}", exp_info=None):
    """Return a Nipype workflow for MR processing.

    Parameters
    ----------
    name : string
        workflow object name
    exp_info : dict
        dictionary with experimental information
    """
    workflow = Workflow(name)

    if exp_info is None:
        exp_info = fitz.default_experiment_parameters()

    # Define the inputs for the preprocessing workflow
    in_fields = [""]  # "timeseries"]

    inputnode = Node(IdentityInterface(in_fields), "inputs")

    """
    # Define Actual Nipype Nodes, Workflows, etc.
    # e.g. The start of an example SPM preproc workflow
    # --------------------------------------------------

    slicetiming = pe.Node(interface=spm.SliceTiming(), name="slicetiming")
    slicetiming.inputs.ref_slice = 1
    realign = pe.Node(interface=spm.Realign(), name="realign")
    realign.inputs.register_to_mean = True
    """
    workflow.connect([
        """
        (inputnode, slicetiming,
            [('timeseries', 'in_files')]),
        (slicetiming, realign,
            [('timecorrected_files', 'in_files')]),
        """
    ])

    output_fields = [""]  # realigned_files", "realignment_parameters"]

    outputnode = Node(IdentityInterface(output_fields), "outputs")

    workflow.connect([
        """
        (realign, outputnode,
            [("realigned_files", "realigned_files"),
             ("realignment_parameters", "realignment_parameters")]),
        """
    ])

    # Return the workflow itself and input and output nodes.
    return workflow, inputnode, outputnode


"""
# Nipype Class Definitions (if needed)
# -------------------------------------
"""
