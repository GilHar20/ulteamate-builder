import os
import bpy

from .asset_library_setup import resolve_asset_library_directory


def _addon_preferences():
    root = __name__.split(".")[0]
    return bpy.context.preferences.addons[root].preferences


def _iter_blend_paths_in_folder(folder, blend_filename=""):
    folder = bpy.path.abspath(folder)
    if not os.path.isdir(folder):
        raise RuntimeError("Cannot read asset library folder: %s" % folder)

    blend_filename = (blend_filename or "").strip()
    try:
        if blend_filename:
            path = bpy.path.abspath(os.path.join(folder, blend_filename))
            if os.path.isfile(path) and path.lower().endswith(".blend"):
                yield path
            return

        for root, dirnames, filenames in os.walk(folder):
            dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
            for name in sorted(filenames):
                if name.startswith(".") or not name.lower().endswith(".blend"):
                    continue
                yield bpy.path.abspath(os.path.join(root, name))
    except OSError as exc:
        raise RuntimeError("Cannot read asset library folder: %s" % exc) from exc


def link_gn_from_library(node_group_name, blend_filename=""):
    if not node_group_name:
        return None, "Node group name is empty"

    existing = bpy.data.node_groups.get(node_group_name)
    if existing is not None:
        return existing, None

    prefs = _addon_preferences()
    folder = resolve_asset_library_directory(prefs)

    try:
        blend_paths = list(_iter_blend_paths_in_folder(folder, blend_filename))
    except RuntimeError as exc:
        return None, str(exc)

    if not blend_paths:
        if blend_filename:
            return None, "Blend file %r not found under %s" % (blend_filename, folder)
        return None, "No .blend files in asset library folder %s" % folder

    for blend_path in blend_paths:
        with bpy.data.libraries.load(blend_path, link = True) as (data_from, data_to):
            if node_group_name not in data_from.node_groups:
                continue
            data_to.node_groups = [node_group_name]

        node_group = bpy.data.node_groups.get(node_group_name)
        if not node_group:
            return None, "Failed to link node group %r from %s" % (node_group_name, blend_path)
        return node_group, None

    return (
        None,
        "Node group %r not found in any .blend under %s"
        % (node_group_name, folder),
    )


class UTMBUILDER_OT_find_node_group(bpy.types.Operator):
    bl_idname = "utmbuilder.find_node_group"
    bl_label = "Link Node Group from Asset Library"
    bl_options = {"REGISTER", "INTERNAL"}

    node_group_name: bpy.props.StringProperty(
        name="Node Group Name",
        description="Name of the node group to link from a library .blend file",
        default="Street_PRESET",
    )
    blend_filename: bpy.props.StringProperty(
        name="Blend File Name",
        description=(
            "If empty, all .blend files in the asset library folder are searched. "
            "If set, only this file is used"
        ),
        default="",
    )

    def execute(self, context):
        node_group, err = link_gn_from_library(
            self.node_group_name,
            self.blend_filename,
        )
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}
