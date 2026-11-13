import math

from source.simulation.objects.object import Object
from .builtin_types.coords2 import Coords2

G = 6.674e-11


class Planet(Object):
    CAN_HAVE_CHILDREN = True
    UI_ICON_COLOR = "#ff0000"

    def __init__(self, name: str, mass: float = 1, parent=None):
        super().__init__(name, parent)

        self.mass = mass
        self.F = Coords2(0, 0)
        self.acceleration = Coords2(0, 0)
        self.velocity = Coords2(0, 0)

    def process_step(self, dt: float):
        super().process_step(dt)

        if self.mass != 0:
            self.acceleration = self.F / self.mass
        else:
            self.acceleration = Coords2(0, 0)

        self.velocity += self.acceleration * dt
        self.local_position += self.velocity * dt

        self.F = Coords2(0, 0)

    def calculate_gravity(self, other_planet):
        p1 = self.get_global_position()
        p2 = other_planet.get_global_position()

        r = p1.get_dist(p2)
        if r == 0:
            return

        d = p2 - p1
        f = G * self.mass * other_planet.mass / (r * r)

        self.F = self.F + Coords2(f * d.x / r, f * d.y / r)
