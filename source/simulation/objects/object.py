import uuid
from typing import Dict, Any, List, Optional
from .builtin_types.coords2 import Coords2


class Object:
    CAN_HAVE_CHILDREN = True
    CONSUME_ROTATION_FROM_PARENTS = True
    CONSUME_POSITION_FROM_PARENTS = True
    UI_ICON_COLOR = "#777777"

    def __init__(self, name: str, parent=None):
        self.id = uuid.uuid4().hex[:8]
        self.name = name
        self.parent: Optional['Object'] = parent
        self.children: List['Object'] = []

        self.local_position = Coords2(0, 0)
        self.local_rotation_deg = 0.0
        self.can_delete = True
        self.obj_type = "object"
        self.icon = "📦"

    @property
    def properties(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "pos_x": self.local_position.x,
            "pos_y": self.local_position.y,
            "pos_z": 0.0,
            "rotation": self.local_rotation_deg,
        }

    def process_step(self, dt: float):
        for child in self.children:
            child.process_step(dt)

    def get_global_position(self, consume_rotation=CONSUME_ROTATION_FROM_PARENTS):
        parent_global_position = Coords2(0, 0)
        if self.parent is not None:
            parent_global_position = self.parent.get_global_position(consume_rotation)

        if consume_rotation and self.parent is not None:
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

    def remove_child(self, obj) -> bool:
        if obj in self.children:
            self.children.remove(obj)
            obj.parent = None
            return True
        return False
