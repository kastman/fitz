from textwrap import dedent
from argparse import RawDescriptionHelpFormatter


def run_parser(subparsers):
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
    parser = subparsers.add_parser('run', help='run')
    parser.description = help
    parser.formatter_class = RawDescriptionHelpFormatter
    parser.add_argument("--experiment", "-e", help="experimental paradigm")
    parser.add_argument("--model", "-m", help="model to fit")
    parser.add_argument("--workflows", "-w", nargs="*",
                        choices=["xnatconvert", "preproc", "onset", "model"],
                        help="which workflows to run")
    parser.add_argument("--subjects", "-s", nargs="*", dest="subjects",
                        help=("list of subject ids, name of file in lyman "
                              "directory, or full path to text file with "
                              "subject ids"))
    parser.add_argument("--plugin", "-p", default="multiproc",
                        choices=["linear", "multiproc", "ipython",
                                 "torque", "sge", "slurm"],
                        help="worklow execution plugin")
    parser.add_argument("--nprocs", "-n", default=4, type=int,
                        help="number of MultiProc processes to use")
    parser.add_argument("--queue", "-q", help="which queue for PBS/SGE execution")
    parser.add_argument("--dontrun", action="store_true",
                        help="don't actually execute the workflows")
    return parser
