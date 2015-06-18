#!/usr/bin/env python
"""
Main execution script for fMRI analysis in the ecosystem.

"""

import os
import sys
import argparse
import nipype
from nipype import Node, SelectFiles, DataSink, config  # , IdentityInterface
import fitz
import fitz.workflows as wf
from fitz import tools
from textwrap import dedent
import os.path as op

print nipype.__file__
# config.enable_provenance()


def main(arglist):
    """Main function for workflow setup and execution."""
    args = parse_args(arglist)

    # Get and process specific information
    project = fitz.gather_project_info()
    exp = fitz.gather_experiment_info(args.experiment, args.altmodel)

    # Subject is always highest level of parameterization
    subject_list = fitz.determine_subjects(args.subjects)
    subj_source = tools.make_subject_source(subject_list)

    # Get the full correct name for the experiment
    if args.experiment is None:
        exp_name = project["default_exp"]
    else:
        exp_name = args.experiment

    exp_base = exp_name
    if args.altmodel is not None:
        exp_name = "-".join([exp_base, args.altmodel])

    # Set roots of output storage
    data_dir = project["data_dir"]
    analysis_dir = op.join(project["analysis_dir"], exp_name)
    working_dir = op.join(project["working_dir"], exp_name)
    # nipype.config.set("execution", "crashdump_dir", project["crash_dir"])
    # nipype.config.set("logging", "filemanip_level", 'DEBUG')
    # nipype.config.enable_debug_mode()
    # nipype.logging.update_logging(nipype.config)

    # Create symlinks to the preproc directory for altmodels
    if not op.exists(analysis_dir):
        os.makedirs(analysis_dir)
    if exp_base != exp_name:
        for subj in subject_list:
            subj_dir = op.join(analysis_dir, subj)
            if not op.exists(subj_dir):
                os.makedirs(subj_dir)
            link_dir = op.join(analysis_dir, subj, "preproc")
            if not op.exists(link_dir):
                preproc_dir = op.join("../..", exp_base, subj, "preproc")
                os.symlink(preproc_dir, link_dir)

    if 'preproc' in args.workflows:
        preproc_workflow(project, exp, args,
                         data_dir, analysis_dir, working_dir, subj_source)

    if 'onset' in args.workflows:
        onset_workflow(project, exp, args,
                       data_dir, analysis_dir, working_dir, subj_source)

    if 'model' in args.workflows:
        model_workflow(project, exp, args,
                       data_dir, analysis_dir, working_dir, subj_source)


def preproc_workflow(project, exp, args,
                     data_dir, analysis_dir, working_dir,
                     subj_source):
    # ----------------------------------------------------------------------- #
    # Preprocessing Workflow
    # ----------------------------------------------------------------------- #

    # Create workflow in function defined elsewhere in this package
    preproc, preproc_input, preproc_output = wf.create_preprocessing_workflow(
                                                exp_info=exp)

    # Collect raw nifti data
    preproc_templates = dict(timeseries=exp["source_template"],
                             anat=exp["anat_template"])

    preproc_source = Node(SelectFiles(preproc_templates,
                                      base_directory=project["data_dir"]),
                          "preproc_source")

    # Convenience class to handle some sterotyped connections
    # between run-specific nodes (defined here) and the inputs
    # to the prepackaged workflow returned above
    preproc_inwrap = tools.InputWrapper(preproc, subj_source,
                                        preproc_source, preproc_input)
    preproc_inwrap.connect_inputs()

    # Store workflow outputs to persistant location
    preproc_sink = Node(DataSink(base_directory=analysis_dir), "preproc_sink")

    # Similar to above, class to handle sterotyped output connections
    preproc_outwrap = tools.OutputWrapper(preproc, subj_source,
                                          preproc_sink, preproc_output)
    preproc_outwrap.set_subject_container()
    preproc_outwrap.set_mapnode_substitutions(exp["n_runs"])
    preproc_outwrap.sink_outputs("preproc")

    # Set the base for the possibly temporary working directory
    preproc.base_dir = working_dir

    # Possibly execute the workflow, depending on the command line
    fitz.run_workflow(preproc, "preproc", args)


