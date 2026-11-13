
class Object:
    CAN_HAVE_CHILDREN = True
    UI_ICON_COLOR = "#777777"
    def __init__(self, name: str):
        self.name = name
        self.children: list[Object] = []

    def get_child(self, index: int):
        return self.children[index]

    def get_child_by_name(self, name: str):
        for child in self.children:
            if child.name == name:
                return child

    def add_child(self, obj):
        if self.CAN_HAVE_CHILDREN:
            self.children.append(obj)
