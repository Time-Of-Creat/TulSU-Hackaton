import copy

from source.simulation.objects.object import Object


class SimulationData:
    def __init__(self):
        self.objects: list[Object] = list()
        self._default = copy.deepcopy(self.__dict__)

    def _snapshot(self):
        """Сохранение дефолтного состояния - должно пересохраняться после каждого обновления конфигурации!!!"""
        self._default = copy.deepcopy(self.__dict__)

    def reset(self):
        self.__dict__.update(copy.deepcopy(self._default))
