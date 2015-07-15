"""Forward facing fitz tools with information about ecosystem."""
import os
import re
import sys
import imp
import os.path as op

import numpy as np


def gather_project_info():
    """Import project information based on environment settings."""
    fitz_dir = os.environ["FITZ_DIR"]
    proj_file = op.join(fitz_dir, "project.py")
    try:
        project = sys.modules["project"]
    except KeyError:
        project = imp.load_source("project", proj_file)

    project_dict = dict()
    for dir in ["data", "analysis", "working", "crash"]:
        path = op.abspath(op.join(fitz_dir, getattr(project, dir + "_dir")))
        project_dict[dir + "_dir"] = path
    project_dict["default_exp"] = project.default_exp
    project_dict["rm_working_dir"] = project.rm_working_dir

    if hasattr(project, "ants_normalization"):
        use_ants = project.ants_normalization
        project_dict["normalization"] = "ants" if use_ants else "fsl"
    else:
        project_dict["normalization"] = "fsl"

    return project_dict


def gather_experiment_info(exp_name=None, model=None):
    """Import an experiment module and add some formatted information."""
    fitz_dir = os.environ["FITZ_DIR"]

    # Allow easy use of default experiment
    if exp_name is None:
        project = gather_project_info()
        exp_name = project["default_exp"]

    # Import the base experiment
    try:
        exp = sys.modules[exp_name]
    except KeyError:
        exp_file = op.join(fitz_dir, exp_name + ".py")
        exp = imp.load_source(exp_name, exp_file)

    exp_dict = default_experiment_parameters()

    def keep(k):
        return not re.match("__.*__", k)

    exp_dict.update({k: v for k, v in exp.__dict__.items() if keep(k)})

    # Possibly import the alternate model details
    if model is not None:
        check_modelname(model, exp_name)
        try:
            mod = sys.modules[model]
        except KeyError:
            model_file = op.join(fitz_dir, "%s-%s.py" % (exp_name, model))
            mod = imp.load_source(model, model_file)

        mod_dict = {k: v for k, v in mod.__dict__.items() if keep(k)}

        # Update the base information with the altmodel info
        exp_dict.update(mod_dict)

    # Save the __doc__ attribute to the dict
    exp_dict["comments"] = "" if exp.__doc__ is None else exp.__doc__
    if model is not None:
        exp_dict["comments"] += "" if mod.__doc__ is None else mod.__doc__

    # Check if it looks like this is a partial FOV acquisition
    exp_dict["partial_brain"] = bool(exp_dict.get("whole_brain_template"))

    # Temporal resolution. Mandatory.
    exp_dict["TR"] = float(exp_dict["TR"])

    # Set up the default contrasts
    if exp_dict["condition_names"] is not None:
        cs = [(name, [name], [1]) for name in exp_dict["condition_names"]]
        exp_dict["contrasts"] = cs + exp_dict["contrasts"]

    # Build contrasts list if neccesary
    exp_dict["contrast_names"] = [c[0] for c in exp_dict["contrasts"]]

    return exp_dict


def default_experiment_parameters():
    """Return default values for experiments."""
    exp = dict(

        source_template="",
        whole_brain_template="",
        n_runs=0,

        TR=2,
        frames_to_toss=0,
        temporal_interp=False,
        interleaved=True,
        coreg_init="fsl",
        slice_order="up",
        intensity_threshold=4.5,
        motion_threshold=1,
        spike_threshold=None,
        smooth_fwhm=6,
        hpf_cutoff=128,

        design_name=None,
        condition_names=None,
        regressor_file=None,
        regressor_names=None,
        hrf_model="GammaDifferenceHRF",
        temporal_deriv=False,
        confound_pca=False,
        hrf_params={},
        contrasts=[],
        memory_request=5,

        flame_mode="flame1",
        cluster_zthresh=2.3,
        grf_pthresh=0.05,
        peak_distance=30,
        surf_name="inflated",
        surf_smooth=5,
        sampling_units="frac",
        sampling_method="average",
        sampling_range=(0, 1, .1),
        surf_corr_sign="pos",

        )

    return exp


def determine_subjects(subject_arg=None):
    """Intelligently find a list of subjects in a variety of ways."""
    if subject_arg is None:
        subject_file = op.join(os.environ["FITZ_DIR"], "subjects.txt")
        subjects = np.loadtxt(subject_file, str, ndmin=1).tolist()
    elif op.isfile(subject_arg[0]):
        subjects = np.loadtxt(subject_arg[0], str).tolist()
    else:
        try:
            subject_file = op.join(os.environ["FITZ_DIR"],
                                   subject_arg[0] + ".txt")
            subjects = np.loadtxt(subject_file, str).tolist()
        except IOError:
            subjects = subject_arg
    return subjects


def determine_engine(args):
    """Read command line args and return Workflow.run() args."""
    plugin_dict = dict(linear="Linear", multiproc="MultiProc",
                       ipython="IPython", torque="PBS", sge="SGE",
                       slurm="SLURM")

    plugin = plugin_dict[args.plugin]

    plugin_args = dict()
    qsub_args = ""

    if plugin == "MultiProc":
        plugin_args['n_procs'] = args.nprocs
    elif plugin in ["SGE", "PBS"]:
        qsub_args += "-V -e /dev/null -o /dev/null "

    if args.queue is not None:
        qsub_args += "-q %s " % args.queue

    plugin_args["qsub_args"] = qsub_args

    return plugin, plugin_args


def run_workflow(wf, name=None, args=None):
    """Run a workflow, if we asked to do so on the command line."""
    plugin, plugin_args = determine_engine(args)
    wf.write_graph(str(wf), format='svg')
    if (name is None or name in args.workflows) and not args.dontrun:
        wf.run(plugin, plugin_args)


def update_params(wf_module, exp):
    # print sys.path, dir(wf_module), wf_module.__name__, wf_module.__file__
    try:
        params = wf_module.default_parameters()
    except IOError:
        print "Workflow must define a default_parameters method!"
        raise

    # default_names = set(params.keys())
    params.update(exp)
    # current_names = set(params.keys())
    # print default_names, current_names

    # new_names = current_names - default_names
    # print new_names
    # if len(new_names):
    #     msg = ["You may have an invalid configuration:"]
    #     for name in new_names:
    #         msg.append("A value for %s was specified, " % name +
    #                    "but not expected by the workflow")
    #     raise Exception(msg)
    return params


def check_modelname(model, exp_name):
    """Do Some sanity checks on the model"""
    err = []
    if model.endswith('.py'):
        err.append("Don't include '.py' when listing your model. ")
    if model.startswith(exp_name):
        err.append("Don't include the experiment name (%s) " % exp_name +
                   "when listing your model.")
    if len(err):
        err.insert(0, "Problem with the way you specified your model on " +
                      "the commandline:")
        raise IOError('\n- '.join(err))
