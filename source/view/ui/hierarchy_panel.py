import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from source.view.models.scene_objects import SceneModel, SceneObject
from source.view.controllers.simulation_controller import SimulationController


class HierarchyPanel(ttk.Frame):
    """
    Иерархия объектов сцены с поддержкой вложенных дочерних элементов.
    Отображает структуру сцены (планеты и координатные системы) в виде дерева
    и синхронизируется с объектами симуляции.
    """
    def __init__(self, parent, model: SceneModel, controller: SimulationController,
                 on_select_callback: Callable[[Optional[SceneObject]], None], *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.model = model
        self.controller = controller
        self.on_select_callback = on_select_callback
        self.selected_obj_id: Optional[str] = None
        self._last_signature = None

        self._build_ui()
        self.refresh_tree()
        self._start_sync_loop()

    def _build_ui(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=4, pady=(4, 2))

        lbl_title = ttk.Label(
            header_frame,
            text="Иерархия объектов",
            font=("Segoe UI", 9, "bold")
        )
        lbl_title.pack(side=tk.LEFT)

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
        self.tree.column("type", stretch=False, minwidth=120, width=130)

        scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Button-3>", self._on_right_click)

        self.context_menu = tk.Menu(self, tearoff=0)

    def refresh_tree(self, select_id: Optional[str] = None):
        """
        Полностью перерисовывает дерево объектов с учетом родительско-дочерних связей.
        Дочерние элементы отображаются вложенными в свои родительские узлы.
        """
        self.tree.delete(*self.tree.get_children())
        root_objects = self.model.get_root_objects()

        target_item = None

        def insert_node(obj, parent_iid=""):
            nonlocal target_item
            type_label = "Планета" if getattr(obj, "obj_type", "") == "planet" else "Координатная система"
            icon = getattr(obj, "icon", "🌍" if type_label == "Планета" else "📐")
            display_text = f"{icon}  {obj.name}"

            item_id = self.tree.insert(
                parent_iid,
                tk.END,
                iid=obj.id,
                text=display_text,
                values=(type_label,),
                open=True
            )

            if select_id and obj.id == select_id:
                target_item = item_id
            elif not select_id and self.selected_obj_id and obj.id == self.selected_obj_id:
                target_item = item_id

            for child in getattr(obj, "children", []):
                insert_node(child, parent_iid=obj.id)

        for root_obj in root_objects:
            insert_node(root_obj, parent_iid="")

        self._last_signature = self._get_scene_signature()

        if target_item and self.tree.exists(target_item):
            self.tree.selection_set(target_item)
            self.tree.focus(target_item)
            self.selected_obj_id = target_item
        else:
            all_children = self.tree.get_children()
            if all_children:
                first_id = all_children[0]
                self.tree.selection_set(first_id)
                self.tree.focus(first_id)
                self.selected_obj_id = first_id
                self.on_select_callback(self.model.get_by_id(first_id))
            else:
                self.selected_obj_id = None
                self.on_select_callback(None)

    def update_item_name(self, obj_id: str, new_name: str):
        """Обновляет имя элемента в дереве без полной перерисовки."""
        obj = self.model.get_by_id(obj_id)
        if obj and self.tree.exists(obj_id):
            icon = getattr(obj, "icon", "📦")
            self.tree.item(obj_id, text=f"{icon}  {new_name}")
            self._last_signature = self._get_scene_signature()

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

            # Передаем ID родителя (row_id), чтобы добавить как дочерний
            self.context_menu.add_command(
                label="➕ Добавить координатную систему",
                command=lambda: self._on_context_add_coord_system(parent_id=row_id)
            )
            self.context_menu.add_separator()

            if obj and getattr(obj, "can_delete", True):
                self.context_menu.add_command(
                    label=f"🗑 Удалить «{obj.name}»",
                    command=lambda: self._on_context_delete_coord_system(obj.id)
                )
            else:
                self.context_menu.add_command(
                    label="🚫 Удаление планет запрещено",
                    state=tk.DISABLED
                )
        else:
            # Клик по пустому месту — parent_id=None (добавляем в корень)
            self.context_menu.add_command(
                label="➕ Добавить координатную систему",
                command=lambda: self._on_context_add_coord_system(parent_id=None)
            )

        self.context_menu.post(event.x_root, event.y_root)

    def _on_context_add_coord_system(self, parent_id: Optional[str] = None):
        """Вызывает создание координатной системы через контроллер."""
        self.controller.add_coordinate_system(parent_id)

    def _on_context_delete_coord_system(self, obj_id: str):
        """Вызывает удаление координатной системы через контроллер."""
        self.controller.remove_coordinate_system(obj_id)

    def _start_sync_loop(self):
        self._check_tree_sync()
        self.after(250, self._start_sync_loop)

    def _get_scene_signature(self):
        all_objs = self.model.get_all()
        return tuple(
            (o.id, getattr(o, "name", ""), getattr(getattr(o, "parent", None), "id", None))
            for o in all_objs
        )

    def _check_tree_sync(self):
        current_sig = self._get_scene_signature()
        if self._last_signature != current_sig:
            self._last_signature = current_sig
            self.refresh_tree(select_id=self.selected_obj_id)
