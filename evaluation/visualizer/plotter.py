from pathlib import Path
from typing import Union, List, Callable

import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

from acquisitor import TITLE_SETUP_K, TITLE_SOLVE_K, AVG_SOLVE_TIME_K


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
