import bpy



class BLENDERRAIL_PT_thumbnail_panel(bpy.types.Panel):
    bl_label = "ULTeaMate Elements Managaer"
    bl_idname = "VIEW3D_PT_elements_manager"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ULTeaMate"


    def draw(self, context):
        layout = self.layout
        layout.label(text = "Thumbnail:")
        layout.operator("blenderrail.render_selected_thumbnail", icon = 'RENDER_RESULT')