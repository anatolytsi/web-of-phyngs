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
from numpy import arange

from backend.python.wopsimulator.openfoam.boundaries.boundary_conditions import BoundaryCondition
from backend.python.wopsimulator.openfoam.common.filehandling import remove_iterable_dirs, remove_dirs_with_pattern, \
    force_remove_dir, remove_files_in_dir_with_pattern, copy_tree
from backend.python.wopsimulator.openfoam.common.parsing import get_latest_time
from backend.python.wopsimulator.openfoam.constant.material_properties import MaterialProperties
from backend.python.wopsimulator.openfoam.probes.probes import ProbeParser
from backend.python.wopsimulator.openfoam.system.blockmesh import BlockMeshDict
from backend.python.wopsimulator.openfoam.system.controldict import ControlDict
from backend.python.wopsimulator.openfoam.system.decomposepar import DecomposeParDict
from backend.python.wopsimulator.openfoam.system.snappyhexmesh import SnappyHexMeshDict


class OpenFoamInterface(ABC):
    """
    OpenFOAM Interface class. Serves as a wrapper of OpenFOAM commands
    """

    def __init__(self, solver_type, path='.', blocking=True, parallel=False, cores=1, mesh_quality=50,
                 clean_limit=0, **kwargs):
        """
        OpenFOAM Interface initialization function
        :param solver_type: solver type, e.g., chtMultiRegionFoam TODO: check for solver type
        :param path: path to case dir
        :param blocking: flag for solver blocking the main thread
        :param parallel: flag for parallel run
        :param cores: number of cores used for parallel run
        :param mesh_quality: mesh quality in percents [0 - 100]
        :param clean_limit: maximum number of results before cleaning, cleans if > 0
        :param kwargs: keys used by children and not by this class
        """
        self.path = path
        self.parallel = parallel
        self.blocking = blocking
        self.cores = cores
        self.clean_limit = clean_limit
        self.control_dict = ControlDict(self.path, solver_type)
        self.decompose_dict = DecomposeParDict(self.path, self.cores, 'simple')
        self.blockmesh_dict = BlockMeshDict(self.path)
        self.blockmesh_dict.mesh_quality = mesh_quality
        self.snappy_dict = SnappyHexMeshDict(self.path)
        self.material_props = MaterialProperties(self.path)
        self.regions = []
        self.boundaries = {}
        self._is_decomposed = False
        self._solver_type = solver_type
        self._solver = None
        self._solver_thread = None
        self._solver_process = None
        self._solver_mutex = Lock()
        self._probe_parser = ProbeParser(self.path)
        self.running = False

    @property
    def cores(self):
        """
        Number of cores getter
        """
        return self._cores

    @cores.setter
    def cores(self, cores):
        """
        Number of cores setter
        :param cores: number of cores
        """
        if self.parallel:
            available_cores = cpu_count()
            if available_cores >= cores > 0:
                if cores == 1:
                    self.parallel = False
                self._cores = cores
            else:
                self._cores = available_cores
            if self._cores != 1 and self._cores % 2:
                self._cores //= 2
        else:
            self._cores = 1

    def remove_processor_dirs(self):
        """
        Removes processors folder
        :return: None
        """
        remove_iterable_dirs(self.path, prepend_str='processor')

    def remove_solution_dirs(self):
        """
        Removes solution directories folder
        :return: None
        """
        remove_iterable_dirs(self.path, exception='0')

    def remove_mesh_dirs(self):
        """
        Removes Mesh folders in all folders (e.g. polyMesh)
        :return: None
        """
        remove_dirs_with_pattern(self.path, suffix='Mesh', is_recursive=True)

    def remove_tri_surface_dir(self):
        """
        Removes tri surface folder
        :return: None
        """
        force_remove_dir(f'{self.path}/constant/triSurface')

    def remove_geometry(self):
        """Removes geometry and mesh related files"""
        self.remove_mesh_dirs()
        self.remove_tri_surface_dir()

    def remove_solutions(self):
        """Removes solutions from directory"""
        self.remove_processor_dirs()
        self.remove_solution_dirs()
        force_remove_dir(f'{self.path}/postProcessing')

    def remove_logs(self):
        """Removes logs and foam files"""
        remove_files_in_dir_with_pattern(self.path, prefix='PyFoamState.')
        remove_files_in_dir_with_pattern(self.path, prefix='log.')
        remove_files_in_dir_with_pattern(self.path, suffix='.logfile')
        remove_files_in_dir_with_pattern(self.path, suffix='.foam')
        remove_files_in_dir_with_pattern(self.path, suffix='.OpenFOAM')

    def remove_initial_boundaries(self):
        """Removes initial boundary conditions directory"""
        force_remove_dir(f'{self.path}/0')

    def clean_case(self):
        """
        Removes old results and logs in the case directory
        :return: None
        """
        self.remove_solutions()
        self.remove_logs()

    def copy_stls(self, src_sub_dir: str = 'geometry', dst_sub_dir: str = 'constant/triSurface'):
        """
        Copy STLs from geometry dir to constant/triSurface or user prefered location
        TODO: move this function to other class later!
        :param src_sub_dir: source subdirectory
        :param dst_sub_dir:
        :return: None
        """
        stls_path = f'{self.path}/{src_sub_dir}'
        path_to_copy = f'{self.path}/{dst_sub_dir}'
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
        self._solver_mutex.acquire()
        argv = ['mpirun', '-np', str(self.cores), self._solver_type, '-case', self.path, '-parallel']
        self._solver = BasicRunner(argv=argv, silent=silent, logname=self._solver_type)
        self._solver.start()
        self.stop()
        print('Process terminated')
        self._solver_mutex.release()

    def run_solver(self, silent=True):
        """
        Runs solver
        :param silent: flag to output console data
        :return: None
        """
        self._solver_mutex.acquire()
        print('Entering thread solver')
        argv = [self._solver_type, '-case', self.path]
        self._solver = BasicRunner(argv=argv, silent=silent, logname=self._solver_type)
        self._solver.start()
        if self._solver.runOK():
            if self.parallel:
                self.run_reconstruct(all_regions=True)
        else:
            raise Exception(f'{self._solver_type} run failed')
        print('Quiting thread solver')
        self._solver_mutex.release()

    def run_decompose(self, all_regions: bool = False, copy_zero: bool = False, latest_time: bool = False,
                      force: bool = False):
        """
        Runs OpenFOAM case decomposition for parallel run, described in system/decomposeParDict
        :param all_regions: flag to decompose all regions (used for multi-region cases like cht)
        :param copy_zero: copy zero state
        :param latest_time: flag to only decompose from the latest time
        :param force: flag to clear processor folders before decomposing
        :return: None
        """
        if self._is_decomposed:
            latest_time = True
            force = True
        else:
            self.decompose_dict.save()
        cmd = 'decomposePar'
        argv = [cmd, '-case', self.path]
        if all_regions:
            argv.insert(1, '-allRegions')
        if copy_zero:
            argv.insert(1, '-copyZero')
        if latest_time:
            argv.insert(1, '-latestTime')
        if force:
            argv.insert(1, '-force')
        self.run_command(argv)
        self._is_decomposed = True

    def run_reconstruct(self, all_regions: bool = False, latest_time: bool = False, fields: list = None,
                        region: str = ''):
        """
        Runs OpenFOAM case reconstruction after a parallel run, described in system/decomposeParDict
        :param all_regions: flag to reconstruct all regions (used for multi-region cases like cht)
        :param latest_time: flag to only reconstruct from the latest time
        :param fields: fields to be reconstructed, e.g., ['U', 'T', 'p']
        :param region: region to reconstruct
        :return: None
        """
        # TODO: check if case is decomposed
        cmd = 'reconstructPar'
        argv = [cmd, '-newTimes', '-case', self.path]
        if all_regions:
            argv.insert(1, '-allRegions')
        elif region:
            argv.insert(1, f'-region {region}')
        if latest_time:
            argv.insert(1, '-latestTime')
        if fields:
            argv.insert(1, f'-fields \'({" ".join(fields)})\'')
        self.run_command(argv)

    def run_block_mesh(self):
        """
        Runs OpenFOAM command to create a mesh as described in system/blockMeshDict
        :return: None
        """
        self.blockmesh_dict.save()
        cmd = 'blockMesh'
        argv = [cmd, '-case', self.path]
        self.run_command(argv)

    def run_snappy_hex_mesh(self):
        """
        Runs OpenFOAM command to snap additional mesh to a background mesh as described in system/snappyHexMeshDict
        :return: None
        """
        self.snappy_dict.save()
        cmd = 'snappyHexMesh'
        argv = [cmd, '-case', self.path, '-overwrite']
        self.run_command(argv, cores=self.cores)

    def run_split_mesh_regions(self, cell_zones: bool = False, cell_zones_only: bool = False):
        """
        Runs OpenFOAM command to split mesh regions for a produced mesh
        :param cell_zones: split additionally cellZones off into separate regions
        :param cell_zones_only: use cellZones only to split mesh into regions; do not use walking
        :return: None
        """
        cmd = 'splitMeshRegions'
        argv = [cmd, '-case', self.path, '-overwrite']
        if cell_zones:
            argv.insert(1, '-cellZones')
        if cell_zones_only:
            argv.insert(1, '-cellZonesOnly')
        self.run_command(argv, cores=self.cores)

    def run_setup_cht(self):
        """
        Runs OpenFOAM command to setup CHT, which copies data from case/templates folder
        :return: None
        """
        self.material_props.save()
        cmd = 'foamSetupCHT'
        argv = [cmd, '-case', self.path]
        self.run_command(argv, cores=self.cores)

    def run_foam_dictionary(self, path: str, entry: str, set_value: str):
        """
        Runs OpenFOAM command to change dictionary specified in the path
        :param path: path to dictionary
        :param entry: field to change
        :param set_value: value to set
        :return: None
        """
        cmd = 'foamDictionary'
        argv = [cmd, f'{self.path}/{path}', '-entry', entry, '-set', set_value]
        subprocess.Popen(argv)

    def extract_boundary_conditions(self):
        """
        Extracts initial boundary conditions for current case from files
        :return: None
        """
        fields_dir = os.listdir(f'{self.path}/0')
        region_dirs = [obj for obj in fields_dir if os.path.isdir(f'{self.path}/0/{obj}')]
        # Check if there are any folders in initial boundary dir
        # If there folders there, then the case is multi-regional
        if any(region_dirs):
            self.regions = region_dirs
            for region in region_dirs:
                self.boundaries.update({region: {}})
                region_dir = os.listdir(f'{self.path}/0/{region}')
                for field in region_dir:
                    cls_instance = BoundaryCondition(field, self.path, region=region)
                    if cls_instance:
                        self.boundaries[region].update({field: cls_instance})
        else:
            for field in fields_dir:
                cls_instance = BoundaryCondition(field, self.path)
                if cls_instance:
                    self.boundaries.update({field: cls_instance})
        self.decompose_dict.regions = self.regions

    @abstractmethod
    def setup(self):
        """
        Setups case, should be overridden by child classes
        :return: None
        """
        raise NotImplementedError('Setup method is not implemented!')

    def save_boundaries(self):
        """Saves all boundary conditions"""
        if self.regions:
            for region in self.regions:
                for field in self.boundaries[region].values():
                    field.save()
        else:
            for field in self.boundaries.values():
                field.save()

    def start_solving(self):
        """
        Starts OpenFOAM solver thread or process
        :return:
        """
        self.control_dict.save()
        self.save_boundaries()
        cleaner_thread = Thread(target=self.result_cleaner, daemon=True)
        if self.parallel:
            self.run_decompose(all_regions=True, latest_time=True, force=True)
            self._solver_process = Process(target=self.run_solver_parallel, args=(True,), daemon=True)
            self._solver_process.start()
        else:
            self._solver_thread = Thread(target=self.run_solver, daemon=True)
            self._solver_thread.start()
        self.running = True
        cleaner_thread.start()

    def stop_solving(self):
        """
        Stops OpenFOAM solver
        :return: None
        """
        if self.parallel:
            self._solver_process.terminate()
            # FIXME: somehow get when the process is really terminated and only then proceed
            time.sleep(1)  # Safe delay to make sure a full stop happened
        else:
            self._solver.stopWithoutWrite()
        self.running = False
        self._solver_mutex.acquire()
        self._solver_mutex.release()

    def result_cleaner(self):
        """Thread to clean the results periodically"""
        if not self.clean_limit:
            return
        time_path = f'{self.path}/processor0' if self.parallel else self.path
        deletion_time = 0
        margin = self.clean_limit / 2 // self.control_dict.write_interval * self.control_dict.write_interval
        while self.running:
            latest_time = get_latest_time(time_path)
            if latest_time != deletion_time and not latest_time % self.clean_limit:
                time.sleep(0.05)
                exceptions = '|'.join([str(int(val) if val.is_integer() else val)
                                       for val in arange(latest_time - margin, latest_time + margin,
                                                         self.control_dict.write_interval)])
                exceptions = exceptions.replace('.', r'\.')
                if self.parallel:
                    for core in range(0, self.cores):
                        remove_dirs_with_pattern(f'{self.path}/processor{core}', f'^(?!(?:0|{exceptions})$)\\d+')
                else:
                    remove_dirs_with_pattern(self.path, f'^(?!(?:0|{exceptions})$)\\d+')
                deletion_time = latest_time
            time.sleep(0.01)

    def run(self):
        """
        Runs solver and monitor threads
        :return: None
        """
        self.start_solving()
        self._probe_parser = ProbeParser(self.path)
        self._probe_parser.start()
        if self.blocking:
            self._solver_mutex.acquire()
            self._solver_mutex.release()

    def stop(self):
        """
        Stops solver and monitor threads
        :return: None
        """
        self._probe_parser.stop()
        self.stop_solving()
