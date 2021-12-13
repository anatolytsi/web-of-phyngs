import traceback
from os import kill
from signal import SIGINT
from threading import Thread, Lock

import PyFoam.Error
import psutil


def default_error_catcher(text):
    raise Exception(text)


PyFoam.Error.debug = lambda *text: None
PyFoam.Error.warning = lambda *text: None
PyFoam.Error.error = default_error_catcher

from PyFoam.Execution.BasicRunner import BasicRunner
from PyFoam.Execution.ParallelExecution import LAMMachine


class RunFailed(Exception):
    pass


def error_callback(error: BaseException):
    """OpenFoam commands error callback"""
    tb = error.__traceback__
    traceback.print_exception(type(error), error, tb)


def run_error_catcher(func):
    """
    OpenFOAM interface error catching decorator
    Calls attached callback if error was caught
    :param func: function to decorate
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (RunFailed, Exception) as e:
            error = e
        error_callback(error)

    return wrapper


def _check_runner_errors(command, solver):
    """Check if errors appeared after running command"""
    if not solver.runOK():
        if solver.fatalError:
            error = f'fatal error'
        elif solver.fatalFPE:
            error = f'fatal FPE'
        elif solver.fatalStackdump:
            error = f'fatal stack dump'
        else:
            error = 'unknown error'
        raise RunFailed(f'{command} run failed with {error}: {solver.data["errorText"]}')


class BasicRunnerWrapper(BasicRunner):
    def __init__(self, *args, **kwargs):
        self.running = False
        super(BasicRunnerWrapper, self).__init__(*args, **kwargs)

    def kill(self, *args, **kwargs):
        """Kills a thread if it is stuck"""
        try:
            self.run.run.send_signal(SIGINT)
            self.run._stop()
        except AssertionError:
            pass

    def start(self):
        """Starts executing command"""
        self.running = True
        super(BasicRunnerWrapper, self).start()
        self.running = False


class PyFoamCmd(BasicRunnerWrapper):
    def __init__(self, argv, silent=True, is_parallel: bool = False, cores: int = 1, **kwargs):
        self.logname = argv[0]
        self.silent = silent
        self.argv = argv
        if is_parallel:
            self.argv = ['mpirun', '-np', str(cores)] + argv + ['-parallel']
        super(PyFoamCmd, self).__init__(argv=self.argv, silent=self.silent, logname=self.logname, **kwargs)

    @run_error_catcher
    def start(self):
        """Starts executing command"""
        super(PyFoamCmd, self).start()
        _check_runner_errors(self.logname, self)


class PyFoamSolver(Thread):
    def __init__(self, solver_type: str, case_dir: str, lock: Lock, is_parallel: bool = False, cores: int = 1,
                 silent=True, **kwargs):
        argv = [solver_type, '-case', case_dir]
        lam = None
        if is_parallel:
            lam = LAMMachine(nr=cores)
        self._solve = False
        self._lock = lock
        self._parallel = is_parallel
        self._solver_type = solver_type
        self._solver = BasicRunnerWrapper(argv=argv, silent=silent, logname=solver_type, lam=lam, **kwargs)
        super(PyFoamSolver, self).__init__(daemon=True)

    @run_error_catcher
    def run(self):
        """Solving thread"""
        with self._lock:
            print('Entering solver thread')
            self._solver.start()
            _check_runner_errors(self._solver_type, self._solver)
            print('Quiting solver thread')

    def stop(self, signal):
        """Stops solving"""
        pid = self._solver.run.threadPid
        if self._parallel:
            mpi_pid = pid
            success = False
            while not success:
                try:
                    process = psutil.Process(mpi_pid)
                    process_name = process.name()
                    # print(f'Found process {process_name} with pid {mpi_pid}')
                    if process_name == 'mpirun':
                        success = True
                    else:
                        mpi_pid += 1
                except Exception:
                    mpi_pid += 1
            # NOTE: threadPid is only an ID of a pipe, but the mpirun itself is other thread
            kill(mpi_pid, signal)
        else:
            # NOT TESTED YET
            kill(self._solver.run.threadPid, signal)

    def kill(self):
        """Kill solving thread"""
        self._solver.run.run.send_signal(SIGINT)
        # self._solver.kill()
        self._solver = None
        try:
            self._stop()
        except AssertionError:
            pass
