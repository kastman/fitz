#!/usr/bin/env python
# Create Lyman/Fitz style long flat Design Files from plain-text onset files
# EKK / June 2015
# Python 2/3 compatibile, depends on Pandas and Numpy/Scipy

from __future__ import print_function
from pandas import concat, read_csv
from argparse import ArgumentParser, FileType
import re
from scipy.io import savemat
from numpy import empty


def main(args):
    runs_df = load_onsets(args.onsets_files, args)

    if len(args.conditions):
        conditions = args.conditions
    else:
        conditions = runs_df['condition'].unique()

    print(runs_df)

    runs_df.to_csv(args.out, index=False)

    exit()

    # for r, run_df in runs_df.groupby('run'):
    #     if args.verbose >= 1:
    #         print(r, run_df)
    #     infolist = []
    #     for cond in conditions:
    #         onsets = onsets_for(cond, run_df)
    #         if onsets:  # Don't append 0-length onsets
    #             infolist.append(onsets)
    #     if args.verbose >= 2:
    #         print(infolist)
    #
    #     outfile = args.prefix + 'run%d.mat' % int(r)
    #     scipy_onsets = _lists_to_scipy(infolist)
    #     savemat(outfile, scipy_onsets, oned_as='row')
    #     print('Saved %s' % outfile)


def load_onsets(onsets_files, args):
    """Read onsets file and add metadata from their filenames.
    Return one concatenated pandas dataframe with all trials as rows."""
    runs = []
    # pat = re.compile('(?P<condition>\w+)\.run(?P<run>\d{3})')
    for i, fid in enumerate(onsets_files):
        cols = ['run', 'onset', 'duration', 'condition']

        run = read_csv(fid)

        # Cleanup any columns that might exist if we don't want them
        if args.drop_cols:
            for col in cols:
                if col in run.columns:
                    run.drop(col, axis=1, inplace=True)

        # run = read_table(fid, names=['onset', 'duration', 'amplitude'])

        # runinfo = pat.search(fid.name).groupdict()
        # print(run)
        # print(run.columns)
        run['filename'] = fid.name

        columns = {}

        columns[args.onset_col] = 'onset'

        if args.run_col:
            columns[args.run_col] = 'run'
        else:
            run['run'] = i + 1

        columns[args.condition_col] = 'condition'

        if args.duration_col:
            columns[args.duration_col] = 'duration'
        else:
            run['duration'] = 0

        if len(args.pmods_col):
            for pmod in args.pmods_col:
                columns[pmod] = 'pmod-' + pmod
                cols.append('pmod-' + pmod)

        print(columns)
        print(run.columns)
        print(len(run.columns))

        run.rename(columns=columns, inplace=True)

        runs.append(run[cols][run['condition'].notnull()])

    print(runs)

    return concat(runs, ignore_index=True)


def onsets_for(cond, run_df):
    """
    Inputs:
      * Condition Label to grab onsets, durations & amplitudes for.
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

        if 'amplitude' in cond_df.columns and cond_df['amplitude'].notnull().any():
            pmods = [dict(
                name=args.pmod_name,
                poly=1,
                param=cond_df['amplitude'].tolist(),
            )]
            condinfo['pmod'] = pmods
    else:
        condinfo = None
    return condinfo


def _lists_to_scipy(onsets_list):
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
            pmod_names = empty((current_condition_n_pmods,), dtype='object')
            pmod_param = empty((current_condition_n_pmods,), dtype='object')
            pmod_poly  = empty((current_condition_n_pmods,), dtype='object')

            for pmod_i, val in enumerate(cond_pmod_list):
                pmod_names[pmod_i] = val['name']
                pmod_param[pmod_i] = val['param']
                pmod_poly[pmod_i]  = float(val['poly'])

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


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('onsets_files', type=FileType('r'),
                        help='List of FSL EV onsets to convert', nargs='+')
    parser.add_argument('--out',   '-o', default='onsets_',
                        help='Output filename.')
    parser.add_argument('--verbose',      '-v', action="count",
                        help="increase output verbosity")
    parser.add_argument('--pmod-name', default='pmod',
                        help='Name to use when writing FSL Amplitude as SPM '
                             'parametric modulator')
    parser.add_argument('--conditions', '-c', default=[], nargs='+')
    parser.add_argument('--condition-col')
    parser.add_argument('--duration-col')
    parser.add_argument('--onset-col', default='')
    parser.add_argument('--pmods-col', default=[], nargs="*")
    parser.add_argument('--run-col')
    parser.add_argument('--drop-cols', help='Should we drop pre-named columns',
                        default=True)
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    print(args)
    if args.verbose >= 2:
        print(args)
    main(args)
