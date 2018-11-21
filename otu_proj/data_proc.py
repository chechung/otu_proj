#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
data_proc.py
Process OTU data to generate phylogenetic abundance group bar plot

General steps:
    1. separate values based on control/treatment category
    2. calculate mean and standard deviation values for phylogenetic groups per control/treatment group
    3. generate group bar plot comparing average abundance values between control/treatment groups
       for each phylogenetic group

Outputs:
    - filename_processed_.xlsx: excel file processed data with the following sheets:
        1. data: relative abundance values for phylogenetic groups that were detected in at least one sample
        2. control: subset of data for control group, as well as the mean and standard deviation values
        3. low: subset of data for low treatment group, as well as the mean and standard deviation values
        4. medium: subset of data for medium treatment group, as well as the mean and standard deviation values
        5. high: subset of data for high treatment group, as well as the mean and standard deviation values
    - filename.png: image file that compares relative abundance between control treatment groups for each
                    phylogenetic group
"""

import sys
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import os

SUCCESS = 0
IO_ERROR = 2

DEF_DATA_FILE = 'data/OTU_data.xlsx'
DEF_FIG_DIM = (20, 10)
DEF_FONT_SIZE = 15
DEF_GRID_BOOL = True


def warning(*objs):
    """Writes a message to stderr."""
    print("WARNING: ", *objs, file=sys.stderr)


def data_process_analysis(data_frame, fname):
    """
    Processing steps:
    1. Remove phylogenetic groups absent in all samples
    2. Separate data into control or treatment groups
    3. Attain mean and standard deviation values for each phylogenetic group in each group
    4. Transfer processed data with mean and standard deviation values onto output excel file

    Parameters
    ----------
    data_frame: pandas dataframe of OTU file
    fname: name for output xlsx file (taken from input data)

    Returns
    -------
    means_df: dataframe of mean values where row index corresponds to control/treatment group and
              column index corresponds to phylogenetic group
    sd_df: dataframe of standard deviation values where row index corresponds to control/treatment group and
           column index corresponds to phylogenetic group
    """

    data_frame = data_frame.loc[:, (data_frame != 0).any(axis=0)]
    control_vals = []
    low_vals = []
    med_vals = []
    high_vals = []
    for i in range(0, data_frame.shape[0]):
        for j in range(0, data_frame.shape[1]):
            if 'control' in data_frame.index[i]:
                control_vals += [data_frame.index[i]]
            elif 'low' in data_frame.index[i] and 'treated' in data_frame.index[i]:
                low_vals += [data_frame.index[i]]
            elif 'medium' in data_frame.index[i] and 'treated' in data_frame.index[i]:
                med_vals += [data_frame.index[i]]
            elif 'high' in data_frame.index[i] and 'treated' in data_frame.index[i]:
                high_vals += [data_frame.index[i]]
    groups = {'control': set(control_vals), 'low': set(low_vals), 'medium': set(med_vals), 'high': set(high_vals)}
    groups_list = list(groups)

    # calculate average and SD values for each group and add to excel file as individual worksheets
    output = fname + '_processed.xlsx'
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    data_frame.to_excel(writer, sheet_name='data')
    means_df = pd.DataFrame(columns=list(data_frame))
    sd_df = pd.DataFrame(columns=list(data_frame))
    for i in range(0, len(groups)):
        label = groups_list[i]
        x = data_frame.loc[groups[label]]
        x.loc['Mean'] = x.mean(axis=0)
        x.loc['SD'] = x.std(axis=0)
        x.to_excel(writer, label)
        means_df.loc['{}'.format(label)] = x.loc['Mean']
        sd_df.loc['{}'.format(label)] = x.loc['SD']
    writer.save()
    print("Wrote file: {}".format(output))
    return means_df, sd_df


def plot_data(mean_values, sd_values, fig_dim, font_size, grid_bool, fname):
    """
    Generate group bar plot showing mean relative abundance of each phylogenetic group with error bars

    Parameters
    ----------
    mean_values: dataframe of mean values generated from data_process_analysis
    sd_values: dataframe of standard deviation values generated from data_process_analysis
    fig_dim: tuple of integer values specifying figure dimension; (horizontal_length, vertical_length)
             (DEFAULT=(20, 10))
    font_size: integer value specifying font_size for axis, tick, and legend labels (DEFAULT=15)
    grid_bool: boolean value that determines whether to include grid lines in figure (DEFAULT=True)
    fname: name for png file (taken from input data)

    Returns
    -------
    saves a png file of group bar plot
    """
    output = fname + '.png'
    mean_values = mean_values.T
    ax = mean_values.plot.bar(figsize=fig_dim, width=0.5, yerr=sd_values.T)
    ax.set_xlabel("Phylogenetic Group", fontsize=font_size)
    ax.set_ylabel("Relative Abundance", fontsize=font_size)
    ax.set_xticklabels(mean_values.index)
    plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right')
    plt.xticks(size=font_size)
    plt.yticks(size=font_size)
    plt.legend(prop={'size': font_size})
    plt.grid(grid_bool)
    plt.savefig(output, bbox_inches="tight")
    print("Wrote file: {}".format(output))


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--xlsx_data_file", help="The location of xlsx file of OTU data.",
                        default=DEF_DATA_FILE)
    parser.add_argument("-f", "--fig_dim", help="Figure dimension for group bar plot (integer tuple).",
                        default=DEF_FIG_DIM)
    parser.add_argument("-s", "--font_size", help="Font size for axis, tick, and legend labels (integer value).",
                        default=DEF_FONT_SIZE)
    parser.add_argument("-g", "--grid_bool", help="To include grid lines or not (boolean value).",
                        default=DEF_GRID_BOOL)
    args = None
    try:
        args = parser.parse_args(argv)
        args.xlsx_data = pd.read_excel(args.xlsx_data_file, index_col=0)
    except IOError as e:
        warning("Problems reading file:", e)
        parser.print_help()
        return args, IO_ERROR

    return args, SUCCESS


def main(argv=None):
    args, ret = parse_cmdline(argv)
    if ret != SUCCESS:
        return ret
    data_fname = os.path.basename(args.xlsx_data_file)
    fname = os.path.splitext(data_fname)[0]
    means_df, sd_df = data_process_analysis(args.xlsx_data, fname)
    plot_data(means_df, sd_df, args.fig_dim, args.font_size, args.grid_bool, fname)
    return SUCCESS  # success


if __name__ == "__main__":
    status = main()
    sys.exit(status)
