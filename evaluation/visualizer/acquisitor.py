import numpy as np
import pandas as pd
from scipy.stats import sem

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
NUM_OF_CORES_K = 'Number of Cores'
NUM_OF_PHYNGS_K = 'Number of Phyngs'
AVG_SETUP_TIME_K = 'Average Setup Time, s'
AVG_SOLVE_TIME_K = 'Average Solving Time, s'
SETUP_TIME_K = 'Setup Time, s'
SOLVE_TIME_K = 'Solving Time, s'
MAE_K = 'MAE'
MAE_SETUP_K = 'MAE setup, s'
MAE_SOLVE_K = 'MAE solve, s'
WHISKER_K = 'whisker'
TITLE_K = 'title'
SETUP_K = 'setup'
SOLVE_K = 'solving'
TITLE_SETUP_K = f'{TITLE_K} {SETUP_K}'
TITLE_SOLVE_K = f'{TITLE_K} {SOLVE_K}'


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
    result[MAE_SETUP_K].append(sem(setup_times) if setup_times.shape[0] > 1 else 0)
    result[MAE_SOLVE_K].append(sem(solve_times) if setup_times.shape[0] > 1 else 0)

    # For regular averaged plot
    result[AVG_SETUP_TIME_K].append(np.average(setup_times))
    result[AVG_SOLVE_TIME_K].append(np.average(solve_times))


def get_phyngs_data(df: pd.DataFrame) -> dict:
    # Get only the best mesh and the most cores
    # mesh_quality = max(df[MSH_QUAL])
    # best_df = df.loc[df[MSH_QUAL] == mesh_quality]
    # cores = max(best_df[CORES])
    # best_df = best_df.loc[best_df[CORES] == cores]

    # Separate DFs according to phyng types
    phyngs_df = form_phyng_df_dict(df)

    phyng_results = {}

    # Iterate through each phyng type and DFs
    for phyng_type, phyng_df in phyngs_df.items():
        mesh_quality = max(phyng_df[MSH_QUAL])
        cores = max(phyng_df[CORES])
        phyng_amounts = sorted(set(phyng_df[PHYNGS_NUM].values))
        phyng_results[phyng_type] = {
            TITLE_SETUP_K: f'{phyng_type.capitalize()} {SETUP_K} vs phyngs '
                           f'({mesh_quality} % mesh quality, {cores} cores)',
            TITLE_SOLVE_K: f'{phyng_type.capitalize()} {SOLVE_K} vs phyngs '
                           f'({mesh_quality} % mesh quality, {cores} cores)',
            NUM_OF_PHYNGS_K: [],
            AVG_SETUP_TIME_K: [],
            AVG_SOLVE_TIME_K: [],
            SETUP_TIME_K: [],
            SOLVE_TIME_K: [],
            MAE_SETUP_K: [],
            MAE_SOLVE_K: [],
        }
        # Iterate through each amount of phyngs
        for amount in phyng_amounts:
            phyng_amount_df = phyng_df.loc[phyng_df[PHYNGS_NUM] == amount]
            phyng_results[phyng_type][NUM_OF_PHYNGS_K].append(amount)

            get_data_for_timing(phyng_results[phyng_type], phyng_amount_df)
        phyng_results[phyng_type][MAE_SETUP_K] = np.round(np.average(phyng_results[phyng_type][MAE_SETUP_K]), 3)
        phyng_results[phyng_type][MAE_SOLVE_K] = np.round(np.average(phyng_results[phyng_type][MAE_SOLVE_K]), 3)

    return phyng_results


