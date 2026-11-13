from .builtin_types.coords2 import Coords2


class Object:
    CAN_HAVE_CHILDREN = True
    CONSUME_ROTATION_FROM_PARENTS = True
    CONSUME_POSITION_FROM_PARENTS = True
    UI_ICON_COLOR = "#777777"

    def __init__(self, name: str, parent=None):
        self.name = name
        self.parent: Object | None = parent
        self.children: list[Object] = []

        self.local_position = Coords2(0, 0)
        self.local_rotation_deg = 0

    def process_step(self, dt: float):
        for child in self.children:
            child.process_step(dt)

    def get_global_position(self, consume_rotation=CONSUME_ROTATION_FROM_PARENTS):
        parent_global_position = Coords2(0, 0)
        if self.parent is not None:
            parent_global_position = self.parent.get_global_position(consume_rotation)

        if consume_rotation:
            rotated_local_pos = self.local_position.rotate(self.parent.local_rotation_deg)
        else:
            rotated_local_pos = self.local_position

        return rotated_local_pos + parent_global_position

    def get_global_rotation(self):
        if self.parent is None:
            return self.local_rotation_deg
        return self.parent.get_global_rotation() + self.local_rotation_deg

    def get_child(self, index: int):
        return self.children[index]

    def get_child_by_name(self, name: str):
        for child in self.children:
            if child.name == name:
                return child

    def add_child(self, obj):
        if self.CAN_HAVE_CHILDREN:
            self.children.append(obj)
            obj.parent = self
