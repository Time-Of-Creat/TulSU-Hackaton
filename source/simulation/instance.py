from .objects.object import Object
from .objects.planet import Planet
from .objects.plane import Plane
from .objects.builtin_types.coords2 import Coords2


class Instance:
    def __init__(self):
        self.objects: list[Object] = []
        self._add_temporary_demo_objects()

    def _add_temporary_demo_objects(self):
        """
        Губка удали это потом
        """
        plane = Plane("Плоскость XY")
        second_plane = Plane("Плоскость XY #2")

        sun = Planet("Солнце", mass=1000)
        earth = Planet("Земля", mass=1)
        mars = Planet("Марс", mass=0.1)

        sun.local_position = Coords2(0, 0)

        earth.local_position = Coords2(90, 0)
        earth.velocity = Coords2(0, 1.5)
        earth.add_child(second_plane)

        mars.local_position = Coords2(-140, 0)
        mars.velocity = Coords2(0, -1.1)

        self.objects.extend([plane, sun, earth, mars])

    def process_step(self, dt: float):
        for planet in self.get_all_planets():
            self.process_planet_gravity(planet)

        for obj in self.objects:
            obj.process_step(dt)

    def get_all_planets(self):
        planets = []
        for obj in self.objects:
            if isinstance(obj, Planet):
                planets.append(obj)
        return planets

    def process_planet_gravity(self, planet):
        for planet_2 in self.get_all_planets():
            planet.calculate_gravity(planet_2)
