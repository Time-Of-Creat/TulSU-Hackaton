import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from source.view.models.scene_objects import SceneModel, SceneObject
from source.view.controllers.simulation_controller import SimulationController


class HierarchyPanel(ttk.Frame):
    """
    Иерархия объектов в стиле игрового движка.
    Поддерживает добавление и удаление координатных плоскостей,
    выбор объектов и контекстное меню.
    """
    def __init__(self, parent, model: SceneModel, controller: SimulationController,
                 on_select_callback: Callable[[Optional[SceneObject]], None], *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.model = model
        self.controller = controller
        self.on_select_callback = on_select_callback
        self.selected_obj_id: Optional[str] = None

        self._build_ui()
        self.refresh_tree()

    def _build_ui(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=4, pady=(4, 2))

        lbl_title = ttk.Label(
            header_frame,
            text="Иерархия объектов",
            font=("Segoe UI", 9, "bold")
        )
        lbl_title.pack(side=tk.LEFT)

        btn_add_plane = ttk.Button(
            header_frame,
            text="+ Plane",
            width=7,
            command=self._on_quick_add_plane
        )
        btn_add_plane.pack(side=tk.RIGHT)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("type",),
            show="tree headings",
            selectmode="browse"
        )
        self.tree.heading("#0", text="Объект", anchor=tk.W)
        self.tree.heading("type", text="Тип", anchor=tk.W)
        self.tree.column("#0", stretch=True, minwidth=140, width=170)
        self.tree.column("type", stretch=False, minwidth=70, width=80)

        scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Button-3>", self._on_right_click)

        self.context_menu = tk.Menu(self, tearoff=0)

    def refresh_tree(self, select_id: Optional[str] = None):
        self.tree.delete(*self.tree.get_children())
        all_objects = self.model.get_all()

        target_item = None
        for obj in all_objects:
            type_label = "Планета" if obj.obj_type == "planet" else "Плоскость"
            display_text = f"{obj.icon}  {obj.name}"
            item_id = self.tree.insert(
                "",
                tk.END,
                iid=obj.id,
                text=display_text,
                values=(type_label,)
            )
            if select_id and obj.id == select_id:
                target_item = item_id

        if target_item:
            self.tree.selection_set(target_item)
            self.tree.focus(target_item)
        elif all_objects and not self.selected_obj_id:
            first_id = all_objects[0].id
            self.tree.selection_set(first_id)
            self.tree.focus(first_id)

    def update_item_name(self, obj_id: str, new_name: str):
        obj = self.model.get_by_id(obj_id)
        if obj and self.tree.exists(obj_id):
            self.tree.item(obj_id, text=f"{obj.icon}  {new_name}")

    def _on_tree_select(self, event=None):
        selected = self.tree.selection()
        if selected:
            obj_id = selected[0]
            self.selected_obj_id = obj_id
            obj = self.model.get_by_id(obj_id)
            self.on_select_callback(obj)
        else:
            self.selected_obj_id = None
            self.on_select_callback(None)

    def _on_right_click(self, event):
        row_id = self.tree.identify_row(event.y)
        self.context_menu.delete(0, tk.END)

        if row_id:
            self.tree.selection_set(row_id)
            self.tree.focus(row_id)
            self.selected_obj_id = row_id
            obj = self.model.get_by_id(row_id)
            self.on_select_callback(obj)

            plane_menu = tk.Menu(self.context_menu, tearoff=0)
            plane_menu.add_command(label="Плоскость XY", command=lambda: self._add_plane_action("XY"))
            plane_menu.add_command(label="Плоскость XZ", command=lambda: self._add_plane_action("XZ"))
            plane_menu.add_command(label="Плоскость YZ", command=lambda: self._add_plane_action("YZ"))

            self.context_menu.add_cascade(label="➕ Добавить плоскость (Plane)", menu=plane_menu)
            self.context_menu.add_separator()

            if obj and obj.can_delete:
                self.context_menu.add_command(
                    label=f"🗑 Удалить \"{obj.name}\"",
                    command=lambda: self._delete_plane_action(obj.id)
                )
            else:
                self.context_menu.add_command(
                    label="🚫 Удаление планет запрещено",
                    state=tk.DISABLED
                )
        else:
            plane_menu = tk.Menu(self.context_menu, tearoff=0)
            plane_menu.add_command(label="Плоскость XY", command=lambda: self._add_plane_action("XY"))
            plane_menu.add_command(label="Плоскость XZ", command=lambda: self._add_plane_action("XZ"))
            plane_menu.add_command(label="Плоскость YZ", command=lambda: self._add_plane_action("YZ"))

            self.context_menu.add_cascade(label="➕ Добавить плоскость (Plane)", menu=plane_menu)

        self.context_menu.post(event.x_root, event.y_root)

    def _on_quick_add_plane(self):
        self._add_plane_action("XY")

    def _add_plane_action(self, orientation: str):
        plane = self.model.add_plane(orientation=orientation)
        self.refresh_tree(select_id=plane.id)
        self.controller.on_plane_added(plane)

    def _delete_plane_action(self, plane_id: str):
        success = self.model.remove_object(plane_id)
        if success:
            self.selected_obj_id = None
            self.refresh_tree()
            self.controller.on_plane_removed(plane_id)
            sel = self.tree.selection()
            if sel:
                self.on_select_callback(self.model.get_by_id(sel[0]))
            else:
                self.on_select_callback(None)
