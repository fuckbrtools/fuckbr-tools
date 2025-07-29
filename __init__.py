bl_info = {
    "name": "fuckbr tools",
    "blender": (2, 80, 0),
    "category": "Import-Export",
    "author": "пьяный мастер разработчик | RRMODELING / RR:mods",
    "version": (2, 4, 0),
    "location": "View3D > N-Panel > fuckbr",
    "description": "Инструмент для импорта карт GTA SA, чистки моделей и экспорта в Unity / Unreal",
}

import bpy
from . import gui

def register():
    gui.register()

def unregister():
    gui.unregister()

# Опционально — перезагрузка модуля при обновлении
if "bpy" in locals():
    import importlib
    importlib.reload(gui)
