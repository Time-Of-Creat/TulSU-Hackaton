from .objects.object import Object
from .objects.planet import Planet


class Instance:
    def __init__(self):
        self.objects: list[Object] = []

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
