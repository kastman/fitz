"""Make SPM *.mat onset files using csv design"""
# import re
import os.path as op
# import numpy as np
# from scipy import stats, signal
import pandas as pd
from scipy.io import savemat
from numpy import empty
# import nibabel as nib
# import matplotlib.pyplot as plt
# from moss import glm
# from moss.mosaic import Mosaic
# import seaborn as sns

from nipype import Node, Workflow, IdentityInterface
# from nipype.interfaces import fsl
from nipype.interfaces.base import (BaseInterface,
                                    BaseInterfaceInputSpec,
                                    # InputMultiPath,
                                    OutputMultiPath,
                                    TraitedSpec, File, traits,
                                    # isdefined
                                    )
import fitz
# from fitz.tools import ManyOutFiles, SaveParameters, nii_to_png


def create_onset_workflow(name="onset", exp_info=None):
    # Default experiment parameters
    if exp_info is None:
        exp_info = fitz.default_experiment_parameters()

    # Define constant inputs
    inputs = ["design_file"]

    # Define the workflow inputs
    inputnode = Node(IdentityInterface(inputs), "inputs")

    onsetsetup = Node(OnsetSetup(), "onsetsetup")
    onsetsetup.inputs.exp_info = exp_info

    # Define the workflow outputs
    outputnode = Node(IdentityInterface(["design_mats"]),
                      "outputs")

    # Define the workflow and connect the nodes
    onsetFlow = Workflow(name=name)
    onsetFlow.connect([
        (inputnode, onsetsetup,
            [("design_file", "design_file")]),
        (onsetsetup, outputnode,
            [("design_mats", "design_mats")])
    ])

    return onsetFlow, inputnode, outputnode

# =========================================================================== #


class OnsetSetupInput(BaseInterfaceInputSpec):

    exp_info = traits.Dict()
    design_file = File(exists=True)
    # design_file = File(exists=True)
    # realign_file = File(exists=True)
    # artifact_file = File(exists=True)
    # regressor_file = File(exists=True)


class OnsetSetupOutput(TraitedSpec):

    design_mats = OutputMultiPath(File(exists=True))
    # contrast_file = File(exists=True)
    # design_matrix_pkl = File(exists=True)
    # report = OutputMultiPath(File(exists=True))


