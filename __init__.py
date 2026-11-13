bl_info = {
    "name": "ULTEAMMATE Builder",
    "version": (0, 8, 4),
    "blender": (5, 3, 0),
    "author": "Gilad Harnik",
    "location": "View3D > Sidebar > ULTEAMMATE > ULTEAMMATE Builder",
    "description": "Spline based procedural building toolkit",
    "category": "3D View",
    "git_url": "https://github.com/GilHar20/ulteamate-builder.git",
    "git_branch": "main",
    "git_commit": "main",
    "tracker_url": "https://github.com/GilHar20/ulteamate-builder/issues",
    "doc_url": "https://github.com/GilHar20/ulteamate-builder",
}

from . import icons
from . import main
from . import viewportgui
from . import utilities


def register():
    icons.register()
    utilities.register()
    main.register()
    viewportgui.register()


def unregister():
    viewportgui.unregister()
    main.unregister()
    utilities.unregister()
    icons.unregister()


if __name__ == "__main__":
    register()
