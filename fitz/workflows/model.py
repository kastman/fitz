"""Timeseries model using SPM"""
# import re
import os.path as op
from numpy import isnan
from scipy.io import loadmat
# import pandas as pd
# import nibabel as nib
# import matplotlib.pyplot as plt
# from moss import glm
# from moss.mosaic import Mosaic
# import seaborn as sns

from nipype import Node, Workflow, IdentityInterface
# from nipype.interfaces import fsl
from nipype.interfaces import spm
from nipype.pipeline import engine as pe
from nipype.algorithms import rapidart as ra, modelgen as model
from nipype.interfaces.base import (BaseInterface,
                                    BaseInterfaceInputSpec,
                                    InputMultiPath,
                                    # OutputMultiPath,
                                    Bunch,
                                    TraitedSpec,
                                    File,
                                    traits,
                                    # isdefined
                                    )
import fitz


def create_timeseries_model_workflow(name="model", exp_info=None):
    # Default experiment parameters for generating graph image, testing, etc.
    if exp_info is None:
        exp_info = fitz.default_experiment_parameters()

    # Define constant inputs
    inputs = ["realignment_params", "timeseries", "onset_files"]
    #
    # # Possibly add the design and regressor files to the inputs
    # if exp_info["design_name"] is not None:
    #     inputs.append("design_file")
    # if exp_info["regressor_file"] is not None:
    #     inputs.append("regressor_file")

    # Define the workflow inputs
    inputnode = Node(IdentityInterface(inputs), "inputs")

    art = create_artifactdetect()

    load_onsets = pe.Node(interface=LoadOnsetsInterface(),
                          name='load_onsets')
    load_onsets.inputs.raise_on_short_conditions = 'raise'

    modelspec = create_modelspec(exp_info)

    level1design = create_level1design(exp_info)
    level1design.inputs.bases = exp_info['bases']

    level1estimate = create_level1estimate(exp_info)

    # Replace the 'T' in the contrast list for nipype (vs. lyman)
    contrastestimate = create_contrastestimate(exp_info)
    contrastestimate.inputs.contrasts = [
        (c[0], 'T', c[1], c[2]) for c in exp_info['contrasts']]

    # Define the workflow and connect the nodes
    model = Workflow(name=name)

    model.connect([
        (inputnode, art,
            [('realignment_params', 'realignment_parameters'),
             ('timeseries', 'realigned_files')]),
        (inputnode, load_onsets,
            [('onset_files', 'onset_files')]),
        (inputnode, modelspec,
            [('realignment_params', 'realignment_parameters'),
             ('timeseries', 'functional_runs')]),
        (load_onsets, modelspec,
            [('onsets_infos', 'subject_info')]),
        (art, modelspec,
            [('outlier_files', 'outlier_files')]),
        (modelspec, level1design,
            [('session_info', 'session_info')]),
        (level1design, level1estimate,
            [('spm_mat_file', 'spm_mat_file')]),
        (level1estimate, contrastestimate,
            [('spm_mat_file', 'spm_mat_file'),
             ('beta_images', 'beta_images'),
             ('residual_image', 'residual_image')]),
    ])

    # Define the workflow outputs
    outputnode = Node(IdentityInterface(["beta_images",
                                         "mask_image",
                                         "residual_image",
                                         "RPVimage",
                                         "con_images",
                                         "spmT_images",
                                         "spm_mat_file",
                                         "outlier_files",
                                         #  "censor_rpt",
                                         #  "censor_csv",
                                         #  "censor_json",
                                         ]),
                      "outputs")

    model.connect([
        (level1estimate, outputnode,
            [('beta_images', 'beta_images'),
             ('mask_image', 'mask_image'),
             ('residual_image', 'residual_image'),
             ('RPVimage', 'RPVimage')]),
        (contrastestimate, outputnode,
            [('con_images', 'con_images'),
             ('spmT_images', 'spmT_images'),
             ('spm_mat_file', 'spm_mat_file')]),
        (art, outputnode,
            [('outlier_files', 'outlier_files')]),
        # (threshold_outliers, outputnode,
        #     [('censor_rpt', 'censor_rpt'),
        #      ('censor_csv', 'censor_csv'),
        #      ('censor_json', 'censor_json')]),
    ])

    return model, inputnode, outputnode


