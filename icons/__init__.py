import os

import bpy.utils.previews


preview_collections = {}


def register():
    pcoll = bpy.utils.previews.new()
    icons_dir = os.path.dirname(__file__)
    pcoll.load(
        "panel_logo",
        os.path.join(icons_dir, "ULTEAMMATE-Builder_IconSmall_01.png"),
        "IMAGE",
    )
    preview_collections["main"] = pcoll


def unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
