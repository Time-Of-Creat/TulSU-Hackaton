import math


class Coords2:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def rotate(self, angle_deg: float):
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        new_x = self.x * cos_a - self.y * sin_a
        new_y = self.x * sin_a + self.y * cos_a

        return Coords2(new_x, new_y)

    def __add__(self, other):
        if isinstance(other, Coords2):
            return Coords2(self.x + other.x, self.y + other.y)
