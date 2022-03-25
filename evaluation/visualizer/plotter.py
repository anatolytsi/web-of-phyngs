from pathlib import Path
from typing import Union, List, Callable

import numpy as np
from matplotlib.ticker import LinearLocator, FormatStrFormatter
from scipy.optimize import curve_fit
from scipy.interpolate import griddata
from matplotlib import cm
import matplotlib.pyplot as plt

from acquisitor import *


TUM_COLORS = [(0, 101, 189), (100, 160, 200), (153, 153, 153), (218, 215, 203)]


def func_exp(x, a, b, c):
    return a * np.exp(np.multiply(x, -b)) + c


def func_log(x, a, b):
    return a + b * np.log(x)


def func_hyperbolic(x, a, b, c):
    return a * np.divide(b, x) + c


def func_power(x, a, b, c):
    return a * np.power(x, b) + c


def func_root(x, a, b, c):
    return a * np.power(x, -b) + c


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


def find_best_fit(x_coords, y_coords, fit_funcs):
    sel_idx = 0
    avg_err = 1e10
    popt = 0
    for idx, func in enumerate(fit_funcs):
        try:
            popt_new, pcov = curve_fit(func, x_coords, y_coords)
        except Exception as e:
            print(e)
            continue
        y_errors = []
        for x_idx, x in enumerate(x_coords):
            y_errors.append(abs(y_coords[x_idx] - func(x, *popt_new)))
        new_avg_err = np.average(y_errors)
        if avg_err > new_avg_err:
            avg_err = new_avg_err
            sel_idx = idx
            popt = popt_new
    return sel_idx, popt


def find_closest_idx(lst, value):
    best_idx = 0
    best_dif = 1000
    for idx, v in enumerate(lst):
        if (dif := abs(value - v)) < best_dif:
            best_dif = dif
            best_idx = idx
    return best_idx


def draw_lines_plot(ax, x_in: List[int], y_in: List[int], color: List[int] = None, legend: str = 'original',
                    fit: bool = True, fit_func: Union[Callable, List[Callable]] = func3,
                    fit_color: List[int] = None,
                    mae: float = None,
                    side_text: str = '',
                    prediction_max: int = 0):
    color = (0, 101, 189) if not color else color
    x, y = [], []
    for v_x, v_y in zip(x_in, y_in):
        if v_y:
            x.append(v_x)
            y.append(v_y)
    if legend:
        legend_mae = f'{legend}, {MAE_K}: {mae}' if mae else legend
        l1, = ax.plot(x, y, 'o', color=[c / 255 for c in color],
                      label=legend_mae, markersize=3)
    else:
        l1, = ax.plot(x, y, 'o', color=[c / 255 for c in color], markersize=3)
    if side_text:
        best_idx = find_closest_idx(x, 40)
        t = plt.text(x[best_idx] + 0.7, y[best_idx], side_text)
        t.set_bbox({'facecolor': 'white', 'alpha': 0.5, 'edgecolor': 'white'})
    if fit:
        fit_color = (0, 101, 189) if not fit_color else fit_color
        if isinstance(fit_func, list):
            sel_idx, popt = find_best_fit(x, y, fit_func)
            fit_func = fit_func[sel_idx]
        else:
            popt, pcov = curve_fit(fit_func, x, y)
        x_fit = np.linspace(x[0], x[-1], 50)
        if legend:
            l2, = ax.plot(x_fit, fit_func(x_fit, *popt), color=[c / 255 for c in fit_color],
                          label=f'{legend}: {get_fit_title(fit_func)}')
        else:
            l2, = ax.plot(x_fit, fit_func(x_fit, *popt), color=[c / 255 for c in fit_color])

        if prediction_max and x[-1] < prediction_max:
            x_fit = np.linspace(x[-1], prediction_max, 50)
            if legend:
                l2, = ax.plot(x_fit, fit_func(x_fit, *popt), '--', color=[c / 255 for c in fit_color],
                              label=f'{legend}: prediction')
            else:
                l2, = ax.plot(x_fit, fit_func(x_fit, *popt), '--', color=[c / 255 for c in fit_color])

        ax.legend()


def plot_3d(df, path, x_name, y_name, z_name, fit_func, title='3dplot'):
    Path(f'{path}/pdfs').mkdir(exist_ok=True)
    Path(f'{path}/pngs').mkdir(exist_ok=True)
    points = 100
    x = []
    y = []
    z = []

    fig = plt.figure()
    ax = fig.gca(projection='3d')
    
    # Fit data
    for y_unique in set(df[y_name]):
        df_y = df.loc[df[y_name] == y_unique]
        popt, pcov = curve_fit(fit_func, list(df_y[x_name]), list(df_y[z_name]))
        x.extend(np.linspace(list(df_y[x_name])[0], list(df_y[x_name])[-1], points))
        y.extend([y_unique for _ in range(points)])
        z.extend(fit_func(x, *popt))
    surf = ax.plot_trisurf(x, y, z, cmap=cm.coolwarm, linewidth=0.5, vmin=0, vmax=60)
    ax.set_xlabel(x_name)
    ax.set_ylabel(y_name)
    ax.set_zlabel(z_name)
    ax.set_title(title)

    fig.colorbar(surf, shrink=0.5, aspect=10, location='right', pad=0.15)
    plt.savefig(f'{path}/pdfs/{title}.pdf')
    plt.savefig(f'{path}/pngs/{title}.png')
    plt.close()


