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
    result[MAE_SETUP_K].append(sem(setup_times))
    result[MAE_SOLVE_K].append(sem(solve_times))

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
            MAE_SETUP_K: [],
            MAE_SOLVE_K: [],
        }
        max_phyngs_df = phyng_df.loc[phyng_df[PHYNGS_NUM] == max_phyngs]
        # Iterate through each mesh quality
        for mesh_quality in mesh_qualities:
            mesh_quality_df = max_phyngs_df.loc[max_phyngs_df[MSH_QUAL] == mesh_quality]
            mesh_results[phyng_type][MESH_QUALITY_K].append(mesh_quality)

            get_data_for_timing(mesh_results[phyng_type], mesh_quality_df)
        mesh_results[phyng_type][MAE_SETUP_K] = np.round(np.average(mesh_results[phyng_type][MAE_SETUP_K]), 3)
        mesh_results[phyng_type][MAE_SOLVE_K] = np.round(np.average(mesh_results[phyng_type][MAE_SOLVE_K]), 3)

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
            MAE_SETUP_K: [],
            MAE_SOLVE_K: [],
        }
        max_phyngs_df = phyng_df.loc[phyng_df[PHYNGS_NUM] == max_phyngs]
        # Iterate through each core
        for core in cores:
            core_df = max_phyngs_df.loc[max_phyngs_df[CORES] == core]
            cores_result[phyng_type][NUM_OF_CORES_K].append(core)

            get_data_for_timing(cores_result[phyng_type], core_df)
        cores_result[phyng_type][MAE_SETUP_K] = np.round(np.average(cores_result[phyng_type][MAE_SETUP_K]), 3)
        cores_result[phyng_type][MAE_SOLVE_K] = np.round(np.average(cores_result[phyng_type][MAE_SOLVE_K]), 3)

    return cores_result
