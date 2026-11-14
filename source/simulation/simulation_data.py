import copy

from source.simulation.instance import Instance
from source.simulation.configuration_detector import (
    ConfigurationDetector,
    DetectionResult,
    SystemConfiguration,
)


class SimulationData:
    def __init__(self):
        self.instance = Instance()
        self.simulation_speed = 1.0
        self.detector = ConfigurationDetector(history_size=60)
        self.detection_result: DetectionResult = self.detector.last_result
        self._default = copy.deepcopy(self.__dict__)

    def _snapshot(self):
        """Сохранение дефолтного состояния - должно пересохраняться после каждого обновления конфигурации!!!"""
        self.detector.reset()
        self.detection_result = self.detector.last_result
        self._default = copy.deepcopy(self.__dict__)

    def reset(self):
        self.__dict__.update(copy.deepcopy(self._default))

    def process_instance_step(self, dt):
        self.instance.process_step(dt)
        planets = self.instance.get_all_planets()
        self.detection_result = self.detector.analyze(planets)

    @property
    def is_collision(self) -> bool:
        return self.detection_result.configuration == SystemConfiguration.COLLISION