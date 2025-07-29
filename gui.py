import bpy
import os
import zipfile
import tempfile
import re
from .gta_sa_ipl_importer import parse_ipl, place_objects

# ---------- Вспомогательные функции ----------

def scan_ipl_files(root):
    return [(os.path.join(dp, f), f)
            for dp, _, names in os.walk(root)
            for f in names if f.lower().endswith('.ipl')]

def find_dff_folder(root):
    for dp, _, names in os.walk(root):
        if any(f.lower().endswith('.dff') for f in names):
            return dp
    return ''

def safe_name(n):
    return re.sub(r'[^a-z0-9_\\-]', '_', n.lower())

# ---------- Свойства ----------

class fuckbr_ipl_item(bpy.types.PropertyGroup):
    path: bpy.props.StringProperty()
    name: bpy.props.StringProperty()

class fuckbr_props(bpy.types.PropertyGroup):
    root_path: bpy.props.StringProperty(
        name="Корневая папка",
        subtype='DIR_PATH',
        update=lambda self, ctx: self.update_list()
    )
    ipl_items: bpy.props.CollectionProperty(type=fuckbr_ipl_item)
    ipl_enum: bpy.props.EnumProperty(
        name="IPL файл",
        items=lambda self, ctx: [(it.path, it.name, "") for it in self.ipl_items] if self.ipl_items else []
    )
    preserve_transforms: bpy.props.BoolProperty(
        name="Сохранять трансформации",
        description="Сохраняет позицию и поворот при экспорте",
        default=False
    )
    export_format: bpy.props.EnumProperty(
        name="Формат экспорта",
        items=[('FBX', 'fbx', ''), ('DFF', 'dff', '')],
        default='FBX'
    )

    def update_list(self):
        self.ipl_items.clear()
        if os.path.isdir(self.root_path):
            for p, n in scan_ipl_files(self.root_path):
                it = self.ipl_items.add()
                it.path, it.name = p, n
            self.ipl_enum = self.ipl_items[0].path if self.ipl_items else ''

# ---------- Операторы ----------

class FUCKBR_OT_import_ipl(bpy.types.Operator):
    bl_idname = "fuckbr.import_ipl"
    bl_label = "Импортировать IPL"

    def execute(self, context):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        props = context.scene.fuckbr_props
        ipl_path = props.ipl_enum
        if not os.path.exists(ipl_path):
            self.report({'ERROR'}, "IPL файл не найден")
            return {'CANCELLED'}

        dff_folder = find_dff_folder(props.root_path)
        if not dff_folder:
            self.report({'ERROR'}, "Папка с DFF не найдена")
            return {'CANCELLED'}

        objs = parse_ipl(ipl_path)
        place_objects(objs, dff_folder)

        for area in context.window.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'SOLID'
                        space.shading.color_type = 'TEXTURE'
                        space.shading.show_specular_highlight = False
                        space.shading.show_object_outline = False

        self.report({'INFO'}, f"Импортировано объектов: {len(objs)}")
        return {'FINISHED'}

