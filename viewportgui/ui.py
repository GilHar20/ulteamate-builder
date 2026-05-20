import bpy



class BLENDERRAIL_PT_thumbnail_panel(bpy.types.Panel):
    bl_label = "thumbnail"
    bl_idname = "VIEW3D_PT_thumbnail"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderRail"

    def draw(self, context):
        layout = self.layout
        layout.label(text = "Thumbnail:")
        layout.operator("blenderrail.render_selected_thumbnail", icon = 'RENDER_RESULT')