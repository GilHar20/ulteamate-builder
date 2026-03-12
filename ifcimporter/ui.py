import bpy

from .parser import check_ifcopenshell, LIBS_PATH



class BLENDERRAIL_PT_ifc_import(bpy.types.Panel):
    bl_label = "IFC Import"
    bl_idname = "VIEW3D_PT_blenderrail_ifc_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderRail"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        has_ifc = check_ifcopenshell()

        if not has_ifc:
            box = layout.box()
            box.label(text="ifcopenshell not found", icon="ERROR")
            col = box.column(align=True)
            col.label(text="Place the ifcopenshell package in:")
            col.label(text=f"  {LIBS_PATH}")
            col.separator()
            col.label(text="Expected structure:")
            col.label(text="  libs/ifcopenshell/__init__.py")
            return

        box = layout.box()
        box.label(text="Import IFC File", icon="FILE_3D")
        row = box.row()
        row.scale_y = 1.5
        row.operator(
            "blenderrail.import_ifc",
            text="Browse IFC File...",
            icon="FILEBROWSER"
        )

        infobox = layout.box()
        infobox.label(text="What gets imported:", icon="INFO")
        col = infobox.column(align=True)
        col.label(text="  Buildings  →  BlenderRail buildings")
        col.label(text="  Storeys     →  Floors (height + elevation)")
        col.label(text="  Walls         →  Curves + segments")
