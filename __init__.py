bl_info = {
    "name": "BlenderRail",
    "version": (0, 7, 0),
    "blender": (4, 5, 0),
    "author": "Gilad Harnik",
    "location": "View3D > Sidebar > blenderrail",
    "description": "A plugin for architectural visualizations",
    "category": "3D View",
    "git_url": "https://github.com/GilHar20/blenderrail.git",
    "git_branch": "main",
    "git_commit": "main",
    "tracker_url": "https://github.com/GilHar20/blenderrail/issues",
    "doc_url": "https://github.com/GilHar20/blenderrail",
}

import bpy
from . import main
from . import viewportgui
from . import utilities

from . import addon_updater_ops



# -----------------
# Addon Preferences
# -----------------
@addon_updater_ops.make_annotations
class BlenderRailPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    auto_check_update = bpy.props.BoolProperty(
        name="Auto-check for Update",
        description="If enabled, auto-check for updates using an interval",
        default=False)

    updater_interval_months = bpy.props.IntProperty(
        name='Months',
        description="Number of months between checking for updates",
        default=0,
        min=0)

    updater_interval_days = bpy.props.IntProperty(
        name='Days',
        description="Number of days between checking for updates",
        default=7,
        min=0,
        max=31)

    updater_interval_hours = bpy.props.IntProperty(
        name='Hours',
        description="Number of hours between checking for updates",
        default=0,
        min=0,
        max=23)

    updater_interval_minutes = bpy.props.IntProperty(
        name='Minutes',
        description="Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59)

    asset_library_name = bpy.props.StringProperty(
        name="Asset Library",
        description=(
            "Name of a library listed under Edit → Preferences → File Paths → Asset Libraries. "
            "Its root folder is used to locate your Geometry Nodes .blend file(s)"
        ),
        default="GeometryNodesModifiers"
    )

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="Asset library", icon="ASSET_MANAGER")
        box.prop(self, "asset_library_name")

        # Addon updater UI - this provides the update functionality
        addon_updater_ops.update_settings_ui(self, context)
        addon_updater_ops.update_notice_box_ui(self, context)



#===================================
    # --- Registration ---
#===================================

def register():
    '''
    addon_updater_ops.make_annotations(BlenderRailPreferences)  # Avoid blender 2.8 warnings
    bpy.utils.register_class(BlenderRailPreferences)
    '''
    
    addon_updater_ops.register(bl_info)

    utilities.register()
    main.register()
    viewportgui.register()


def unregister():
    viewportgui.unregister()
    main.unregister()
    utilities.unregister()

    '''
    addon_updater_ops.unregister()
    bpy.utils.unregister_class(BlenderRailPreferences)
    '''



if __name__ == "__main__":
    register()