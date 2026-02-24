bl_info = {
    "name": "BlenderRail",
    "author": "Gilad Harnik",
    "description": "A plugin for architectural visualizations",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "View3D > Tool Shelf",
    "category": "3D View",
}

import bpy

from . import controlpanel



def register():
    controlpanel.register()


def unregister():
    controlpanel.unregister()



if __name__ == "__main__":
    register()