# =========================================================================== #
# Northwest Labs Preprocessing Shared Workflows                               #
# ekk 12Nov12                                                                 #
# =========================================================================== #


def create_artifactdetect(name='art'):
    """Use :class:`nipype.algorithms.rapidart` to determine which of the
    images in the functional series are outliers based on deviations in
    intensity or movement.
    """
    art = pe.Node(interface=ra.ArtifactDetect(), name=name)
    art.inputs.use_differences = [True, False]
    art.inputs.use_norm = True
    art.inputs.norm_threshold = 1
    art.inputs.zintensity_threshold = 3
    art.inputs.mask_type = 'spm_global'
    art.inputs.parameter_source = 'SPM'
    art.inputs.save_plot = False  # Don't save plots when running on cluster

    return art


def create_modelspec(exp_info, name='modelspec'):
    """Generate SPM-specific design information using
    :class:`nipype.interfaces.spm.SpecifyModel`.
    """
    modelspec = pe.Node(interface=model.SpecifySPMModel(),
                        name="modelspec", run_without_submitting=True)
    modelspec.inputs.concatenate_runs = False
    modelspec.inputs.input_units = exp_info['input_units']
    modelspec.inputs.output_units = 'secs'
    modelspec.inputs.high_pass_filter_cutoff = exp_info['hpcutoff']
    modelspec.inputs.time_repetition = exp_info['TR']

    return modelspec


def create_level1design(exp_info, name='level1design'):
    """Generate a first level SPM.mat file for analysis
    :class:`nipype.interfaces.spm.Level1Design`.
    """
    level1design = pe.Node(interface=spm.Level1Design(), name=name)
    level1design.inputs.timing_units = exp_info['output_units']
    level1design.inputs.bases = exp_info['bases']
    level1design.inputs.interscan_interval = exp_info['TR']
    return level1design


def create_level1estimate(exp_info, name='level1estimate'):
    """Use :class:`nipype.interfaces.spm.EstimateModel` to determine the
    parameters of the model.
    """
    level1estimate = pe.Node(interface=spm.EstimateModel(), name=name)
    level1estimate.inputs.estimation_method = {exp_info['estimation_method']: 1}
    return level1estimate


def create_contrastestimate(exp_info, name='contrastestimate'):
    """Use :class:`nipype.interfaces.spm.EstimateContrast` to estimate the
    first level contrasts specified in the task_list dictionary above.
    """
    contrastestimate = pe.Node(interface=spm.EstimateContrast(), name=name)
    return contrastestimate

####### Begin LoadOnsetsInterface ########
class LoadOnsetsInterfaceInputSpec(BaseInterfaceInputSpec):
    onset_files = InputMultiPath(traits.Either(traits.List(File(exists=True)),File(exists=True)),
                    desc='Computed MATLAB .mat SPM onsets files', mandatory=True)
    raise_on_short_conditions = traits.Enum('raise', 'remove', 'ignore',
                    desc='Raise an error or remove empty conditions?', usedefault=True)
    conditions_list = traits.List(desc='Optional list of conditions to include. Loads all conditions in file if not present')
    raise_on_nan_values = traits.Enum('raise','ignore',
                    desc='Raise an error or remove values that are nan?', usedefault=True)

class LoadOnsetsInterfaceOutputSpec(TraitedSpec):
    onsets_infos = traits.List(desc="Loaded Nipype Onsets Bunches")

