import argparse
import glob
import os.path
import re
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit
import pandas as pd
import matplotlib.pyplot as plt

RES_STORAGE = '../results'

CASE_NAME = 'Case Name'
CORES = 'Cores'
MSH_QUAL = 'Mesh Quality'
PHYNGS_TYPE = 'Phyngs Type'
PHYNGS_NUM = 'Phyngs Amount'
SETUP_TIME = 'Setup Time, ms'
SOLVE_TIME = 'Solving Time, ms'
ERROR = 'Error'
DF_COLUMNS = [
    CORES,
    MSH_QUAL,
    PHYNGS_TYPE,
    PHYNGS_NUM,
    SETUP_TIME,
    SOLVE_TIME,
    ERROR,
]

PHYNG_TYPES = ['heaters', 'acs', 'doors', 'windows']

MESH_QUALITY_K = 'Mesh Quality, %'
NUM_OF_CORES_K = 'Num of Cores'
NUM_OF_PHYNGS_K = 'Num of Phyngs'
AVG_SETUP_TIME_K = 'Average Setup Time, s'
AVG_SOLVE_TIME_K = 'Average Solving Time, s'
SETUP_TIME_K = 'Setup Time, s'
SOLVE_TIME_K = 'Solving Time, s'
WHISKER_K = 'whisker'
TITLE_K = 'title'
SETUP_K = 'setup'
SOLVE_K = 'solving'
TITLE_SETUP_K = f'{TITLE_K} {SETUP_K}'
TITLE_SOLVE_K = f'{TITLE_K} {SOLVE_K}'


def func_exp(x, a, b, c):
    return a * np.exp(np.multiply(x, -b)) + c


def func_log(x, a, b):
    return a + b * np.log(x)


def func_power(x, a, b):
    return a * np.power(x, -b)


def func1(x, a, b):
    return np.multiply(x, a) + b


def func2(x, a, b, c):
    return a * np.power(x, 2) + np.multiply(x, b) + c


def func3(x, a, b, c, d):
    return a * np.power(x, 3) + b * np.power(x, 2) + np.multiply(x, c) + d


def func4(x, a, b, c, d, e):
    return a * np.power(x, 4) + b * np.power(x, 3) + c * np.power(x, 2) + np.multiply(x, d) + e


def func5(x, a, b, c, d, e, f):
    return a * np.power(x, 5) + b * np.power(x, 4) + c * np.power(x, 3) + d * np.power(x, 2) + np.multiply(x, e) + f


def get_fit_title(func):
    if func == func_exp:
        return 'exp fit'
    elif func == func_log:
        return 'logarithmic fit'
    elif func == func_power:
        return 'power fit'
    elif func == func1:
        return 'linear fit'
    elif func == func2:
        return 'quadratic fit'
    elif func == func3:
        return 'cubic fit'
    elif func == func4:
        return 'quartic fit'
    elif func == func5:
        return 'quintic fit'


def form_phyng_df_dict(df: pd.DataFrame):
    phyngs_df = {}
    for phyng_type in PHYNG_TYPES:
        phyng_df = df.loc[df[PHYNGS_TYPE] == phyng_type]
        if not phyng_df.empty:
            phyngs_df[phyng_type] = phyng_df
    return phyngs_df


def get_data_for_timing(result: dict, df: pd.DataFrame):
    # For Whisker plot
    setup_times = df[SETUP_TIME].values / 1000
    solve_times = df[SOLVE_TIME].values / 1000
    result[SETUP_TIME_K].append(setup_times)
    result[SOLVE_TIME_K].append(solve_times)
    result[WHISKER_K] = setup_times.shape[0] > 1

    # For regular averaged plot
    result[AVG_SETUP_TIME_K].append(np.average(setup_times))
    result[AVG_SOLVE_TIME_K].append(np.average(solve_times))


def get_phyngs_data(df: pd.DataFrame) -> dict:
    # Get only the best mesh and the most cores
    mesh_quality = max(df[MSH_QUAL])
    best_df = df.loc[df[MSH_QUAL] == mesh_quality]
    cores = max(best_df[CORES])
    best_df = best_df.loc[best_df[CORES] == cores]

    # Separate DFs according to phyng types
    phyngs_df = form_phyng_df_dict(best_df)

    phyng_results = {}

    # Iterate through each phyng type and DFs
    for phyng_type, phyng_df in phyngs_df.items():
        phyng_amounts = sorted(set(phyng_df[PHYNGS_NUM].values))
        phyng_results[phyng_type] = {
            TITLE_SETUP_K: f'{phyng_type.capitalize()} {SETUP_K} - {mesh_quality} % mesh quality, {cores} cores',
            TITLE_SOLVE_K: f'{phyng_type.capitalize()} {SOLVE_K} - {mesh_quality} % mesh quality, {cores} cores',
            NUM_OF_PHYNGS_K: [],
            AVG_SETUP_TIME_K: [],
            AVG_SOLVE_TIME_K: [],
            SETUP_TIME_K: [],
            SOLVE_TIME_K: [],
        }
        # Iterate through each amount of phyngs
        for amount in phyng_amounts:
            phyng_amount_df = phyng_df.loc[phyng_df[PHYNGS_NUM] == amount]
            phyng_results[phyng_type][NUM_OF_PHYNGS_K].append(amount)

            get_data_for_timing(phyng_results[phyng_type], phyng_amount_df)

    return phyng_results


