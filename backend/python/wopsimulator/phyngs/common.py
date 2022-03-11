from threading import Lock


class Environment:
    _instances = {}

    def __new__(cls, case_dir, **kwargs):
        if case_dir in cls._instances:
            return cls._instances[case_dir]
        instance = super(Environment, cls).__new__(cls)
        cls._instances[case_dir] = instance
        return instance

    def __init__(self, case_dir, temperature: float = 293.15):
        self._lock = Lock()
        self._case_dir = case_dir
        self._temperature = temperature

    @property
    def temperature(self):
        with self._lock:
            return self._temperature

    @temperature.setter
    def temperature(self, value):
        with self._lock:
            self._temperature = value