def onset_workflow(project, exp, args,
                   data_dir, analysis_dir, working_dir,
                   subj_source):
    # ----------------------------------------------------------------------- #
    # Create Onsets
    # ----------------------------------------------------------------------- #

    # Create SPM.mat onsets files from design file.
    onset, onset_input, onset_output = wf.create_onset_workflow(
        exp_info=exp)
    onset_base = op.join(data_dir, "{subject_id}/design")
    design_file = exp["design_name"] + ".csv"
    onset_templates = dict(
        design_file=op.join(onset_base, design_file),
    )

    onset_source = Node(SelectFiles(onset_templates), "onsets_source")

    onset_inwrap = tools.InputWrapper(onset, subj_source,
                                      onset_source, onset_input)
    onset_inwrap.connect_inputs()

    onset_sink = Node(DataSink(base_directory=analysis_dir), "onset_sink")

    onset_outwrap = tools.OutputWrapper(onset, subj_source,
                                        onset_sink, onset_output)
    onset_outwrap.set_subject_container()
    onset_outwrap.set_mapnode_substitutions(exp["n_runs"])
    onset_outwrap.sink_outputs("onset")

    # Set temporary output locations
    onset.base_dir = working_dir

    # Possibly execute the workflow
    fitz.run_workflow(onset, "onset", args)


def model_workflow(project, exp, args,
                   data_dir, analysis_dir, working_dir,
                   subj_source):
    # ----------------------------------------------------------------------- #
    # Timeseries Model
    # ----------------------------------------------------------------------- #

    # Create a modelfitting workflow and specific nodes as above
    model, model_input, model_output = wf.create_timeseries_model_workflow(
        name="model", exp_info=exp)

    model_base = op.join(analysis_dir, "{subject_id}/preproc/")
    model_templates = dict(
        timeseries=op.join(model_base,
                           'sw*%s*.img' % op.splitext(op.basename(exp["source_template"]))[0]),
        realignment_params=op.join(model_base, "rp*.txt"),
        onset_files=op.join(analysis_dir, "{subject_id}/onset/*run*.mat")
        )

    # if exp["design_name"] is not None:
    #     design_file = exp["design_name"] + "*.mat"
    #     regressor_file = exp["design_name"] + ".csv"
    #     model_templates["design_file"] = op.join(data_dir, "{subject_id}",
    #                                              "design", design_file)
    # if exp["regressor_file"] is not None:
    #     regressor_file = exp["regressor_file"] + ".csv"
    #     model_templates["regressor_file"] = op.join(data_dir, "{subject_id}",
    #                                                 "design", regressor_file)

    model_source = Node(SelectFiles(model_templates), "model_source")

    model_inwrap = tools.InputWrapper(model, subj_source,
                                      model_source, model_input)
    model_inwrap.connect_inputs()

    model_sink = Node(DataSink(base_directory=analysis_dir), "model_sink")

    model_outwrap = tools.OutputWrapper(model, subj_source,
                                        model_sink, model_output)
    model_outwrap.set_subject_container()
    model_outwrap.set_mapnode_substitutions(exp["n_runs"])
    model_outwrap.sink_outputs("model")

    # Set temporary output locations
    model.base_dir = working_dir

    # Possibly execute the workflow
    fitz.run_workflow(model, "model", args)


