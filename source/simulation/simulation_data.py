import copy

from source.simulation.instance import Instance


class SimulationData:
    def __init__(self):
        self.instance = Instance()
        self.simulation_speed = 1.0
        self._default = copy.deepcopy(self.__dict__)

    def _snapshot(self):
        """Сохранение дефолтного состояния - должно пересохраняться после каждого обновления конфигурации!!!"""
        self._default = copy.deepcopy(self.__dict__)

    def reset(self):
        self.__dict__.update(copy.deepcopy(self._default))

    def process_instance_step(self, dt):
        self.instance.process_step(dt)