def plot3d_const_mesh(df, path):
    fit_funcs = [
        func_hyperbolic,  # heaters
        func_hyperbolic,  # acs
        func_hyperbolic,  # doors
        func_hyperbolic,  # windows
    ]
    for phyng_type, fit_func in zip(PHYNG_TYPES, fit_funcs):
        phyng_df = df.loc[df[PHYNGS_TYPE] == phyng_type]
        max_mesh = phyng_df[MESH_QUALITY_K].max()
        max_mesh_df = phyng_df.loc[phyng_df[MESH_QUALITY_K] == max_mesh]
        title_solve = f'{int(max_mesh)} % mesh, {phyng_type} {SOLVE_K}\n{get_fit_title(fit_func)} estimation'
        plot_3d(max_mesh_df, path, NUM_OF_CORES_K, NUM_OF_PHYNGS_K, AVG_SOLVE_TIME_K, fit_func,
                title=title_solve)


def plot3d_const_cores(df, path):
    fit_funcs = [
        [func3, func3],  # heaters
        [func3, func3],  # acs
        [func3, func3],  # doors
        [func3, func3],  # windows
    ]
    for phyng_type, fit_func in zip(PHYNG_TYPES, fit_funcs):
        phyng_df = df.loc[df[PHYNGS_TYPE] == phyng_type]
        max_cores = phyng_df[NUM_OF_CORES_K].max()
        cores_df = phyng_df.loc[phyng_df[NUM_OF_CORES_K] == max_cores]
        title_setup = f'{int(max_cores)} cores, {phyng_type} {SETUP_K}\n{get_fit_title(fit_func[0])} estimation'
        title_solve = f'{int(max_cores)} cores, {phyng_type} {SOLVE_K}\n{get_fit_title(fit_func[1])} estimation'
        plot_3d(cores_df, path, MESH_QUALITY_K, NUM_OF_PHYNGS_K, AVG_SETUP_TIME_K, fit_func[0],
                title=title_setup)
        plot_3d(cores_df, path, MESH_QUALITY_K, NUM_OF_PHYNGS_K, AVG_SOLVE_TIME_K, fit_func[1],
                title=title_solve)


def plot3d_const_phyngs(df, path):
    fit_funcs = [
        func_hyperbolic,  # heaters
        func_hyperbolic,  # acs
        func_hyperbolic,  # doors
        func_hyperbolic,  # windows
    ]
    for phyng_type, fit_func in zip(PHYNG_TYPES, fit_funcs):
        phyng_df = df.loc[df[PHYNGS_TYPE] == phyng_type]
        max_phyng = phyng_df[NUM_OF_PHYNGS_K].max()
        title_solve = f'{int(max_phyng)} {phyng_type} {SOLVE_K}\n{get_fit_title(fit_func)} estimation'
        phyng_num_df = phyng_df.loc[phyng_df[NUM_OF_PHYNGS_K] == max_phyng]
        plot_3d(phyng_num_df, path, NUM_OF_CORES_K, MESH_QUALITY_K, AVG_SOLVE_TIME_K, fit_func,
                title=title_solve)


def plot_setup_vs_data(results, handler, xlabel, path, legends, colors, xspan=None, y_lim=0):
    Path(f'{path}/pdfs').mkdir(exist_ok=True)
    Path(f'{path}/pngs').mkdir(exist_ok=True)

    for type_key in results[0].keys():
        fig, ax = plt.subplots()
        title = results[0][type_key][TITLE_SETUP_K]
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(AVG_SETUP_TIME_K)
        for result, legend, color in zip(results, legends, colors[:len(results)]):
            type_res = result[type_key]
            if AVG_SETUP_TIME_K in type_res:
                handler(ax, type_res, legend, color)
            else:
                for phyng_k, phyng_res in type_res.items():
                    if isinstance(phyng_res, dict):
                        handler(ax, phyng_res, legend, color, side_text=f'#{phyng_k}')
                        if legend:
                            legend = ''

        if y_lim and ax.get_ylim()[1] > y_lim:
            ax.set_ylim([None, y_lim])

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
            plt.text(text_x, text_y, 'Mesh is too coarse', rotation=90, fontsize=16)

        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        plt.savefig(f'{path}/pdfs/{title}.pdf')
        plt.savefig(f'{path}/pngs/{title}.png')
        plt.close()


def plot_solve_vs_data(results, handler, xlabel, path, legends, colors, xspan=None, yspan_start=None, y_lim=0):
    Path(f'{path}/pdfs').mkdir(exist_ok=True)
    Path(f'{path}/pngs').mkdir(exist_ok=True)

    for type_key in results[0].keys():
        fig, ax = plt.subplots()
        title = results[0][type_key][TITLE_SOLVE_K]
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(AVG_SOLVE_TIME_K)
        for result, legend, color in zip(results, legends, colors[:len(results)]):
            type_res = result[type_key]
            if AVG_SOLVE_TIME_K in type_res:
                handler(ax, type_res, legend, color)
            else:
                for phyng_k, phyng_res in type_res.items():
                    if isinstance(phyng_res, dict):
                        handler(ax, phyng_res, legend, color, side_text=f'#{phyng_k}')
                        if legend:
                            legend = ''

        if y_lim and ax.get_ylim()[1] > y_lim:
            ax.set_ylim([None, y_lim])

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
            plt.text(text_x, text_y, 'Mesh is too coarse', rotation=90, fontsize=16)

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

        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        plt.savefig(f'{path}/pdfs/{title}.pdf')
        plt.savefig(f'{path}/pngs/{title}.png')
        plt.close()