class FUCKBR_OT_export_zip(bpy.types.Operator):
    bl_idname = "fuckbr.export_zip"
    bl_label = "Экспорт в .zip"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        props = context.scene.fuckbr_props
        sel = context.selected_objects
        if not sel:
            self.report({'ERROR'}, "Нет выбранных объектов")
            return {'CANCELLED'}

        tmp = tempfile.mkdtemp()
        files = []

        # Сохраняем текстуры
        for obj in sel:
            for slot in obj.material_slots:
                mat = slot.material
                if mat and mat.node_tree:
                    for node in mat.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image and node.image.has_data:
                            name = safe_name(os.path.splitext(node.image.name)[0])
                            path = os.path.join(tmp, f"{name}.png")
                            node.image.filepath_raw = path
                            node.image.file_format = 'PNG'
                            node.image.save()
                            files.append(path)

        # Сохраняем модель
        fmt = props.export_format.lower()
        name = safe_name(sel[0].name)
        model_path = os.path.join(tmp, f"{name}.{fmt}")

        if fmt == 'fbx':
            bpy.ops.export_scene.fbx(
                filepath=model_path,
                use_selection=True,
                apply_unit_scale=False,
                bake_space_transform=not props.preserve_transforms,
                use_space_transform=not props.preserve_transforms,
                global_scale=1.0
            )
        else:
            bpy.ops.export_dff.scene(
                filepath=model_path,
                only_selected=True,
                preserve_positions=props.preserve_transforms,
                preserve_rotations=props.preserve_transforms
            )

        files.append(model_path)

        out = self.filepath or os.path.join(os.path.expanduser("~"), "Desktop", f"{name}.zip")
        if not out.lower().endswith('.zip'):
            out += '.zip'

        with zipfile.ZipFile(out, 'w') as z:
            for f in files:
                z.write(f, os.path.basename(f))

        self.report({'INFO'}, f"Экспорт завершён: {out}")
        return {'FINISHED'}

    def invoke(self, context, event):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        name = safe_name(context.selected_objects[0].name) if context.selected_objects else "export"
        self.filepath = os.path.join(desktop, f"{name}.zip")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class FUCKBR_OT_clean_dff(bpy.types.Operator):
    bl_idname = "fuckbr.clean_dff"
    bl_label = "Очистить DFF"
    bl_description = "Удаляет коллизии, LOD'ы, пустышки и лишние колёса"

    def execute(self, context):
        logs = []
        objs = list(bpy.data.objects)
        world_matrices = {o.name: o.matrix_world.copy() for o in objs}
        empty_names = [o.name for o in objs if o.type == 'EMPTY']

        # Удаление коллизий и LOD'ов
        for o in objs:
            lname = o.name.lower()
            if any(tag in lname for tag in ("colmesh", "colsphere")) or lname.endswith("vlo"):
                bpy.data.objects.remove(o, do_unlink=True)
                logs.append(f"Удалено: {o.name}")

        # Удаление и замена колёс
        mesh_data = None
        for o in list(bpy.data.objects):
            if o.name.startswith("wheel") and "_" not in o.name and o.type == 'MESH':
                mesh_data = o.data
                bpy.data.objects.remove(o, do_unlink=True)
                logs.append(f"Удалено колесо: {o.name}")

        if mesh_data:
            for name in empty_names:
                if name.startswith("wheel_"):
                    dummy = bpy.data.objects.get(name)
                    if not dummy:
                        continue
                    new = bpy.data.objects.new(f"wheel_{name}", mesh_data)
                    new.matrix_world = dummy.matrix_world.copy()
                    if name.startswith("wheel_l"):
                        sx, sy, sz = new.scale
                        new.scale = (-sx, sy, sz)
                    context.collection.objects.link(new)
                    logs.append(f"Скопировано колесо: {name}")

        # Удаление пустышек
        for name in empty_names:
            empty = bpy.data.objects.get(name)
            if empty:
                for child in list(empty.children):
                    child.parent = None
                bpy.data.objects.remove(empty, do_unlink=True)
                logs.append(f"Удалена пустышка: {name}")

        # Восстановление матриц
        for name, mat in world_matrices.items():
            o = bpy.data.objects.get(name)
            if o:
                o.matrix_world = mat

        for msg in logs:
            self.report({'INFO'}, msg)

        return {'FINISHED'}

# ---------- UI Панель ----------

class FUCKBR_PT_panel(bpy.types.Panel):
    bl_label = "fuckbr tools"
    bl_idname = "FUCKBR_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "fuckbr"

    def draw(self, context):
        layout = self.layout
        props = context.scene.fuckbr_props

        box = layout.box()
        box.label(text="Импорт карты", icon='IMPORT')
        box.prop(props, "root_path")
        if props.ipl_enum:
            box.prop(props, "ipl_enum", text="IPL")
            box.operator("fuckbr.import_ipl")
        else:
            box.label(text="IPL не найден")

        box = layout.box()
        box.label(text="Экспорт", icon='EXPORT')
        box.prop(props, "preserve_transforms")
        box.prop(props, "export_format")
        box.operator("fuckbr.export_zip")

        box = layout.box()
        box.label(text="Очистка DFF", icon='TRASH')
        box.operator("fuckbr.clean_dff", text="Очистить DFF")

# ---------- Регистрация ----------

classes = [
    fuckbr_ipl_item,
    fuckbr_props,
    FUCKBR_OT_import_ipl,
    FUCKBR_OT_export_zip,
    FUCKBR_OT_clean_dff,
    FUCKBR_PT_panel,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.fuckbr_props = bpy.props.PointerProperty(type=fuckbr_props)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.fuckbr_props

if __name__ == "__main__":
    register()
