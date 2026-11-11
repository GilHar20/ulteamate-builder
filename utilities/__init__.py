import bpy



from . import asset_library_setup
from . import find_node_group
from . import preferences

classes = [
    preferences.UTMBUILDER_Preferences,
    asset_library_setup.UTMBUILDER_OT_open_addon_preferences,
    asset_library_setup.UTMBUILDER_OT_setup_asset_library,
    find_node_group.UTMBUILDER_OT_find_node_group,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    asset_library_setup.ensure_default_asset_library_path_pref()
    asset_library_setup.sync_asset_library_exists_from_filepaths()


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)