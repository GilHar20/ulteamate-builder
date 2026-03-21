bl_info = {
    "name": "BlenderRail",
    "version": (0, 5, 0),
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
from . import controlpanel
from . import ifcimporter
from . import viewportgui

from . import addon_updater_ops



#===================================
    # --- Addon Updater ---
#===================================
@addon_updater_ops.make_annotations
class SetupAutoPreferences(bpy.types.AddonPreferences):
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

    def draw(self, context):
        layout = self.layout
        
        # Update section
        box = layout.box()
        box.label(text="Update Addon", icon='FILE_REFRESH')
        
        # Display current version
        row = box.row()
        row.label(text=f"Current Version: {bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}")
        
        # Display repository info
        row = box.row()
        row.label(text=f"Repository: {bl_info['git_url']}")
        
        row = box.row()
        row.label(text=f"Branch: {bl_info['git_branch']}")
        
        # Documentation links
        box = layout.box()
        box.label(text="Documentation & Support", icon='HELP')
        
        row = box.row()
        row.operator("wm.url_open", text="GitHub Repository", icon='URL').url = bl_info['doc_url']
        
        row = box.row()
        row.operator("wm.url_open", text="Report Issues", icon='URL').url = bl_info['tracker_url']

        # Addon updater UI - this provides the update functionality
        addon_updater_ops.update_settings_ui(self, context)
        addon_updater_ops.update_notice_box_ui(self, context)



#===================================
    # --- Registration ---
#===================================

def register():
    addon_updater_ops.make_annotations(SetupAutoPreferences)  # Avoid blender 2.8 warnings
    bpy.utils.register_class(SetupAutoPreferences)
    
    addon_updater_ops.register(bl_info)

    ifcimporter.register()
    controlpanel.register()
    viewportgui.register()

def unregister():
    viewportgui.unregister()
    controlpanel.unregister()
    ifcimporter.unregister()

    addon_updater_ops.unregister()
    bpy.utils.unregister_class(SetupAutoPreferences)



if __name__ == "__main__":
    register()