class OnsetSetup(BaseInterface):

    input_spec = OnsetSetupInput
    output_spec = OnsetSetupOutput

    def _run_interface(self, runtime):
        self._exp_info = self.inputs.exp_info
        self.design_mats = self._mats_from_csv(self.inputs.design_file)

        return runtime

        # # Get all the information for the design
        # design_kwargs = self.build_design_information()
        #
        # # Initialize the design matrix object
        # X = glm.DesignMatrix(**design_kwargs)
        #
        # # Report on the design
        # self.design_report(self.inputs.exp_info, X, design_kwargs)
        #
        # # Write out the design object as a pkl to pass to the report function
        # X.to_pickle("design.pkl")
        #
        # # Finally, write out the design files in FSL format
        # X.to_fsl_files("design", self.inputs.exp_info["contrasts"])
        #
        # return runtime

    def _mats_from_csv(self, design_file):
        runs_df = pd.read_csv(design_file)
        if len(self._exp_info.get('conditions', [])):
            conditions = self._exp_info['conditions']
        else:
            conditions = runs_df['condition'].unique()

        outfiles = []
        for r, run_df in runs_df.groupby('run'):
            infolist = []
            for cond in conditions:
                onsets = self.onsets_for(cond, run_df)
                if onsets:  # Don't append 0-length onsets
                    infolist.append(onsets)
            outfile = self._exp_info["design_name"] + '_run%d.mat' % int(r)
            scipy_onsets = self._lists_to_scipy(infolist)
            savemat(outfile, scipy_onsets, oned_as='row')
            outfiles.append(op.abspath(outfile))
        return outfiles

    def onsets_for(self, cond, run_df):
        """
        Inputs:
          * Condition Label to grab onsets, durations & amplitudes / values.
          * Pandas Dataframe for current run containing onsets values as columns.

        Outputs:
          * Returns a dictionary of extracted values for onsets, durations, etc.
          * Returns None if there are no onsets.
        """
        condinfo = {}
        cond_df = run_df[run_df['condition'] == cond]

        if cond_df['onset'].notnull().any():  # Onsets Present
            if cond_df['duration'].notnull().any():
                durations = cond_df['duration'].tolist()
            else:
                durations = [0]

            condinfo = dict(
                name=cond,
                durations=durations,
                onsets=cond_df['onset'].tolist(),
            )

            if (('value' in cond_df.columns) and
                    (cond_df['value'].notnull().any()) and
                    (len(cond_df['value'].unique()) > 1)):
                pmods = [dict(
                    name=self._exp_info.get('pmod_name', 'pmod'),
                    poly=1,
                    param=cond_df['value'].tolist(),
                )]
                condinfo['pmod'] = pmods
        else:
            condinfo = None
        return condinfo

    def _lists_to_scipy(self, onsets_list):
        """
        Inputs:
          * List of dicts (one dict for each condition)

            [{'name':'Low','durations':0,'onsets':[1,3,5]},
             {'name':'Hi', 'durations':0, 'onsets':[2,4,6]}]

            - Or with Parametric Modulators -
            [{'name':'Low','durations':0,'onsets':[1,3,5], 'pmod':[
               {'name': 'RT', 'poly':1, 'param':[42,13,666]}]},
             {'name':'High',, 'durations':0, 'onsets':[2,4,6]}]

        Outputs:
          * Dict of scipy arrays for keys names, durations and onsets
            that can be written using scipy.io.savemat
        """

        conditions_n = len(onsets_list)
        names = empty((conditions_n,),     dtype='object')
        durations = empty((conditions_n,), dtype='object')
        onsets = empty((conditions_n,),    dtype='object')

        pmoddt = [('name', 'O'), ('poly', 'O'), ('param', 'O')]
        pmods = empty((conditions_n),      dtype=pmoddt)
        has_pmods = False

        for i, ons in enumerate(onsets_list):
            names[i] = ons['name']
            durations[i] = ons['durations']
            onsets[i] = ons['onsets']
            if 'pmod' not in ons.keys():
                pmods[i]['name'], pmods[i]['poly'], pmods[i]['param'] = [], [], []
            else:
                # 'pmod': [{'name':'rt','poly':1,'param':[1,2,3]}]
                # Multiple pmods per condition are allowed, so pmod
                # is a list of dicts.
                has_pmods = True
                cond_pmod_list = ons['pmod']
                current_condition_n_pmods = len(cond_pmod_list)
                pmod_names = empty((current_condition_n_pmods,), dtype=object)
                pmod_param = empty((current_condition_n_pmods,), dtype=object)
                pmod_poly = empty((current_condition_n_pmods,), dtype=object)

                for pmod_i, val in enumerate(cond_pmod_list):
                    pmod_names[pmod_i] = val['name']
                    pmod_param[pmod_i] = val['param']
                    pmod_poly[pmod_i] = val['poly']

                pmods[i]['name'] = pmod_names
                pmods[i]['poly'] = pmod_poly
                pmods[i]['param'] = pmod_param

        scipy_onsets = dict(
            names=names,
            durations=durations,
            onsets=onsets
        )

        if has_pmods:
            scipy_onsets['pmod'] = pmods

        return scipy_onsets


    # def build_design_information(self):

        # # Load in the design information
        # exp_info = self.inputs.exp_info
        # tr = self.inputs.exp_info["TR"]
        #
        # # Derive the length of the scan and run number from the timeseries
        # ntp = nib.load(self.inputs.timeseries).shape[-1]
        # run = int(re.search("run_(\d+)", self.inputs.timeseries).group(1))
        #
        # # Get the experimental design
        # if isdefined(self.inputs.design_file):
        #     design = pd.read_csv(self.inputs.design_file)
        #     design = design[design["run"] == run]
        # else:
        #     design = None
        #
        # # Get the motion correction parameters
        # realign = pd.read_csv(self.inputs.realign_file)
        # realign = realign.filter(regex="rot|trans").apply(stats.zscore)
        #
        # # Get the image artifacts
        # artifacts = pd.read_csv(self.inputs.artifact_file).max(axis=1)
        #
        # # Get the additional model regressors
        # if isdefined(self.inputs.regressor_file):
        #     regressors = pd.read_csv(self.inputs.regressor_file)
        #     regressors = regressors[regressors["run"] == run]
        #     regressors = regressors.drop("run", axis=1)
        #     if exp_info["regressor_names"] is not None:
        #         regressors = regressors[exp_info["regressor_names"]]
        #     regressors.index = np.arange(ntp) * tr
        # else:
        #     regressors = None
        #
        # # Set up the HRF model
        # hrf = getattr(glm, exp_info["hrf_model"])
        # hrf = hrf(exp_info["temporal_deriv"], tr, **exp_info["hrf_params"])
        #
        # # Build a dict of keyword arguments for the design matrix
        # design_kwargs = dict(design=design,
        #                      hrf_model=hrf,
        #                      ntp=ntp,
        #                      tr=tr,
        #                      confounds=realign,
        #                      artifacts=artifacts,
        #                      regressors=regressors,
        #                      condition_names=exp_info["condition_names"],
        #                      confound_pca=exp_info["confound_pca"],
        #                      hpf_cutoff=exp_info["hpf_cutoff"])
        #
        # return design_kwargs

    # def design_report(self, exp_info, X, design_kwargs):
    #     """Generate static images summarizing the design."""
    #     # Plot the design itself
    #     design_png = op.abspath("design.png")
    #     X.plot(fname=design_png, close=True)
    #
    #     with sns.axes_style("whitegrid"):
    #         # Plot the eigenvalue spectrum
    #         svd_png = op.abspath("design_singular_values.png")
    #         X.plot_singular_values(fname=svd_png, close=True)
    #
    #         # Plot the correlations between design elements and confounds
    #         corr_png = op.abspath("design_correlation.png")
    #         if design_kwargs["design"] is None:
    #             with open(corr_png, "wb"):
    #                 pass
    #         else:
    #             X.plot_confound_correlation(fname=corr_png, close=True)
    #
    #     # Build a list of images sumarrizing the model
    #     report = [design_png, corr_png, svd_png]
    #
    #     # Now plot the information loss from the high-pass filter
    #     design_kwargs["hpf_cutoff"] = None
    #     X_unfiltered = glm.DesignMatrix(**design_kwargs)
    #     tr = design_kwargs["tr"]
    #     ntp = design_kwargs["ntp"]
    #
    #     # Plot for each contrast
    #     for i, (name, cols, weights) in enumerate(exp_info["contrasts"], 1):
    #
    #         # Compute the contrast predictors
    #         C = X.contrast_vector(cols, weights)
    #         y_filt = X.design_matrix.dot(C)
    #         y_unfilt = X_unfiltered.design_matrix.dot(C)
    #
    #         # Compute the spectral density for filtered and unfiltered
    #         fs, pxx_filt = signal.welch(y_filt, 1. / tr, nperseg=ntp)
    #         fs, pxx_unfilt = signal.welch(y_unfilt, 1. / tr, nperseg=ntp)
    #
    #         # Draw the spectral density
    #         with sns.axes_style("whitegrid"):
    #             f, ax = plt.subplots(figsize=(9, 3))
    #         ax.fill_between(fs, pxx_unfilt, color="#C41E3A")
    #         ax.axvline(1.0 / exp_info["hpf_cutoff"], c=".3", ls=":", lw=1.5)
    #         ax.fill_between(fs, pxx_filt, color=".5")
    #
    #         # Label the plot
    #         ax.set(xlabel="Frequency",
    #                ylabel="Spectral Density",
    #                xlim=(0, .15))
    #         plt.tight_layout()
    #
    #         # Save the plot
    #         fname = op.abspath("cope%d_filter.png" % i)
    #         f.savefig(fname, dpi=100)
    #         plt.close(f)
    #         report.append(fname)
    #
    #     # Store the report files for later
    #     self.report_files = report

    def _list_outputs(self):

        outputs = self._outputs().get()
        outputs["design_mats"] = self.design_mats
        # outputs["contrast_file"] = op.abspath("design.con")
        # outputs["design_matrix_pkl"] = op.abspath("design.pkl")
        # outputs["design_matrix_file"] = op.abspath("design.mat")
        return outputs
