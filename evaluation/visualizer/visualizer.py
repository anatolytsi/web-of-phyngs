import argparse
import glob
import os.path
import re

from acquisitor import *
from plotter import *


def plot_time_vs_phyngs(df: Union[pd.DataFrame, List[pd.DataFrame]],
                        hosts: Union[str, List[str]]):
    setup_handler = lambda ax, res, legend, color: draw_lines_plot(ax, res[NUM_OF_PHYNGS_K],
                                                                   res[AVG_SETUP_TIME_K],
                                                                   legend=legend, mae=res[MAE_SETUP_K],
                                                                   fit_func=[func1, func3],
                                                                   color=color, fit_color=color)
    solve_handler = lambda ax, res, legend, color: draw_lines_plot(ax, res[NUM_OF_PHYNGS_K],
                                                                   res[AVG_SOLVE_TIME_K],
                                                                   legend=legend, mae=res[MAE_SOLVE_K],
                                                                   fit_func=[func1, func3],
                                                                   color=color, fit_color=color)
    results = []
    colors = TUM_COLORS
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
    setup_handler = lambda ax, res, legend, color: draw_lines_plot(ax, res[MESH_QUALITY_K], res[AVG_SETUP_TIME_K],
                                                                   legend=legend, mae=res[MAE_SETUP_K],
                                                                   fit_func=func5,
                                                                   color=color, fit_color=color)
    solve_handler = lambda ax, res, legend, color: draw_lines_plot(ax, res[MESH_QUALITY_K],
                                                                   res[AVG_SOLVE_TIME_K],
                                                                   legend=legend, mae=res[MAE_SOLVE_K],
                                                                   fit_func=func5,
                                                                   color=color, fit_color=color)
    results = []
    colors = TUM_COLORS
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
                                                                   res[AVG_SOLVE_TIME_K], mae=res[MAE_SOLVE_K],
                                                                   legend=legend,
                                                                   fit_func=[func_power, func_exp, func_hyperbolic,
                                                                             func_log],
                                                                   color=color, fit_color=color)
    results = []
    colors = TUM_COLORS
    if isinstance(df, list):
        for dataframe in df:
            results.append(get_cores_data(dataframe))
    else:
        results = [get_cores_data(df)]
    plot_solve_vs_data(results, solve_handler, NUM_OF_CORES_K, f'{RES_STORAGE}/cores', hosts, colors, yspan_start=60)


def plot_time_vs_all(df: Union[pd.DataFrame, List[pd.DataFrame]],
                     hosts: Union[str, List[str]]):
    Path(f'{RES_STORAGE}/3d - constant phyngs').mkdir(exist_ok=True)
    Path(f'{RES_STORAGE}/3d - constant cores').mkdir(exist_ok=True)
    Path(f'{RES_STORAGE}/3d - constant mesh').mkdir(exist_ok=True)
    if isinstance(df, list):
        for dataframe, host in zip(df, hosts):
            Path(f'{RES_STORAGE}/3d - constant phyngs/{host}').mkdir(exist_ok=True)
            Path(f'{RES_STORAGE}/3d - constant cores/{host}').mkdir(exist_ok=True)
            Path(f'{RES_STORAGE}/3d - constant mesh/{host}').mkdir(exist_ok=True)
            data_df = get_all_data(dataframe)
            plot3d_const_phyngs(data_df, f'{RES_STORAGE}/3d - constant phyngs/{host}')
            plot3d_const_cores(data_df, f'{RES_STORAGE}/3d - constant cores/{host}')
            plot3d_const_mesh(data_df, f'{RES_STORAGE}/3d - constant mesh/{host}')
    else:
        results = [get_cores_data(df)]


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
        filepath = glob.glob(f'{RES_STORAGE}/*.csv')[-1]
        if not filepath:
            raise Exception(f'No CSVs in the result folder')
        name = re.search(r'\/.+\/(.+)\.csv', filepath).group(1)
        Path(RES_STORAGE).mkdir(exist_ok=True)
        df = pd.read_csv(filepath, index_col=0, sep=';')
        plot_time_vs_phyngs([df], [name])
        plot_time_vs_mesh_quality([df], [name])
        plot_time_vs_cores([df], [name])
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
