import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class SceneObject:
    id: str
    name: str
    obj_type: str
    icon: str
    can_delete: bool
    properties: Dict[str, Any] = field(default_factory=dict)


class PlanetItem(SceneObject):
    def __init__(self, name: str, mass: float, radius: float,
                 pos_x: float, pos_y: float, pos_z: float,
                 vel_x: float = 0.0, vel_y: float = 0.0, vel_z: float = 0.0,
                 color: str = "#4A90E2", is_fixed: bool = False,
                 icon: str = "🌍"):
        super().__init__(
            id=str(uuid.uuid4())[:8],
            name=name,
            obj_type="planet",
            icon=icon,
            can_delete=False,
            properties={
                "name": name,
                "mass": mass,
                "radius": radius,
                "pos_x": pos_x,
                "pos_y": pos_y,
                "pos_z": pos_z,
                "vel_x": vel_x,
                "vel_y": vel_y,
                "vel_z": vel_z,
                "color": color,
                "is_fixed": is_fixed
            }
        )


class PlaneItem(SceneObject):
    def __init__(self, name: str, orientation: str = "XY",
                 grid_step: float = 10.0, grid_size: float = 100.0,
                 line_color: str = "#7A8288", is_visible: bool = True,
                 icon: str = "📐"):
        super().__init__(
            id=str(uuid.uuid4())[:8],
            name=name,
            obj_type="plane",
            icon=icon,
            can_delete=True,
            properties={
                "name": name,
                "orientation": orientation,
                "grid_step": grid_step,
                "grid_size": grid_size,
                "line_color": line_color,
                "is_visible": is_visible
            }
        )


class SceneModel:
    def __init__(self):
        self._objects: List[SceneObject] = []
        self._plane_counter = 1
        self._init_default_scene()

    def _init_default_scene(self):
        default_plane = PlaneItem(
            name="Плоскость XY",
            orientation="XY",
            grid_step=20.0,
            grid_size=200.0,
            line_color="#6c757d"
        )
        self._objects.append(default_plane)

        sun = PlanetItem(
            name="Солнце",
            mass=1.989e30,
            radius=696340.0,
            pos_x=0.0,
            pos_y=0.0,
            pos_z=0.0,
            vel_x=0.0,
            vel_y=0.0,
            vel_z=0.0,
            color="#FFB703",
            is_fixed=True,
            icon="🌍"
        )
        earth = PlanetItem(
            name="Земля",
            mass=5.972e24,
            radius=6371.0,
            pos_x=149.6,
            pos_y=0.0,
            pos_z=0.0,
            vel_x=0.0,
            vel_y=29.78,
            vel_z=0.0,
            color="#219EBC",
            is_fixed=False,
            icon="🌍"
        )
        mars = PlanetItem(
            name="Марс",
            mass=6.417e23,
            radius=3389.0,
            pos_x=227.9,
            pos_y=0.0,
            pos_z=0.0,
            vel_x=0.0,
            vel_y=24.07,
            vel_z=0.0,
            color="#FB8500",
            is_fixed=False,
            icon="🌍"
        )

        self._objects.extend([sun, earth, mars])

    def get_all(self) -> List[SceneObject]:
        return list(self._objects)

    def get_by_id(self, obj_id: str) -> Optional[SceneObject]:
        for obj in self._objects:
            if obj.id == obj_id:
                return obj
        return None

    def add_plane(self, orientation: str = "XY") -> PlaneItem:
        self._plane_counter += 1
        name = f"Плоскость {orientation} #{self._plane_counter}"
        plane = PlaneItem(name=name, orientation=orientation)
        self._objects.append(plane)
        return plane

    def remove_object(self, obj_id: str) -> bool:
        obj = self.get_by_id(obj_id)
        if obj and obj.can_delete:
            self._objects = [o for o in self._objects if o.id != obj_id]
            return True
        return False

    def update_property(self, obj_id: str, key: str, value: Any) -> bool:
        obj = self.get_by_id(obj_id)
        if not obj:
            return False

        obj.properties[key] = value
        if key == "name":
            obj.name = str(value)
        return True
