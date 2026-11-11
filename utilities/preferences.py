import bpy

from . asset_library_setup import default_user_asset_library_directory


class UTMBUILDER_Preferences(bpy.types.AddonPreferences):
    bl_idname = 'ulteamate-builder'

    asset_library_path : bpy.props.StringProperty(
        subtype = 'DIR_PATH',
        name = "Asset Library Path",
        description = (
            "Folder for the ULTEAMMATE asset library. "
            "Uses this folder directly when set to the default bundled path; "
            "otherwise files are stored in a ulteammate_assets subfolder"
        ),
        default = default_user_asset_library_directory(),
    )

    asset_library_exists : bpy.props.BoolProperty(
        name = "Asset Library Exists",
        description = "Whether the asset library exists",
        default = False,
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()

        if self.asset_library_exists:
            box.label(text = "Asset library is set up correctly!", icon = 'INFO')
            box.prop(self, "asset_library_path", text = "Asset library Path")
            return
            
        box.label(text = "Asset library is set up properly!", icon = 'ERROR')
        box.prop(self, "asset_library_path", text = "Asset library Path")
        box.operator("utmbuilder.setup_asset_library", text = "Register in Blender File Paths", icon = "FILE_REFRESH")
