import time
from threading import Thread
from typing import Callable

CHECKER_SLEEP_TIME = 0.01
CHECKER_DELAY_WAIT_SCALE = 100
CHECKER_DELAY_WAIT = CHECKER_DELAY_WAIT_SCALE * CHECKER_SLEEP_TIME


class RunTimeMonitor(Thread):
    def __init__(self, enabled: bool, tolerance: int, case_runner: Callable, case_stopper: Callable,
                 time_difference_getter: Callable):
        self._enabled = enabled
        self.running = False
        self.tolerance = tolerance
        self._run_case = case_runner
        self._stop_case = case_stopper
        self._get_time_diff = time_difference_getter
        super(RunTimeMonitor, self).__init__(daemon=True)

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if not value:
            self.stop()
        self._enabled = value

    def run(self) -> None:
        previous_difference = 0
        self.running = True
        while self.running and self._enabled:
            time_difference = self._get_time_diff()
            if (previous_difference - time_difference) >= CHECKER_DELAY_WAIT:
                time.sleep(CHECKER_DELAY_WAIT)
            previous_difference = time_difference
            if time_difference >= self.tolerance:
                self._stop_case(runtime_checker=True)
            elif time_difference <= 0:
                self._run_case()
            time.sleep(CHECKER_SLEEP_TIME)

    def start(self) -> None:
        if not self._enabled:
            return
        super(RunTimeMonitor, self).__init__(daemon=True)
        super(RunTimeMonitor, self).start()

    def stop(self) -> None:
        self.running = False
