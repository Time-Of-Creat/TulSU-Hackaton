import copy

from source.simulation.objects.plane import Plane


class SimulationData:
    def __init__(self):
        self.plane = Plane()
        self._default = copy.deepcopy(self.__dict__)

    def _snapshot(self):
        """Сохранение дефолтного состояния - должно пересохраняться после каждого обновления конфигурации!!!"""
        self._default = copy.deepcopy(self.__dict__)

    def reset(self):
        self.__dict__.update(copy.deepcopy(self._default))
