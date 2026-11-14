import uuid
from typing import Dict, Any, List, Optional
from source.simulation.objects.object import Object
from source.simulation.objects.planet import Planet
from source.simulation.objects.plane import Plane
from source.simulation.instance import Instance

# Compatibility aliases
SceneObject = Object
PlanetItem = Planet
PlaneItem = Plane


class SceneModel:
    """
    Модель сцены, связывающая объекты визуализации и симуляции с графическим интерфейсом.
    Управляет объектами симуляции (Instance), их иерархией и свойствами.
    """
    def __init__(self, backend=None):
        self.backend = backend
        self._fallback_instance: Optional[Instance] = None
        self._plane_counter = 2

    @property
    def instance(self) -> Instance:
        if self.backend and hasattr(self.backend, "simulation_data"):
            return self.backend.simulation_data.instance
        if self._fallback_instance is None:
            self._fallback_instance = Instance()
        return self._fallback_instance

    def get_root_objects(self) -> List[Object]:
        """Возвращает объекты верхнего уровня сцены."""
        lock = getattr(self.backend, "lock", None)
        if lock:
            with lock:
                return list(self.instance.objects)
        return list(self.instance.objects)

    def get_all(self) -> List[Object]:
        """Возвращает все объекты сцены (включая дочерние)."""
        lock = getattr(self.backend, "lock", None)
        if lock:
            with lock:
                return list(self.instance.get_all_objects())
        return list(self.instance.get_all_objects())

    def get_by_id(self, obj_id: str) -> Optional[Object]:
        """Поиск объекта по его уникальному ID."""
        lock = getattr(self.backend, "lock", None)
        if lock:
            with lock:
                return self.instance.get_object_by_id(obj_id)
        return self.instance.get_object_by_id(obj_id)

    def add_plane(self, orientation: str = "XY", parent_id: Optional[str] = None) -> Plane:
        """Добавляет координатную систему в сцену или как дочерний объект."""
        self._plane_counter += 1
        name = f"Координатная система #{self._plane_counter}"
        lock = getattr(self.backend, "lock", None)
        if lock:
            with lock:
                plane = self.instance.add_plane(name=name, orientation=orientation, parent_id=parent_id)
                self._update_backend_snapshot()
                return plane
        else:
            plane = self.instance.add_plane(name=name, orientation=orientation, parent_id=parent_id)
            self._update_backend_snapshot()
            return plane

    def remove_object(self, obj_id: str) -> bool:
        """Удаляет объект из сцены, если его удаление разрешено."""
        obj = self.get_by_id(obj_id)
        if not obj or not getattr(obj, "can_delete", True):
            return False

        lock = getattr(self.backend, "lock", None)
        if lock:
            with lock:
                success = self.instance.remove_object(obj_id)
                self._update_backend_snapshot()
                return success
        else:
            success = self.instance.remove_object(obj_id)
            self._update_backend_snapshot()
            return success

    def update_property(self, obj_id: str, key: str, value: Any) -> bool:
        """Обновляет свойство объекта и синхронизирует снимок дефолтного состояния."""
        lock = getattr(self.backend, "lock", None)
        if lock:
            with lock:
                return self._apply_property_update(obj_id, key, value)
        return self._apply_property_update(obj_id, key, value)

    def _apply_property_update(self, obj_id: str, key: str, value: Any) -> bool:
        obj = self.instance.get_object_by_id(obj_id)
        if not obj:
            return False

        try:
            if key == "name":
                obj.name = str(value)
            elif key == "pos_x":
                obj.local_position.x = float(value)
            elif key == "pos_y":
                obj.local_position.y = float(value)
            elif key == "vel_x" and hasattr(obj, "velocity"):
                obj.velocity.x = float(value)
            elif key == "vel_y" and hasattr(obj, "velocity"):
                obj.velocity.y = float(value)
            elif key == "mass" and hasattr(obj, "mass"):
                obj.mass = max(float(value), 0.0)
            elif key == "density" and hasattr(obj, "density"):
                obj.density = max(float(value), 1e-6)
            elif key == "is_fixed":
                obj.is_fixed = bool(value)
            elif key == "color":
                obj.color = str(value)
            elif key == "orientation":
                obj.orientation = str(value)
            elif key == "grid_step":
                obj.grid_step = max(float(value), 0.1)
            elif key == "grid_size":
                obj.grid_size = max(float(value), 1.0)
            elif key == "line_color":
                obj.line_color = str(value)
            elif key == "is_visible":
                obj.is_visible = bool(value)
            elif key == "rotation":
                obj.local_rotation_deg = float(value)
            else:
                setattr(obj, key, value)

            self._update_backend_snapshot()
            return True
        except (ValueError, TypeError):
            return False

    def _update_backend_snapshot(self):
        if self.backend and not getattr(self.backend, "running", False):
            sim_data = getattr(self.backend, "simulation_data", None)
            if sim_data and hasattr(sim_data, "_snapshot"):
                sim_data._snapshot()
