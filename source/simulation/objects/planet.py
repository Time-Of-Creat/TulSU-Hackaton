from source.simulation.objects.object import Object


class Planet(Object):
    CAN_HAVE_CHILDREN = True
    UI_ICON_COLOR = "#ff0000"
    def __init__(self, name: str, parent = None):
        super().__init__(name, parent)
