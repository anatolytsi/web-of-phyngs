import argparse
import glob
import os.path
import re
from pathlib import Path
from typing import Union, List, Callable

import numpy as np
from scipy.optimize import curve_fit
import pandas as pd
import matplotlib as mpl
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


def func_hyperbolic(x, a, b):
    return a + np.divide(b, x)


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
    elif func == func_hyperbolic:
        return 'hyperbolic fit'
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


def find_best_fit(x_coords, y_coords, fit_funcs):
    sel_idx = 0
    avg_err = 1e10
    popt = 0
    for idx, func in enumerate(fit_funcs):
        popt_new, pcov = curve_fit(func, x_coords, y_coords)
        y_errors = []
        for x_idx, x in enumerate(x_coords):
            y_errors.append(abs(y_coords[x_idx] - func(x, *popt_new)))
        new_avg_err = np.average(y_errors)
        if avg_err > new_avg_err:
            avg_err = new_avg_err
            sel_idx = idx
            popt = popt_new
    return sel_idx, popt


def draw_lines_plot(ax, x: List[int], y: List[int], color: List[int] = None, legend: str = 'original',
                    fit: bool = True, fit_func: Union[Callable, List[Callable]] = func3,
                    fit_color: List[int] = None):
    color = (0, 101, 189) if not color else color
    l1, = ax.plot(x, y, 'o', color=[c / 255 for c in color],
                  label=legend, markersize=3)
    if fit:
        fit_color = (0, 101, 189) if not fit_color else fit_color
        if isinstance(fit_func, list):
            sel_idx, popt = find_best_fit(x, y, fit_func)
            fit_func = fit_func[sel_idx]
        else:
            popt, pcov = curve_fit(fit_func, x, y)
        x_fit = np.linspace(x[0], x[-1], 50)
        l2, = ax.plot(x_fit, fit_func(x_fit, *popt), color=[c / 255 for c in fit_color],
                      label=f'{legend}: {get_fit_title(fit_func)}')
        ax.legend()


def plot_setup_vs_data(results, handler, xlabel, path, legends, colors, xspan=None):
    Path(f'{path}/pdfs').mkdir(exist_ok=True)
    Path(f'{path}/pngs').mkdir(exist_ok=True)

    for res_key in results[0].keys():
        fig, ax = plt.subplots()
        title = results[0][res_key][TITLE_SETUP_K]
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(AVG_SOLVE_TIME_K)
        for result, legend, color in zip(results, legends, colors):
            res = result[res_key]
            handler(ax, res, legend, color)
        if xspan:
            ax.axvspan(xspan[0], xspan[1], alpha=0.3, color='red', linestyle='None')
            ax.set_xlim([xspan[0], None])
            x_min, _ = ax.get_xlim()
            x_max = xspan[1]
            x_range = x_max - x_min
            y_min, y_max = ax.get_ylim()
            y_range = y_max - y_min
            text_x = x_min + x_range / 2 - x_range / 8
            text_y = y_min + y_range / 2 - y_range / 4
            plt.text(text_x, text_y, 'Mesh is to coarse', rotation=90, fontsize=16)

        plt.savefig(f'{path}/pdfs/{title}.pdf')
        plt.savefig(f'{path}/pngs/{title}.png')
        plt.close()


def plot_solve_vs_data(results, handler, xlabel, path, legends, colors, xspan=None, yspan_start=None):
    Path(f'{path}/pdfs').mkdir(exist_ok=True)
    Path(f'{path}/pngs').mkdir(exist_ok=True)

    for res_key in results[0].keys():
        fig, ax = plt.subplots()
        title = results[0][res_key][TITLE_SOLVE_K]
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(AVG_SOLVE_TIME_K)
        for result, legend, color in zip(results, legends, colors):
            res = result[res_key]
            handler(ax, res, legend, color)

        if xspan:
            ax.axvspan(xspan[0], xspan[1], alpha=0.3, color='red', linestyle='None')
            ax.set_xlim([xspan[0], None])
            x_min, _ = ax.get_xlim()
            x_max = xspan[1]
            x_range = x_max - x_min
            y_min, y_max = ax.get_ylim()
            y_range = y_max - y_min
            text_x = x_min + x_range / 2 - x_range / 8
            text_y = y_min + y_range / 2 - y_range / 4
            plt.text(text_x, text_y, 'Mesh is to coarse', rotation=90, fontsize=16)

        if yspan_start:
            _, y_max = ax.get_ylim()
            y_min = yspan_start
            y_max += 10
            ax.axhspan(y_min, y_max, alpha=0.3, color='red', linestyle='None')
            ax.set_ylim([None, y_max])
            x_min, x_max = ax.get_xlim()
            x_range = x_max - x_min
            y_range = y_max - y_min
            text_x = x_min + x_range / 2 - x_range / 8
            text_y = y_min + y_range / 2
            plt.text(text_x, text_y, 'No real-time', fontsize=16)

        plt.savefig(f'{path}/pdfs/{title}.pdf')
        plt.savefig(f'{path}/pngs/{title}.png')
        plt.close()