def get_phyngs_iter(values, phyngs):
    if phyngs == 'all':
        return values
    elif phyngs == 'boundary':
        return [values[0], values[-1]]
    elif phyngs == 'boundary middle':
        return [values[0], values[len(values) // 2], values[-1]]
    elif phyngs == 'max':
        return [max(values)]
    elif phyngs == 'min':
        return [min(values)]
    else:
        raise Exception(f'Wrong iter type {phyngs}')


def get_mesh_data(df: pd.DataFrame, phyngs) -> dict:
    # Get only the most cores
    cores = max(df[CORES])
    best_df = df.loc[df[CORES] == cores]

    # Separate DFs according to phyng types
    phyngs_df = form_phyng_df_dict(best_df)

    mesh_results = {}

    # Iterate through each phyng type and DFs
    for phyng_type, phyng_df in phyngs_df.items():
        mesh_results[phyng_type] = {
            TITLE_SETUP_K: f'{phyng_type.capitalize()} {SETUP_K} vs mesh quality ({cores} cores)',
            TITLE_SOLVE_K: f'{phyng_type.capitalize()} {SOLVE_K} vs mesh quality ({cores} cores)',
        }
        cur_mesh_t = mesh_results[phyng_type]
        phyng_iter = get_phyngs_iter(sorted(list(set(phyng_df[PHYNGS_NUM]))), phyngs)
        for phyngs_num in phyng_iter:
            mesh_qualities = sorted(set(phyng_df[MSH_QUAL].values))
            cur_mesh_t[phyngs_num] = {
                MESH_QUALITY_K: [],
                AVG_SETUP_TIME_K: [],
                AVG_SOLVE_TIME_K: [],
                SETUP_TIME_K: [],
                SOLVE_TIME_K: [],
                MAE_SETUP_K: [],
                MAE_SOLVE_K: [],
            }
            phyngs_df = phyng_df.loc[phyng_df[PHYNGS_NUM] == phyngs_num]
            # Iterate through each mesh quality
            for mesh_quality in mesh_qualities:
                mesh_quality_df = phyngs_df.loc[phyngs_df[MSH_QUAL] == mesh_quality]
                if not np.all(mesh_quality_df[SETUP_TIME].values):
                    continue
                cur_mesh_t[phyngs_num][MESH_QUALITY_K].append(mesh_quality)

                get_data_for_timing(cur_mesh_t[phyngs_num], mesh_quality_df)
            cur_mesh_t[phyngs_num][MAE_SETUP_K] = np.round(np.average(cur_mesh_t[phyngs_num][MAE_SETUP_K]), 3)
            cur_mesh_t[phyngs_num][MAE_SOLVE_K] = np.round(np.average(cur_mesh_t[phyngs_num][MAE_SOLVE_K]), 3)

    return mesh_results


def get_cores_data(df: pd.DataFrame, phyngs) -> dict:
    # # Get only the most cores
    # mesh_quality = max(df[MSH_QUAL])
    # best_df = df.loc[df[MSH_QUAL] == mesh_quality]
    #
    # # Separate DFs according to phyng types
    # phyngs_df = form_phyng_df_dict(best_df)
    phyngs_df = form_phyng_df_dict(df)

    cores_result = {}

    # Iterate through each phyng type and DFs
    for phyng_type, phyng_df in phyngs_df.items():
        mesh_quality = max(phyng_df[MSH_QUAL])
        cores_result[phyng_type] = {
            TITLE_SETUP_K: f'{phyng_type.capitalize()} {SETUP_K} vs cores ({mesh_quality} % mesh quality)',
            TITLE_SOLVE_K: f'{phyng_type.capitalize()} {SOLVE_K} vs cores ({mesh_quality} % mesh quality)',
        }
        cur_core_t = cores_result[phyng_type]
        phyng_iter = get_phyngs_iter(sorted(list(set(phyng_df[PHYNGS_NUM]))), phyngs)
        for phyngs_num in phyng_iter:
            cores = sorted(set(phyng_df[CORES].values))
            cur_core_t[phyngs_num] = {
                NUM_OF_CORES_K: [],
                AVG_SETUP_TIME_K: [],
                AVG_SOLVE_TIME_K: [],
                SETUP_TIME_K: [],
                SOLVE_TIME_K: [],
                MAE_SETUP_K: [],
                MAE_SOLVE_K: [],
            }
            max_phyngs_df = phyng_df.loc[phyng_df[PHYNGS_NUM] == phyngs_num]
            # Iterate through each core
            for core in cores:
                core_df = max_phyngs_df.loc[max_phyngs_df[CORES] == core]
                cur_core_t[phyngs_num][NUM_OF_CORES_K].append(core)

                get_data_for_timing(cur_core_t[phyngs_num], core_df)
            cur_core_t[phyngs_num][MAE_SETUP_K] = np.round(np.average(cur_core_t[phyngs_num][MAE_SETUP_K]), 3)
            cur_core_t[phyngs_num][MAE_SOLVE_K] = np.round(np.average(cur_core_t[phyngs_num][MAE_SOLVE_K]), 3)

    return cores_result


def get_all_data(df: pd.DataFrame):
    cases = list(dict.fromkeys(list(df.index)))
    averaged_data = {
        CASE_NAME: [],
        NUM_OF_CORES_K: [],
        MESH_QUALITY_K: [],
        PHYNGS_TYPE: [],
        NUM_OF_PHYNGS_K: [],
        AVG_SETUP_TIME_K: [],
        AVG_SOLVE_TIME_K: []
    }
    averaged_columns = list(averaged_data.keys())
    for case in cases:
        rows = df.loc[df.index == case]
        averaged_data[CASE_NAME].append(case)
        averaged_data[NUM_OF_CORES_K].append(np.average(rows[CORES]))
        averaged_data[MESH_QUALITY_K].append(np.average(rows[MSH_QUAL]))
        averaged_data[PHYNGS_TYPE].append(rows[PHYNGS_TYPE][0])
        averaged_data[NUM_OF_PHYNGS_K].append(np.average(rows[PHYNGS_NUM]))
        averaged_data[AVG_SETUP_TIME_K].append(np.average(rows[SETUP_TIME]) / 1000)
        averaged_data[AVG_SOLVE_TIME_K].append(np.average(rows[SOLVE_TIME]) / 1000)
    # return averaged_data
    return pd.DataFrame(averaged_data, columns=averaged_columns)