class LoadOnsetsInterface(BaseInterface):
    '''The LoadOnsets Interface just reads a correctly formatted
    MATLAB .mat SPM onsets file from disk and returns a Nipype Onsets Bunch.

    Loosely based on the standard subjectinfo method from several Nipype examples.'''
    input_spec = LoadOnsetsInterfaceInputSpec
    output_spec = LoadOnsetsInterfaceOutputSpec

    def _run_interface(self, runtime):
        self.onsets_infos = []
        conditions_list = self.inputs.conditions_list

        for srcmat in self.inputs.onset_files:
            if not op.exists(srcmat):
                raise IOError("Can't find input onsets file %s" % srcmat)
            mat = loadmat(srcmat)
            if 'names' not in mat.keys():
                raise KeyError("Onsets file %s doesn't appear to be a valid SPM multiple regressors file; found keys %s instead of ['names', 'onsets', 'durations']. " % (srcmat, mat.keys()))

            # SPM Multiple Regressors Files should be all rows. The cell structure creates
            # double layers, so to get each item when loaded address one level in, and then
            # to get each item address one level in again.
            nConditions = len(mat['names'][0])
            names,durations,onsets=[],[],[]

            for i in range(nConditions):
                # Go through each condition and cast it into Stdlibrary strings and lists for Nipype
                name = str(mat['names'][0][i][0])
                # print mat['onsets'][0]
                # print mat['onsets'][0][i][0]
                if conditions_list and (name not in conditions_list):
                    print 'Skipping %s' % name
                    continue
                else:
                    print 'Found %s' % name
                duration = list(mat['durations'][0][i].flatten().tolist())

                if len(mat['onsets'][0][i]):
                    onset = list(mat['onsets'][0][i][0])
                else:
                    onset = []

                names.append(name)
                durations.append(duration)
                onsets.append(onset)

            if conditions_list:
                for cond in conditions_list:
                    if cond not in names:
                        raise RuntimeError("Warning, condition %s not found in %s, got %s"%(cond,srcmat,names))

            for index, onset in enumerate(onsets):
                # print index,onset,len(onset)
                if len(onset) == 0:
                    if self.inputs.raise_on_short_conditions == 'raise':
                        raise AssertionError("Condition %s is too short to be a valid condition: %s (%s)" % (names[index], onset, srcmat))
                    elif self.inputs.raise_on_short_conditions == 'remove':
                        action = "removing"
                        names.pop(index)
                        durations.pop(index)
                        onsets.pop(index)
                    else:
                        action = "ignoring"
                    print "==> Condition %s was short for file %s (length %d), %s..." % (names[index], srcmat, len(onset), action)
                if isnan(sum(onset)):
                    if self.inputs.raise_on_nan_values == 'raise':
                        raise AssertionError("Condition %s contains NaNs and raise_on_nan_values is true. %s (%s)" % (names[index], onset, srcmat))
                    else:
                        print "==> Condition %s for file %s contains NaN values, but continuing anyway..." % (names[index], srcmat)

            self.onsets_infos.append(Bunch(dict(
                conditions=names,
                onsets=onsets,
                durations=durations
            )))


        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["onsets_infos"] = self.onsets_infos
        return outputs


    #
    #
    # workflow.connect([
    #     (onsetnode, load_onsets,
    #         [('onsets_files', 'onsets_files')]),
    #     (modelinfo, load_onsets,
    #         [('conditions','conditions_list')]),
    #     # (inputspec, build_subject_info, [('func_images', 'func_images')]),
    #     # (load_onsets, build_subject_info, [('onsets_infos', 'onsets_infos')]),
    #
    #     # (modelinfo, build_pmods,     [('pmod_name', 'pmod_name')]),
    #     (build_subject_info, modelspec,
    #         [('subject_info', 'subject_info')]),
    #     (rpnode, art,
    #         [('realignment_parameters','realignment_parameters'),
    #                       ('realigned_files', 'realigned_files')]),
    #
    #     (rpnode, threshold_outliers, [('realignment_parameters','realignment_parameters')]),
    #     (art, threshold_outliers, [('outlier_files','outlier_files')]),
    #
    #     # (pmodsource, validate_pmods, [('pmods_files','pmods_files')]),
    #
    #     # Threshold Inputs according to Art Censors and Valid Pmods
    #     # (validate_pmods, select_runs, [('selected_indices','pmods_indices')]),
    #     # (threshold_outliers, select_runs, [('selected_indices', 'outliers_indices')]),
    #
    #     # Select Onsets
    #     (threshold_outliers, select_onsets, [('selected_indices','index')]),
    #     (load_onsets, select_onsets, [('onsets_infos','inlist')]),
    #     (select_onsets, build_subject_info, [(('out',as_list), 'onsets_infos')]),
    #
    #     # Select Images
    #     (threshold_outliers, select_images, [('selected_indices','index')]),
    #     (imagenode, select_images, [('func_images','inlist')]),
    #     (select_images, modelspec, [(('out',as_list), 'functional_runs')]),
    #     (select_images, build_subject_info, [(('out',as_list), 'func_images')]),
    #
    #     # Select RPs
    #     (threshold_outliers, select_rps, [('selected_indices','index')]),
    #     (rpnode, select_rps, [('realignment_parameters','inlist')]),
    #     (select_rps, restrict_rps, [(('out',as_list),'inlist')]),
    #     (modelinfo, restrict_rps, [('use_motion_rps','should_include')]),
    #     (restrict_rps,modelspec, [('outlist','realignment_parameters')]),
    #
    #     # Select Outliers
    #     (threshold_outliers, select_outliers, [('selected_indices', 'index')]),
    #     (art, select_outliers, [('outlier_files', 'inlist')]),
    #     (select_outliers, restrict_outliers, [(('out',as_list),'inlist')]),
    #     (modelinfo, restrict_outliers, [('use_outliers','should_include')]),
    #     (restrict_outliers, modelspec, [('outlist','outlier_files')]),
    #
    #     # (select_runs, select_pmods, [('selected_indices', 'index')]),
    #     # (pmodsource, select_pmods, [('pmods_files','inlist')]),
    #     #                             # (('pmods_files',ignore_exceptions_for),'ignore_exception')]),
    #     # (select_pmods, build_pmods,[(('out',as_list),'pmods_param_files')]),
    #     # (select_onsets, build_pmods,[(('out',as_list),'onsets_infos')]),
    #     # (build_pmods, build_subject_info, [('pmods_infos', 'pmods_infos')]),
    #
    #
    #     (threshold_outliers, build_subject_info, [('selected_indices','selected_indices')]),
    #
    #     # (additionalregressorssource, load_additional_regressors, [('additional_regressors', 'additional_regressors_files')]),
    #     # (load_additional_regressors, modelspec, [('additional_regressors', 'additional_regressors'),
    #     #                                           ('additional_regressors_names', 'additional_regressors_names')]),
    #     (modelinfo, level1design, [('bases', 'bases')]),
    #     (modelspec, level1design, [('session_info', 'session_info')]),
    #     (level1design, level1estimate, [('spm_mat_file', 'spm_mat_file')]),
    #     (level1estimate, contrastestimate, [('spm_mat_file', 'spm_mat_file'),
    #                                         ('beta_images', 'beta_images'),
    #                                         ('residual_image', 'residual_image')]),
    #     (modelinfo, contrastestimate, [('contrasts', 'contrasts')])
    # ])
    #
    #