def plot_time_vs_phyngs(df: Union[pd.DataFrame, List[pd.DataFrame]],
                        hosts: Union[str, List[str]]):
    setup_handler = lambda ax, res, legend, color: draw_lines_plot(ax, res[NUM_OF_PHYNGS_K],
                                                                   res[AVG_SETUP_TIME_K],
                                                                   legend=legend,
                                                                   fit_func=[func1, func3],
                                                                   color=color, fit_color=color)
    solve_handler = lambda ax, res, legend, color: draw_lines_plot(ax, res[NUM_OF_PHYNGS_K],
                                                                   res[AVG_SOLVE_TIME_K],
                                                                   legend=legend,
                                                                   fit_func=[func1, func3],
                                                                   color=color, fit_color=color)
    results = []
    colors = [(0, 101, 189), (153, 153, 153)]
    if isinstance(df, list):
        for dataframe in df:
            results.append(get_phyngs_data(dataframe))
    else:
        results = [get_phyngs_data(df)]
    plot_setup_vs_data(results, setup_handler, NUM_OF_PHYNGS_K, f'{RES_STORAGE}/phyngs', hosts, colors)
    plot_solve_vs_data(results, solve_handler, NUM_OF_PHYNGS_K, f'{RES_STORAGE}/phyngs', hosts, colors, yspan_start=60)


def plot_time_vs_mesh_quality(df: Union[pd.DataFrame, List[pd.DataFrame]],
                              hosts: Union[str, List[str]]):
    xspan = [40, 50]
    setup_handler = lambda ax, res, legend, color: draw_lines_plot(ax, res[MESH_QUALITY_K], res[AVG_SOLVE_TIME_K],
                                                                   legend=legend,
                                                                   fit_func=func5,
                                                                   color=color, fit_color=color)
    solve_handler = lambda ax, res, legend, color: draw_lines_plot(ax, res[MESH_QUALITY_K],
                                                                   res[AVG_SOLVE_TIME_K],
                                                                   legend=legend,
                                                                   fit_func=func5,
                                                                   color=color, fit_color=color)
    results = []
    colors = [(0, 101, 189), (153, 153, 153)]
    if isinstance(df, list):
        for dataframe in df:
            results.append(get_mesh_data(dataframe))
    else:
        results = [get_mesh_data(df)]
    plot_setup_vs_data(results, setup_handler, MESH_QUALITY_K, f'{RES_STORAGE}/meshes', hosts, colors, xspan)
    plot_solve_vs_data(results, solve_handler, MESH_QUALITY_K, f'{RES_STORAGE}/meshes', hosts, colors, xspan, 60)


def plot_time_vs_cores(df: Union[pd.DataFrame, List[pd.DataFrame]],
                       hosts: Union[str, List[str]]):
    solve_handler = lambda ax, res, legend, color: draw_lines_plot(ax, res[NUM_OF_CORES_K],
                                                                   res[AVG_SOLVE_TIME_K],
                                                                   legend=legend,
                                                                   fit_func=[func_power, func_exp, func_hyperbolic,
                                                                             func_log],
                                                                   color=color, fit_color=color)
    results = []
    colors = [(0, 101, 189), (153, 153, 153)]
    if isinstance(df, list):
        for dataframe in df:
            results.append(get_cores_data(dataframe))
    else:
        results = [get_cores_data(df)]
    plot_solve_vs_data(results, solve_handler, NUM_OF_CORES_K, f'{RES_STORAGE}/cores', hosts, colors, yspan_start=60)


def plot_time_vs_all(df: Union[pd.DataFrame, List[pd.DataFrame]],
                     hosts: Union[str, List[str]]):
    plot_time_vs_phyngs(df, hosts)
    plot_time_vs_cores(df, hosts)
    plot_time_vs_mesh_quality(df, hosts)


def get_args() -> dict:
    parser = argparse.ArgumentParser(description='Web of Phyngs evaluation results plotter')
    parser.add_argument('-hn', '--host-names',
                        help='Host name, same as in the results folder',
                        nargs='+',
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
    args = get_args()

    host_names = args['host_names']

    if host_names:
        for host_name in host_names:
            path = f'{RES_STORAGE}/{host_name}'
            if not os.path.exists(path):
                raise Exception(f'Path for host {host_name} does not exist')

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
        # RES_STORAGE = f'../results/{name}'
        Path(RES_STORAGE).mkdir(exist_ok=True)
        df = pd.read_csv(filepath, index_col=0, sep=';')
        plot_time_vs_phyngs(df)
        plot_time_vs_mesh_quality(df)
        plot_time_vs_cores(df)
        return
    df = []
    for host_name in host_names:
        filepath = f'{RES_STORAGE}/{host_name}/{name}.csv'
        if not os.path.exists(filepath):
            raise Exception(f'Path for host {host_name} {name} does not exist')
        path = f'{RES_STORAGE}/{name}'
        Path(path).mkdir(exist_ok=True)
        df.append(pd.read_csv(filepath, index_col=0, sep=';'))
    func(df, host_names)


if __name__ == '__main__':
    main()
