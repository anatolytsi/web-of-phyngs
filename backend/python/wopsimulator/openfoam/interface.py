"""
OpenFOAM python interface
"""
import os
import time
import subprocess
from abc import ABC, abstractmethod
from multiprocessing import Process, cpu_count
from threading import Thread, Lock

from PyFoam.Execution.BasicRunner import BasicRunner

from .boundaries.boundary_conditions import BoundaryCondition
from .common.filehandling import remove_iterable_dirs, remove_dirs_with_pattern, force_remove_dir, \
    remove_files_in_dir_with_pattern, copy_tree, get_numerated_dirs
from .probes.probes import ProbeParser
from .system.snappyhexmesh import SnappyHexMeshDict


def get_latest_time(case_dir: str) -> float or int:
    """
    Returns latest time of the simulation that
    correspond to latest time result folder name
    :param case_dir: case directory
    :return: latest simulation time
    """
    try:
        latest_time = sorted([float(val) for val in get_numerated_dirs(case_dir, exception='0')])[-1]
        return int(latest_time) if latest_time.is_integer() else latest_time
    except IndexError:
        return 0


class OpenFoamInterface(ABC):
    """
    OpenFOAM Interface class. Serves as a wrapper of OpenFOAM commands
    """

    def __init__(self,
                 solver_type,
                 case_dir='.',
                 is_blocking=True,
                 is_mesh_parallel=False,
                 is_run_parallel=False,
                 num_of_cores=1):
        self.solver_type = solver_type
        self.case_dir = case_dir
        self.is_setup_parallel = is_mesh_parallel
        self.is_run_parallel = is_run_parallel
        self.available_cores = cpu_count()
        self.case_is_decomposed = False
        if self.available_cores >= num_of_cores > 0:
            self.num_of_cores = num_of_cores
        else:
            raise ValueError('Incorrect number of cores')
        self.boundaries = {}
        self.solver = None
        self.solver_thread = None
        self.solver_process = None
        self.solver_mutex = Lock()
        self.solver_is_blocking = is_blocking
        self.solver_is_running = False
        self.probe_parser = ProbeParser(self.case_dir)
        self.snappy_dict = SnappyHexMeshDict(self.case_dir)

    def remove_processor_dirs(self):
        """
        Removes processors folder
        :return: None
        """
        remove_iterable_dirs(self.case_dir, prepend_str='processor')

    def remove_solution_dirs(self):
        """
        Removes solution directories folder
        :return: None
        """
        remove_iterable_dirs(self.case_dir, exception='0')

    def remove_mesh_dirs(self):
        """
        Removes Mesh folders in all folders (e.g. polyMesh)
        :return: None
        """
        remove_dirs_with_pattern(self.case_dir, suffix='Mesh', is_recursive=True)

    def remove_tri_surface_dir(self):
        """
        Removes tri surface folder
        :return: None
        """
        force_remove_dir(f'{self.case_dir}/constant/triSurface')

    def clean_case(self):
        """
        Removes old files in the case directory and prepares the case
        :return: None
        """
        self.remove_processor_dirs()
        self.remove_solution_dirs()
        self.remove_mesh_dirs()
        remove_files_in_dir_with_pattern(self.case_dir, prefix='PyFoamState.')
        remove_files_in_dir_with_pattern(self.case_dir, prefix='log.')
        remove_files_in_dir_with_pattern(self.case_dir, suffix='.logfile')
        remove_files_in_dir_with_pattern(self.case_dir, suffix='.foam')
        remove_files_in_dir_with_pattern(self.case_dir, suffix='.OpenFOAM')

    def copy_stls(self, src_sub_dir: str = 'geometry', dst_sub_dir: str = 'constant/triSurface'):
        """
        Copy STLs from geometry dir to constant/triSurface or user prefered location
        TODO: move this function to other class later!
        :param src_sub_dir: source subdirectory
        :param dst_sub_dir:
        :return: None
        """
        stls_path = f'{self.case_dir}/{src_sub_dir}'
        path_to_copy = f'{self.case_dir}/{dst_sub_dir}'
        copy_tree(stls_path, path_to_copy)

    @staticmethod
    def run_command(argv, silent=True,
                    is_parallel: bool = False, cores: int = 1):
        """
        Runs a console command
        :param argv: command arguments
        :param silent: flag to output console data
        :param is_parallel: flag for multiprocessing run
        :param cores: cores to use for multiprocessing run
        :return: None
        """
        if is_parallel:
            argv = ['mpirun', '-np', str(cores)] + argv + ['-parallel']
        # The only pyFoam dependency by now
        runner = BasicRunner(argv=argv, silent=silent, logname=argv[0])
        runner.start()
        if not runner.runOK():
            raise Exception(f'{argv[0]} run failed')

    def run_solver_parallel(self, silent=True):
        """
        Runs solver using multiprocessing tools
        :param silent: flag to output console data
        :return: None
        """
        # FIXME: this function is not exited properly as the Process is terminated
        self.solver_mutex.acquire()
        argv = ['mpirun', '-np', str(self.num_of_cores), self.solver_type, '-case', self.case_dir, '-parallel']
        self.solver = BasicRunner(argv=argv, silent=silent, logname=self.solver_type)
        self.solver.start()
        print('Process terminated')
        self.solver_mutex.release()

    def run_solver(self, silent=True):
        """
        Runs solver
        :param silent: flag to output console data
        :return: None
        """
        self.solver_mutex.acquire()
        print('Entering thread solver')
        argv = [self.solver_type, '-case', self.case_dir]
        self.solver = BasicRunner(argv=argv, silent=silent, logname=self.solver_type)
        self.solver.start()
        if self.solver.runOK():
            if self.is_run_parallel:
                self.run_reconstruct(all_regions=True)
        else:
            raise Exception(f'{self.solver_type} run failed')
        print('Quiting thread solver')
        self.solver_mutex.release()

    def run_decompose(self, all_regions: bool = False, copy_zero: bool = False):
        """
        Runs OpenFOAM case decomposition for parallel run, described in system/decomposeParDict
        :param all_regions: flag to decompose all regions (used for multi-region cases like cht)
        :param copy_zero: copy zero state
        :return: None
        """
        if not self.case_is_decomposed:
            cmd = 'decomposePar'
            argv = [cmd, '-case', self.case_dir]
            if all_regions:
                argv.insert(1, '-allRegions')
            if copy_zero:
                argv.insert(1, '-copyZero')
            self.run_command(argv)
            self.case_is_decomposed = True

    def run_reconstruct(self, all_regions: bool = False):
        """
        Runs OpenFOAM case reconstruction after a parallel run, described in system/decomposeParDict
        :param all_regions: flag to reconstruct all regions (used for multi-region cases like cht)
        :return: None
        """
        # TODO: check if case is decomposed
        cmd = 'reconstructPar'
        argv = [cmd, '-case', self.case_dir]
        if all_regions:
            argv.insert(1, '-allRegions')
        self.run_command(argv)

    def run_block_mesh(self):
        """
        Runs OpenFOAM command to create a mesh as described in system/blockMeshDict
        :return: None
        """
        cmd = 'blockMesh'
        argv = [cmd, '-case', self.case_dir]
        self.run_command(argv)

    def run_snappy_hex_mesh(self):
        """
        Runs OpenFOAM command to snap additional mesh to a background mesh as described in system/snappyHexMeshDict
        :return: None
        """
        self.snappy_dict.save()
        cmd = 'snappyHexMesh'
        argv = [cmd, '-case', self.case_dir, '-overwrite']
        self.run_command(argv, is_parallel=self.is_setup_parallel, cores=self.num_of_cores)

    def run_split_mesh_regions(self, cell_zones_only: bool = False):
        """
        Runs OpenFOAM command to split mesh regions for a produced mesh
        :param cell_zones_only: TODO: look it up :)
        :return: None
        """
        cmd = 'splitMeshRegions'
        argv = [cmd, '-case', self.case_dir, '-overwrite']
        if cell_zones_only:
            argv.insert(1, '-cellZonesOnly')
        self.run_command(argv, is_parallel=self.is_setup_parallel, cores=self.num_of_cores)

    def run_setup_cht(self):
        """
        Runs OpenFOAM command to setup CHT, which copies data from case/templates folder
        :return: None
        """
        cmd = 'foamSetupCHT'
        argv = [cmd, '-case', self.case_dir]
        self.run_command(argv, is_parallel=self.is_setup_parallel, cores=self.num_of_cores)

    def get_boundary_conditions(self):
        """
        Gets initial boundary conditions for current case
        :return: None
        """
        fields_dir = os.listdir(f'{self.case_dir}/0')
        region_dirs = [obj for obj in fields_dir if os.path.isdir(f'{self.case_dir}/0/{obj}')]
        # Check if there are any folders in initial boundary dir
        # If there folders there, then the case is multi-regional
        if any(region_dirs):
            for region in region_dirs:
                self.boundaries.update({region: {}})
                region_dir = os.listdir(f'{self.case_dir}/0/{region}')
                for field in region_dir:
                    cls_instance = BoundaryCondition(field, self.case_dir, region=region)
                    if cls_instance:
                        self.boundaries[region].update({field: cls_instance})
                    # cls_obj = get_bc_class(field)
                    # if cls_obj:
                    #     cls_instance = cls_obj(self.case_dir, region=region)
                    #     self.boundaries[region].update({field: cls_instance})
        else:
            for field in fields_dir:
                cls_instance = BoundaryCondition(field, self.case_dir)
                if cls_instance:
                    self.boundaries.update({field: cls_instance})
                # cls_obj = get_bc_class(field)
                # if cls_obj:
                #     cls_instance = cls_obj(self.case_dir)
                #     self.boundaries.update({field: cls_instance})

    @abstractmethod
    def setup(self):
        """
        Setups case, should be overridden by child classes
        :return: None
        """
        raise NotImplementedError('Setup method is not implemented!')

    def start_solving(self):
        """
        Starts OpenFOAM solver thread or process
        :return:
        """
        if self.is_run_parallel:
            self.run_decompose(all_regions=True, copy_zero=True)
            self.solver_process = Process(target=self.run_solver_parallel, args=(True,))
            self.solver_process.start()
        else:
            self.solver_thread = Thread(target=self.run_solver, daemon=True)
            self.solver_thread.start()

    def stop_solving(self):
        """
        Stops OpenFOAM solver
        :return: None
        """
        if self.is_run_parallel:
            self.solver_process.terminate()
            # FIXME: somehow get when the process is really terminated and only then proceed
            time.sleep(1)  # Safe delay to make sure a full stop happened
        else:
            self.solver.stopWithoutWrite()
        self.solver_mutex.acquire()
        self.solver_mutex.release()

    def run(self):
        """
        Runs solver and monitor threads
        :return: None
        """
        self.start_solving()
        self.probe_parser = ProbeParser(self.case_dir)
        self.probe_parser.start()
        if self.solver_is_blocking:
            self.solver_mutex.acquire()
            self.solver_mutex.release()

    def stop(self):
        """
        Stops solver and monitor threads
        :return: None
        """
        self.probe_parser.stop()
        self.stop_solving()
