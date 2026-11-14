from .objects.object import Object
from .objects.planet import Planet
from .objects.plane import Plane
from .objects.builtin_types.coords2 import Coords2


class Instance:
    def __init__(self):
        self.objects: list[Object] = []
        self._add_temporary_demo_objects()

    def _add_temporary_demo_objects(self):
        sun = Planet("Солнце", mass=1000)
        sun.color = "#FFB703"
        earth = Planet("Земля", mass=1)
        earth.color = "#219EBC"
        mars = Planet("Марс", mass=0.1)
        mars.color = "#FB8500"

        sun.local_position = Coords2(0, 0)

        earth.local_position = Coords2(90, 0)
        earth.velocity = Coords2(0, 1.5)

        mars.local_position = Coords2(-140, 0)
        mars.velocity = Coords2(0, -1.1)

        self.objects.extend([sun, earth, mars])

    def process_step(self, dt: float):
        for planet in self.get_all_planets():
            self.process_planet_gravity(planet)

        for obj in self.objects:
            obj.process_step(dt)

    def get_all_objects(self) -> list[Object]:
        result = []

        def visit(obj):
            result.append(obj)
            for child in getattr(obj, "children", []):
                visit(child)

        for obj in self.objects:
            visit(obj)
        return result

    def get_object_by_id(self, obj_id: str) -> Object | None:
        for obj in self.get_all_objects():
            if getattr(obj, "id", None) == obj_id:
                return obj
        return None

    def get_all_planets(self):
        planets = []
        for obj in self.get_all_objects():
            if isinstance(obj, Planet):
                planets.append(obj)
        return planets

    def process_planet_gravity(self, planet):
        for planet_2 in self.get_all_planets():
            if planet is not planet_2:
                planet.calculate_gravity(planet_2)

    def remove_object(self, obj_id: str) -> bool:
        obj = self.get_object_by_id(obj_id)
        if not obj:
            return False
        if getattr(obj, "parent", None) is not None:
            if obj in obj.parent.children:
                obj.parent.children.remove(obj)
                obj.parent = None
                return True
        elif obj in self.objects:
            self.objects.remove(obj)
            return True
        return False

    def add_plane(self, name: str = "Плоскость XY", orientation: str = "XY", parent_id: str | None = None) -> Plane:
        plane = Plane(name=name)
        plane.orientation = orientation
        if parent_id:
            parent = self.get_object_by_id(parent_id)
            if parent and getattr(parent, "CAN_HAVE_CHILDREN", True):
                parent.add_child(plane)
                return plane
        self.objects.append(plane)
        return plane