def get_mesh_data(df: pd.DataFrame) -> dict:
    # Get only the most cores
    cores = max(df[CORES])
    best_df = df.loc[df[CORES] == cores]

    # Separate DFs according to phyng types
    phyngs_df = form_phyng_df_dict(best_df)

    mesh_results = {}

    # Iterate through each phyng type and DFs
    for phyng_type, phyng_df in phyngs_df.items():
        max_phyngs = max(phyng_df[PHYNGS_NUM])
        mesh_qualities = sorted(set(phyng_df[MSH_QUAL].values))
        mesh_results[phyng_type] = {
            TITLE_SETUP_K: f'{max_phyngs} {phyng_type} {SETUP_K} - {cores} cores',
            TITLE_SOLVE_K: f'{max_phyngs} {phyng_type} {SOLVE_K} - {cores} cores',
            MESH_QUALITY_K: [],
            AVG_SETUP_TIME_K: [],
            AVG_SOLVE_TIME_K: [],
            SETUP_TIME_K: [],
            SOLVE_TIME_K: [],
        }
        max_phyngs_df = phyng_df.loc[phyng_df[PHYNGS_NUM] == max_phyngs]
        # Iterate through each mesh quality
        for mesh_quality in mesh_qualities:
            mesh_quality_df = max_phyngs_df.loc[max_phyngs_df[MSH_QUAL] == mesh_quality]
            mesh_results[phyng_type][MESH_QUALITY_K].append(mesh_quality)

            get_data_for_timing(mesh_results[phyng_type], mesh_quality_df)

    return mesh_results


def get_cores_data(df: pd.DataFrame) -> dict:
    # Get only the most cores
    mesh_quality = max(df[MSH_QUAL])
    best_df = df.loc[df[MSH_QUAL] == mesh_quality]

    # Separate DFs according to phyng types
    phyngs_df = form_phyng_df_dict(best_df)

    cores_result = {}

    # Iterate through each phyng type and DFs
    for phyng_type, phyng_df in phyngs_df.items():
        max_phyngs = max(phyng_df[PHYNGS_NUM])
        cores = sorted(set(phyng_df[CORES].values))
        cores_result[phyng_type] = {
            TITLE_SETUP_K: f'{max_phyngs} {phyng_type} {SETUP_K} - {mesh_quality} % mesh quality',
            TITLE_SOLVE_K: f'{max_phyngs} {phyng_type} {SOLVE_K} - {mesh_quality} % mesh quality',
            NUM_OF_CORES_K: [],
            AVG_SETUP_TIME_K: [],
            AVG_SOLVE_TIME_K: [],
            SETUP_TIME_K: [],
            SOLVE_TIME_K: [],
        }
        max_phyngs_df = phyng_df.loc[phyng_df[PHYNGS_NUM] == max_phyngs]
        # Iterate through each core
        for core in cores:
            core_df = max_phyngs_df.loc[max_phyngs_df[CORES] == core]
            cores_result[phyng_type][NUM_OF_CORES_K].append(core)

            get_data_for_timing(cores_result[phyng_type], core_df)

    return cores_result


def draw_lines_plot(x, y, xlabel='', ylabel='', title='',
                    xspan=None, yspan=None, fit=True, fit_func=func3):
    fig, ax = plt.subplots()
    l1, = ax.plot(x, y)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if xspan:
        ax.axvspan(xspan[0], xspan[1], alpha=0.5, color='red')
        ax.set_xlim([xspan[0], None])
    if yspan:
        ax.axhspan(yspan[0], yspan[1], alpha=0.5, color='red')
        ax.set_ylim([None, yspan[1]])
    if fit:
        popt, pcov = curve_fit(fit_func, x, y)
        x_fit = np.linspace(x[0], x[-1], 50)
        l2, = ax.plot(x_fit, fit_func(x_fit, *popt), color='orange', alpha=0.5)
        ax.legend([l1, l2], ['original', get_fit_title(fit_func)])
    Path(f'{RES_STORAGE}/pdfs').mkdir(exist_ok=True)
    Path(f'{RES_STORAGE}/pngs').mkdir(exist_ok=True)
    plt.savefig(f'{RES_STORAGE}/pdfs/{title}.pdf')
    plt.savefig(f'{RES_STORAGE}/pngs/{title}.png')
    # plt.show()
    plt.close()


