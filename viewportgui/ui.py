import bpy



class UTMBUILDER_PT_thumbnail_panel(bpy.types.Panel):
    bl_idname = "UTMBUILDER_PT_elements_manager"
    bl_label = "ULTEAMMATE Elements Managaer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ULTEAMMATE"


    def draw(self, context):
        layout = self.layout
        layout.label(text = "Thumbnail:")
        layout.operator("utmbuilder.render_selected_thumbnail", icon = 'RENDER_RESULT')