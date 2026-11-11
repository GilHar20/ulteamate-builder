import os
import shutil

import bpy


FILEPATHS_ASSET_LIBRARY_NAME = "ULTEAMMATE"
CUSTOM_LIBRARY_FOLDER_NAME = "ulteammate_assets"
DEFAULT_USER_LIBRARY_NAMES = frozenset({"Default", "User Library", "Assets"})


def addon_shipped_assets_directory():
    """Directory inside the addon that ships .blend files (copy source only)."""
    addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(addon_root, "assets")


def default_user_asset_library_directory():
    """Blender's default local asset library (e.g. Documents/Blender/Assets)."""
    libs = bpy.context.preferences.filepaths.asset_libraries
    for lib in libs:
        if lib.name in DEFAULT_USER_LIBRARY_NAMES and (lib.path or "").strip():
            return _normalize_directory(lib.path)

    home = os.path.expanduser("~")
    for candidate in (
        os.path.join(home, "Documents", "Blender", "Assets"),
        os.path.join(home, "Blender", "Assets"),
    ):
        if os.path.isdir(candidate):
            return _normalize_directory(candidate)

    return _normalize_directory(os.path.join(home, "Documents", "Blender", "Assets"))


def _addon_module_name():
    return __name__.split(".")[0]


def _addon_preferences():
    addon = bpy.context.preferences.addons.get(_addon_module_name())
    if addon is None:
        return None
    return addon.preferences


def _normalize_directory(path):
    return os.path.normpath(bpy.path.abspath(path))


def _paths_equal(path_a, path_b):
    if not path_a or not path_b:
        return False
    a = os.path.normcase(_normalize_directory(path_a))
    b = os.path.normcase(_normalize_directory(path_b))
    return a == b


def _pref_asset_library_root(prefs):
    path = (prefs.asset_library_path or "").strip()
    if not path:
        return default_user_asset_library_directory()
    return _normalize_directory(path)


def uses_default_user_library_location(prefs):
    """True when using Blender's default user asset library (no ulteammate_assets subfolder)."""
    return _paths_equal(_pref_asset_library_root(prefs), default_user_asset_library_directory())


def uses_bundled_library_location(prefs):
    return uses_default_user_library_location(prefs)


def resolve_asset_library_directory(prefs):
    if uses_default_user_library_location(prefs):
        return default_user_asset_library_directory()
    parent = _normalize_directory(prefs.asset_library_path)
    return os.path.join(parent, CUSTOM_LIBRARY_FOLDER_NAME)


def _iter_bundled_blend_sources():
    shipped = _normalize_directory(addon_shipped_assets_directory())
    if not os.path.isdir(shipped):
        return
    for root, dirnames, filenames in os.walk(shipped):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if name.startswith(".") or not name.lower().endswith(".blend"):
                continue
            src = os.path.join(root, name)
            rel = os.path.relpath(src, shipped)
            yield src, rel


def sync_bundled_blends_to_library(target_dir):
    """Copy shipped addon .blend files into target_dir (always overwrite)."""
    target_dir = _normalize_directory(target_dir)
    shipped = _normalize_directory(addon_shipped_assets_directory())
    if _paths_equal(target_dir, shipped):
        return None

    sources = list(_iter_bundled_blend_sources())
    if not sources:
        return "No .blend files in addon assets folder: %s" % shipped

    try:
        os.makedirs(target_dir, exist_ok=True)
        for src, rel in sources:
            dst = os.path.join(target_dir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    except OSError as exc:
        return "Failed to copy asset library files: %s" % exc

    return None


def ensure_default_asset_library_path_pref():
    prefs = _addon_preferences()
    if prefs is None:
        return
    if not (prefs.asset_library_path or "").strip():
        prefs.asset_library_path = default_user_asset_library_directory()


def _find_filepaths_asset_library(library_name):
    for lib in bpy.context.preferences.filepaths.asset_libraries:
        if lib.name == library_name:
            return lib
    return None


def _apply_prefs_path_from_registered_library(lib_path):
    """Map File Paths library folder back to addon asset_library_path pref."""
    prefs = _addon_preferences()
    if prefs is None:
        return
    lib_path = _normalize_directory(lib_path)
    default_user = default_user_asset_library_directory()
    if _paths_equal(lib_path, default_user):
        prefs.asset_library_path = default_user
        return
    if os.path.basename(lib_path) == CUSTOM_LIBRARY_FOLDER_NAME:
        prefs.asset_library_path = os.path.dirname(lib_path)
        return
    prefs.asset_library_path = lib_path


def sync_asset_library_exists_from_filepaths():
    prefs = _addon_preferences()
    if prefs is None:
        return
    ensure_default_asset_library_path_pref()
    lib = _find_filepaths_asset_library(FILEPATHS_ASSET_LIBRARY_NAME)
    if lib is None or not lib.enabled:
        prefs.asset_library_exists = False
        return
    path = _normalize_directory(lib.path)
    if not os.path.isdir(path):
        return
    _apply_prefs_path_from_registered_library(path)
    prefs.asset_library_exists = True


def register_asset_library_in_filepaths():
    """Add or update Blender File Paths entry named ULTEAMMATE at the resolved library path."""
    prefs = _addon_preferences()
    if prefs is None:
        return "Addon preferences are not available"

    ensure_default_asset_library_path_pref()
    directory = resolve_asset_library_directory(prefs)
    shipped = addon_shipped_assets_directory()

    if not _paths_equal(directory, shipped):
        err = sync_bundled_blends_to_library(directory)
        if err:
            return err
    elif not os.path.isdir(directory):
        return "Asset library folder does not exist: %s" % directory

    if not os.path.isdir(directory):
        return "Asset library folder does not exist: %s" % directory

    libs = bpy.context.preferences.filepaths.asset_libraries
    lib = _find_filepaths_asset_library(FILEPATHS_ASSET_LIBRARY_NAME)
    if lib is None:
        lib = libs.new(name=FILEPATHS_ASSET_LIBRARY_NAME, directory=directory)
    else:
        lib.path = directory
    lib.enabled = True
    return None


class UTMBUILDER_OT_open_addon_preferences(bpy.types.Operator):
    bl_idname = "utmbuilder.open_addon_preferences"
    bl_label = "Open Addon Preferences"
    bl_description = "Open ULTEAMMATE Builder preferences to register the asset library"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context):
        module = _addon_module_name()
        bpy.ops.screen.userpref_show("INVOKE_DEFAULT")
        bpy.ops.preferences.addon_show(module=module)
        return {"FINISHED"}


class UTMBUILDER_OT_setup_asset_library(bpy.types.Operator):
    bl_idname = "utmbuilder.setup_asset_library"
    bl_label = "Register Asset Library in Blender"
    bl_description = (
        "Add or update the %r asset library under Edit → Preferences → File Paths"
        % FILEPATHS_ASSET_LIBRARY_NAME
    )
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context):
        err = register_asset_library_in_filepaths()
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        prefs = _addon_preferences()
        if prefs is not None:
            prefs.asset_library_exists = True
        directory = resolve_asset_library_directory(prefs)
        self.report(
            {"INFO"},
            "Asset library %r set to %s" % (FILEPATHS_ASSET_LIBRARY_NAME, directory),
        )
        return {"FINISHED"}