def plot_time_vs_phyngs(df: pd.DataFrame):
    phyng_results = get_phyngs_data(df)
    for res in phyng_results.values():
        draw_lines_plot(res[NUM_OF_PHYNGS_K], res[AVG_SETUP_TIME_K],
                        NUM_OF_PHYNGS_K, AVG_SETUP_TIME_K, res[TITLE_SETUP_K])
        yspan = None
        max_span = max(res[AVG_SOLVE_TIME_K]) + 10000
        if max_span > 60000:
            yspan = [60000, max_span]
        draw_lines_plot(res[NUM_OF_PHYNGS_K], res[AVG_SOLVE_TIME_K],
                        NUM_OF_PHYNGS_K, AVG_SOLVE_TIME_K, res[TITLE_SOLVE_K],
                        yspan=yspan)


def plot_time_vs_mesh_quality(df: pd.DataFrame):
    mesh_results = get_mesh_data(df)
    xspan = [40, 50]
    for res in mesh_results.values():
        draw_lines_plot(res[MESH_QUALITY_K], res[AVG_SETUP_TIME_K],
                        MESH_QUALITY_K, AVG_SETUP_TIME_K, res[TITLE_SETUP_K],
                        xspan=xspan, fit_func=func5)
        yspan = None
        max_span = max(res[AVG_SOLVE_TIME_K]) + 10
        if max_span > 60:
            yspan = [60, max_span]
        draw_lines_plot(res[MESH_QUALITY_K], res[AVG_SOLVE_TIME_K],
                        MESH_QUALITY_K, AVG_SOLVE_TIME_K, res[TITLE_SOLVE_K],
                        xspan=xspan, yspan=yspan, fit_func=func5)


def plot_time_vs_cores(df: pd.DataFrame):
    cores_result = get_cores_data(df)
    for res in cores_result.values():
        yspan = None
        max_span = max(res[AVG_SOLVE_TIME_K]) + 10000
        if max_span > 60000:
            yspan = [60000, max_span]
        draw_lines_plot(res[NUM_OF_CORES_K], res[AVG_SOLVE_TIME_K],
                        NUM_OF_CORES_K, AVG_SOLVE_TIME_K, res[TITLE_SOLVE_K],
                        yspan=yspan, fit_func=func_power)


def plot_time_vs_all(df: pd.DataFrame):
    plot_time_vs_phyngs(df)
    plot_time_vs_cores(df)
    plot_time_vs_mesh_quality(df)


def get_args() -> dict:
    parser = argparse.ArgumentParser(description='Web of Phyngs evaluation results plotter')
    parser.add_argument('-hn', '--host-name',
                        help='Host name, same as in the results folder',
                        required=False)
    parser.add_argument('-p', '--phyngs',
                        help='Plot data from phyngs',
                        action='store_true',
                        required=False)
    parser.add_argument('-c', '--cores',
                        help='Plot data from cores',
                        action='store_true',
                        required=False)
    parser.add_argument('-m', '--meshes',
                        help='Plot data from meshes',
                        action='store_true',
                        required=False)
    parser.add_argument('-a', '--all',
                        help='Plot data from all CSVs',
                        action='store_true',
                        required=False)
    return vars(parser.parse_args())


def main():
    global RES_STORAGE
    path = RES_STORAGE
    args = get_args()

    if host_name := args['host_name']:
        path = f'{path}/{host_name}'
        if not os.path.exists(path):
            raise Exception(f'Path for host {host_name} does not exist')
        RES_STORAGE = path

    if args['phyngs']:
        name = 'phyngs'
        func = plot_time_vs_phyngs
    elif args['cores']:
        name = 'cores'
        func = plot_time_vs_cores
    elif args['meshes']:
        name = 'meshes'
        func = plot_time_vs_mesh_quality
    elif args['all']:
        name = 'all'
        func = plot_time_vs_all
    else:
        filepath = glob.glob(f'{path}/*.csv')[-1]
        if not filepath:
            raise Exception(f'No CSVs in the result folder')
        name = re.search(r'\/.+\/(.+)\.csv', filepath).group(1)
        RES_STORAGE = f'../results/{name}'
        Path(RES_STORAGE).mkdir(exist_ok=True)
        df = pd.read_csv(filepath, index_col=0, sep=';')
        plot_time_vs_phyngs(df)
        plot_time_vs_mesh_quality(df)
        plot_time_vs_cores(df)
        return
    filepath = f'{path}/{name}.csv'
    if not os.path.exists(filepath):
        raise Exception(f'Path for host {host_name} {name} does not exist')
    RES_STORAGE += f'/{name}'
    Path(RES_STORAGE).mkdir(exist_ok=True)
    df = pd.read_csv(filepath, index_col=0, sep=';')
    func(df)


if __name__ == '__main__':
    main()
