bl_info = {
    "name": "ULTEAMMATE Builder",
    "version": (0, 8, 0),
    "blender": (5, 3, 0),
    "author": "Gilad Harnik",
    "location": "View3D > Sidebar > ULTEAMMATE > ULTEAMMATE Builder",
    "description": "Spline based procedural building toolkit",
    "category": "3D View",
    "git_url": "https://github.com/GilHar20/ulteamate-builder.git",
    "git_branch": "main",
    "git_commit": "main",
    "tracker_url": "https://github.com/GilHar20/ulteamate-builder/issues",
    "doc_url": "https://github.com/GilHar20/ulteamate-builder",
}

import bpy

from . import icons
from . import main
from . import viewportgui
from . import utilities


class UTMBUILDER_Preferences(bpy.types.AddonPreferences):
    bl_idname = 'ulteamate-builder'

    asset_library_name : bpy.props.StringProperty(
        name = "Asset Library",
        description = "Name of the asset library to link node groups from",
        default = "ULTEAMMATE"
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text = "Asset library", icon = "ASSET_MANAGER")
        box.prop(self, "asset_library_name")


def register():
    bpy.utils.register_class(UTMBUILDER_Preferences)

    icons.register()
    utilities.register()
    viewportgui.register()
    main.register()


def unregister():
    main.unregister()
    viewportgui.unregister()
    utilities.unregister()
    icons.unregister()

    bpy.utils.unregister_class(UTMBUILDER_Preferences)


if __name__ == "__main__":
    register()