def parse_args(arglist):
    """Take an arglist and return an argparse Namespace."""
    help = dedent("""
    Process subject-level data in fitz.

    This script controls the workflows that process data from raw Nifti files
    through a subject-level fixed effects model. It is based on the FSL FEAT
    processing stream and is enhanced with Freesurfer tools for coregistration.
    The other main difference is that the design generation is performed with
    custom code from the `moss.glm` package, although the design matrix
    creation uses the same rules as in FEAT and is expected to give highly
    similar results.

    By using Nipype's parallel machinery, the execution of this script can be
    distributed across a local or managed cluster. The script can thus be run
    for several subjects at once, and (with a large enough cluster) all of the
    subjects can be processed in the time it takes to process a single run of
    data linearly.

    At each stage of the pipeline, a number of static image files are created
    to summarize the results of the processing and facilitate quality
    assurance. These files are stored in the output directories alongside the
    data they correspond with and can be easily browsed using the ziegler
    web-app.

    The processing is organized into four large workflows that save their
    outputs in the analyis_dir hierarchy and can be executed independently.
    The structure of these workflows is represented in detail with the graphs
    that are on the website and in the source distribution. Briefly:

        preproc:

            Preprocess the raw timeseries files by realigning, skull-stripping,
            and filtering. Additionally, artifact detection is performed and
            coregistation to the anatomy is estimated, although the results of
            these stages are not applied to the data until later in the
            pipeline. A smoothed and an unsmoothed version of the final
            timeseries are always written to the analysis_dir.

        model:

            Estimate the timeseries model and generate inferential maps for the
            contrasts of interest. This model is estimated in the native run
            space, and separate models can be estimated for the smoothed and
            unsmoothed versions of the data.

        reg:

            Align the data from each run in a common space. There are two
            options for the target space: `mni`, which uses nonlinear
            normalization to the MNI template (this requires that the
            run_warp.py script has been executed), and `epi`, which transforms
            runs 2-n into the space of the first run. By default this registers
            the summary statistic images from the model, but it is also
            possible to transform the preprocessed timeseries without having
            run the model workflow. Additionally, there is an option to
            transform the unsmoothed version of these data. (The results are
            saved separately for each of these choices, so it is possible to
            use several or all of them). The ROI mask generation script
            (make_masks.py) produces masks in the epi space, so this workflow
            must be run before doing ROI/decoding analyses.

        ffx:

            Estimate the across-run fixed effects model. This model combines
            the summary statistics from each of the runs and produces a single
            set of model results, organized by contrast, for each subject. It
            is possible to fit the ffx model in either the mni or epi space and
            on either smoothed or unsmoothed data. Fixed effects results in the
            mni space can be used for volume-based group analysis, and the
            results in the epi space can be used with the surface-based group
            pipeline.

    Many details of these workflows can be configured by setting values in the
    experiment file. Additionally, it is possible to preprocess the data for an
    experiment once and then estimate several different models using altmodel
    files.

    If you do not delete your cache directory after running (which is
    configured in the project file), repeated use of this script will only
    rerun the nodes that have changes to their inputs. Otherwise, you will
    have to rerun at the level of the workflows.


    Examples
    --------


    Note that the parameter switches match any unique short version
    of the full parameter name.

    run_fmri.py -w preproc model reg ffx

        Run every stage of processing for the default experiment for each
        subject defined in $FITZ_DIR/subjects.txt. Coregistration will be
        performed for smoothed model outputs in the mni space. The processing
        will be distributed locally with the MultiProc plugin using 4
        processes.

    run_fmri.py -s subj1 subj2 subj3 -w preproc -p sge -q batch.q

        Run preprocessing of the default experiment for subjects `subj1`,
        `subj2`, and `subj3` with distributed execution in the `batch.q` queue
        of the Sun Grid Engine.

    run_fmri.py -s pilot_subjects -w preproc -e nback -n 8

        Preprocess the subjects enumerated in $FITZ_DIR/pilot_subjects.txt
        with the experiment details in $FITZ_DIR/nback.py. Distribute the
        execution locally with 8 parallel processes.

    run_fmri.py -s subj1 -w model reg ffx -e nback -a parametric

        Fit the model, register, and combine across runs for subject `subj1`
        with the experiment details defined in $FITZ_DIR/nback-parametric.py.
        This assumes preprocessing has been performed for the nback experiment.

    run_fmri.py -w preproc reg -t -u -reg epi

        Preprocess the default experiment for all subjects, and then align
        the unsmoothed timeseries into the epi space. This is the standard set
        of processing that must be performed before multivariate analyses.

    run_fmri.py -w reg ffx -reg epi

        Align the summary statistics for all subjects into the epi space and
        then combine across runs. This is the standard processing that must
        be added to use surface-based group analyses.

    run_fmri.py -w preproc model reg ffx -dontrun

        Set up all of the workflows for the default experiment, but do not
        actually submit them for execution. This can be useful for testing
        before starting a large job.

    Usage Details
    -------------

    """)
    parser = tools.parser
    parser.description = help
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.add_argument("--experiment", "-e", help="experimental paradigm")
    parser.add_argument("--altmodel", "-a", help="alternate model to fit")
    parser.add_argument("--workflows", "-w", nargs="*",
                        choices=["preproc", "onset", "model"],
                        help="which workflows to run")
    return parser.parse_args(arglist)


if __name__ == '__main__':
    main(sys.argv[1:])