# =========================================================================== #

#
# class ModelSetupInput(BaseInterfaceInputSpec):
#
#     exp_info = traits.Dict()
#     timeseries = File(exists=True)
#     design_file = File(exists=True)
#     realign_file = File(exists=True)
#     artifact_file = File(exists=True)
#     regressor_file = File(exists=True)
#
#
# class ModelSetupOutput(TraitedSpec):
#
#     design_matrix_file = File(exists=True)
#     contrast_file = File(exists=True)
#     design_matrix_pkl = File(exists=True)
#     report = OutputMultiPath(File(exists=True))
#
#
# class ModelSetup(BaseInterface):
#
#     input_spec = ModelSetupInput
#     output_spec = ModelSetupOutput
#
#     def _run_interface(self, runtime):
#
#         # Get all the information for the design
#         design_kwargs = self.build_design_information()
#
#         # Initialize the design matrix object
#         X = glm.DesignMatrix(**design_kwargs)
#
#         # Report on the design
#         self.design_report(self.inputs.exp_info, X, design_kwargs)
#
#         # Write out the design object as a pkl to pass to the report function
#         X.to_pickle("design.pkl")
#
#         # Finally, write out the design files in FSL format
#         X.to_fsl_files("design", self.inputs.exp_info["contrasts"])
#
#         return runtime
#
#     def build_design_information(self):
#
#         # Load in the design information
#         exp_info = self.inputs.exp_info
#         tr = self.inputs.exp_info["TR"]
#
#         # Derive the length of the scan and run number from the timeseries
#         ntp = nib.load(self.inputs.timeseries).shape[-1]
#         run = int(re.search("run_(\d+)", self.inputs.timeseries).group(1))
#
#         # Get the experimental design
#         if isdefined(self.inputs.design_file):
#             design = pd.read_csv(self.inputs.design_file)
#             design = design[design["run"] == run]
#         else:
#             design = None
#
#         # Get the motion correction parameters
#         realign = pd.read_csv(self.inputs.realign_file)
#         realign = realign.filter(regex="rot|trans").apply(stats.zscore)
#
#         # Get the image artifacts
#         artifacts = pd.read_csv(self.inputs.artifact_file).max(axis=1)
#
#         # Get the additional model regressors
#         if isdefined(self.inputs.regressor_file):
#             regressors = pd.read_csv(self.inputs.regressor_file)
#             regressors = regressors[regressors["run"] == run]
#             regressors = regressors.drop("run", axis=1)
#             if exp_info["regressor_names"] is not None:
#                 regressors = regressors[exp_info["regressor_names"]]
#             regressors.index = np.arange(ntp) * tr
#         else:
#             regressors = None
#
#         # Set up the HRF model
#         hrf = getattr(glm, exp_info["hrf_model"])
#         hrf = hrf(exp_info["temporal_deriv"], tr, **exp_info["hrf_params"])
#
#         # Build a dict of keyword arguments for the design matrix
#         design_kwargs = dict(design=design,
#                              hrf_model=hrf,
#                              ntp=ntp,
#                              tr=tr,
#                              confounds=realign,
#                              artifacts=artifacts,
#                              regressors=regressors,
#                              condition_names=exp_info["condition_names"],
#                              confound_pca=exp_info["confound_pca"],
#                              hpf_cutoff=exp_info["hpf_cutoff"])
#
#         return design_kwargs
#
#     def design_report(self, exp_info, X, design_kwargs):
#         """Generate static images summarizing the design."""
#         # Plot the design itself
#         design_png = op.abspath("design.png")
#         X.plot(fname=design_png, close=True)
#
#         with sns.axes_style("whitegrid"):
#             # Plot the eigenvalue spectrum
#             svd_png = op.abspath("design_singular_values.png")
#             X.plot_singular_values(fname=svd_png, close=True)
#
#             # Plot the correlations between design elements and confounds
#             corr_png = op.abspath("design_correlation.png")
#             if design_kwargs["design"] is None:
#                 with open(corr_png, "wb"):
#                     pass
#             else:
#                 X.plot_confound_correlation(fname=corr_png, close=True)
#
#         # Build a list of images sumarrizing the model
#         report = [design_png, corr_png, svd_png]
#
#         # Now plot the information loss from the high-pass filter
#         design_kwargs["hpf_cutoff"] = None
#         X_unfiltered = glm.DesignMatrix(**design_kwargs)
#         tr = design_kwargs["tr"]
#         ntp = design_kwargs["ntp"]
#
#         # Plot for each contrast
#         for i, (name, cols, weights) in enumerate(exp_info["contrasts"], 1):
#
#             # Compute the contrast predictors
#             C = X.contrast_vector(cols, weights)
#             y_filt = X.design_matrix.dot(C)
#             y_unfilt = X_unfiltered.design_matrix.dot(C)
#
#             # Compute the spectral density for filtered and unfiltered
#             fs, pxx_filt = signal.welch(y_filt, 1. / tr, nperseg=ntp)
#             fs, pxx_unfilt = signal.welch(y_unfilt, 1. / tr, nperseg=ntp)
#
#             # Draw the spectral density
#             with sns.axes_style("whitegrid"):
#                 f, ax = plt.subplots(figsize=(9, 3))
#             ax.fill_between(fs, pxx_unfilt, color="#C41E3A")
#             ax.axvline(1.0 / exp_info["hpf_cutoff"], c=".3", ls=":", lw=1.5)
#             ax.fill_between(fs, pxx_filt, color=".5")
#
#             # Label the plot
#             ax.set(xlabel="Frequency",
#                    ylabel="Spectral Density",
#                    xlim=(0, .15))
#             plt.tight_layout()
#
#             # Save the plot
#             fname = op.abspath("cope%d_filter.png" % i)
#             f.savefig(fname, dpi=100)
#             plt.close(f)
#             report.append(fname)
#
#         # Store the report files for later
#         self.report_files = report
#
#     def _list_outputs(self):
#
#         outputs = self._outputs().get()
#         outputs["report"] = self.report_files
#         outputs["contrast_file"] = op.abspath("design.con")
#         outputs["design_matrix_pkl"] = op.abspath("design.pkl")
#         outputs["design_matrix_file"] = op.abspath("design.mat")
#         return outputs
#
#
# class ModelSummaryInput(BaseInterfaceInputSpec):
#
#     design_matrix_pkl = File(exists=True)
#     timeseries = File(exists=True)
#     pe_files = InputMultiPath(File(exists=True))
#
#
# class ModelSummaryOutput(TraitedSpec):
#
#     r2_files = OutputMultiPath(File(exists=True))
#     ss_files = OutputMultiPath(File(exists=True))
#     tsnr_file = File(exists=True)
#
#
# class ModelSummary(BaseInterface):
#
#     input_spec = ModelSummaryInput
#     output_spec = ModelSummaryOutput
#
#     def _run_interface(self, runtime):
#
#         # Load the design matrix object
#         X = glm.DesignMatrix.from_pickle(self.inputs.design_matrix_pkl)
#
#         # Load and de-mean the timeseries
#         ts_img = nib.load(self.inputs.timeseries)
#         ts_aff, ts_header = ts_img.get_affine(), ts_img.get_header()
#         y = ts_img.get_data()
#         ybar = y.mean(axis=-1)[..., np.newaxis]
#         y -= ybar
#         self.y = y
#
#         # Store the image attributes
#         self.affine = ts_aff
#         self.header = ts_header
#
#         # Load the parameter estimates, make 4D, and concatenate
#         pes = [nib.load(f).get_data() for f in self.inputs.pe_files]
#         pes = [pe[..., np.newaxis] for pe in pes]
#         pes = np.concatenate(pes, axis=-1)
#
#         # Compute and save the total sum of squares
#         self.sstot = np.sum(np.square(y), axis=-1)
#         self.save_image(self.sstot, "sstot")
#
#         # Compute the full model r squared
#         yhat_full = self.dot_by_slice(X, pes)
#         ss_full, r2_full = self.compute_r2(yhat_full)
#         self.save_image(ss_full, "ssres_full")
#         self.save_image(r2_full, "r2_full")
#
#         # Compute the main model r squared
#         yhat_main = self.dot_by_slice(X, pes, "main")
#         ss_main, r2_main = self.compute_r2(yhat_main)
#         self.save_image(ss_main, "ssres_main")
#         self.save_image(r2_main, "r2_main")
#
#         # Compute the confound model r squared
#         yhat_confound = self.dot_by_slice(X, pes, "confound")
#         _, r2_confound = self.compute_r2(yhat_confound)
#         self.save_image(r2_confound, "r2_confound")
#
#         # Compute and save the residual tSNR
#         std = np.sqrt(ss_full / len(y))
#         tsnr = np.squeeze(ybar) / std
#         tsnr = np.nan_to_num(tsnr)
#         self.save_image(tsnr, "tsnr")
#
#         return runtime
#
#     def save_image(self, data, fname):
#         """Save data to the output structure."""
#         img = nib.Nifti1Image(data, self.affine, self.header)
#         img.to_filename(fname + ".nii.gz")
#
#     def dot_by_slice(self, X, pes, component=None):
#         """Broadcast a dot product by image slices to balance speed/memory."""
#         if component is not None:
#             pes = pes * getattr(X, component + "_vector").T[np.newaxis,
#                                                             np.newaxis, :, :]
#         # Set up the output data structure
#         n_x, n_y, n_z, n_pe = pes.shape
#         n_t = X.design_matrix.shape[0]
#         out = np.empty((n_x, n_y, n_z, n_t))
#
#         # Do the dot product, broadcasted for each Z slice
#         for k in range(n_z):
#             slice_pe = pes[:, :, k, :].reshape(-1, n_pe).T
#             slice_dot = X.design_matrix.values.dot(slice_pe)
#             out[:, :, k, :] = slice_dot.T.reshape(n_x, n_y, n_t)
#
#         return out
#
#     def compute_r2(self, yhat):
#
#         ssres = np.sum(np.square(yhat - self.y), axis=-1)
#         r2 = 1 - ssres / self.sstot
#         return ssres, r2
#
#     def _list_outputs(self):
#
#         outputs = self._outputs().get()
#
#         outputs["r2_files"] = [op.abspath("r2_full.nii.gz"),
#                                op.abspath("r2_main.nii.gz"),
#                                op.abspath("r2_confound.nii.gz")]
#         outputs["ss_files"] = [op.abspath("sstot.nii.gz"),
#                                op.abspath("ssres_full.nii.gz"),
#                                op.abspath("ssres_main.nii.gz")]
#         outputs["tsnr_file"] = op.abspath("tsnr.nii.gz")
#
#         return outputs
#
#
# class ModelReportInput(BaseInterfaceInputSpec):
#
#     timeseries = File(exists=True)
#     sigmasquareds_file = File(exists=True)
#     tsnr_file = File(exists=True)
#     zstat_files = InputMultiPath(File(exists=True))
#     r2_files = InputMultiPath(File(exists=True))
#
#
# class ModelReport(BaseInterface):
#
#     input_spec = ModelReportInput
#     output_spec = ManyOutFiles
#
#     def _run_interface(self, runtime):
#
#         # Load the sigmasquareds and use it to infer the model mask
#         var_img = nib.load(self.inputs.sigmasquareds_file).get_data()
#         self.mask = (var_img > 0).astype(np.int16)
#
#         # Load the timeseries and take the mean over time for a background
#         ts_img = nib.load(self.inputs.timeseries)
#         self.mean = nib.Nifti1Image(ts_img.get_data().mean(axis=-1),
#                                     ts_img.get_affine(),
#                                     ts_img.get_header())
#
#         # Set up the output list
#         self.out_files = []
#
#         # Plot the data
#         self.plot_residuals()
#         self.plot_rsquareds()
#         self.plot_tsnr()
#         if isdefined(self.inputs.zstat_files):
#             self.plot_zstats()
#
#         return runtime
#
#     def plot_residuals(self):
#         """Plot the variance of the model residuals across time."""
#         ss = self.inputs.sigmasquareds_file
#         m = Mosaic(self.mean, ss, self.mask, step=1)
#         m.plot_overlay("cube:.8:.2", 0, alpha=.6, fmt="%d")
#         png_name = nii_to_png(ss)
#         m.savefig(png_name)
#         m.close()
#         self.out_files.append(png_name)
#
#     def plot_tsnr(self):
#
#         tsnr = self.inputs.tsnr_file
#         m = Mosaic(self.mean, tsnr, self.mask, step=1)
#         m.plot_overlay("cube:1.9:.5", 0, alpha=1, fmt="%d")
#         png_name = nii_to_png(tsnr)
#         m.savefig(png_name)
#         m.close()
#         self.out_files.append(png_name)
#
#     def plot_rsquareds(self):
#         """Plot the full, main, and confound R squared maps."""
#         cmaps = ["cube:2:0", "cube:2.6:0", "cube:1.5:0"]
#         for r2_file, cmap in zip(self.inputs.r2_files, cmaps):
#             m = Mosaic(self.mean, r2_file, self.mask, step=1)
#             m.plot_overlay(cmap, 0, alpha=.6)
#             png_name = nii_to_png(r2_file)
#             m.savefig(png_name)
#             m.close()
#             self.out_files.append(png_name)
#
#     def plot_zstats(self):
#         """Plot the positive and negative z stats with a low threshold."""
#         for z_file in self.inputs.zstat_files:
#             m = Mosaic(self.mean, z_file, self.mask, step=1)
#             m.plot_activation(pos_cmap="Reds_r", neg_cmap="Blues",
#                               thresh=1.7, alpha=.85)
#             png_name = nii_to_png(z_file)
#             m.savefig(png_name)
#             m.close()
#             self.out_files.append(png_name)
#
#     def _list_outputs(self):
#
#         outputs = self._outputs().get()
#         outputs["out_files"] = self.out_files
#         return outputs
#
