"""
Thumbnail off-screen render (self-contained module).

Draws the scene with a temporary camera into a GPU off-screen buffer, reads pixels
into RAM (Blender GPU example pattern), packs an Image data-block in the .blend,
and optionally shows it in the Image Editor.
"""

from __future__ import annotations

import math
import re

import bpy
import gpu
from mathutils import Matrix, Vector


def _sanitize_image_name(base: str) -> str:
    base = re.sub(r"[^\w\-. ]+", "_", base, flags=re.UNICODE).strip()
    if not base:
        base = "Thumbnail"
    name = f"BR_Thumb_{base}"
    if name in bpy.data.images:
        i = 1
        while f"{name}.{i:03d}" in bpy.data.images:
            i += 1
        name = f"{name}.{i:03d}"
    return name


def _unique_object_name(prefix: str) -> str:
    name = prefix
    if name in bpy.data.objects:
        i = 1
        while f"{prefix}.{i:03d}" in bpy.data.objects:
            i += 1
        name = f"{prefix}.{i:03d}"
    return name


def _world_bounds_min_max(objects: list[bpy.types.Object]) -> tuple[Vector, Vector] | None:
    inf = float("inf")
    min_c = Vector((inf, inf, inf))
    max_c = Vector((-inf, -inf, -inf))
    found = False
    for obj in objects:
        for corner in obj.bound_box:
            w = obj.matrix_world @ Vector(corner)
            min_c.x = min(min_c.x, w.x)
            min_c.y = min(min_c.y, w.y)
            min_c.z = min(min_c.z, w.z)
            max_c.x = max(max_c.x, w.x)
            max_c.y = max(max_c.y, w.y)
            max_c.z = max(max_c.z, w.z)
            found = True
    if not found:
        return None
    return min_c, max_c


def _fit_camera_to_bounds(
    cam_data: bpy.types.Camera,
    cam_obj: bpy.types.Object,
    center: Vector,
    dimensions: Vector,
    ) -> None:
    """Perspective camera placed on a diagonal, looking at *center*."""
    cam_data.type = "PERSP"
    cam_data.lens = 50.0
    fov = cam_data.angle
    max_dim = max(dimensions.x, dimensions.y, dimensions.z)
    if max_dim < 1e-6:
        max_dim = 1.0
    dist = (max_dim * 0.55 * 1.25) / max(math.tan(fov * 0.5), 1e-6)
    offset = Vector((1.0, 0.85, 0.65)).normalized()
    cam_loc = center + offset * dist
    direction = center - cam_loc
    if direction.length < 1e-9:
        direction = Vector((0.0, 0.0, -1.0))
    quat = direction.to_track_quat("-Z", "Y")
    cam_obj.matrix_world = Matrix.Translation(cam_loc) @ quat.to_matrix().to_4x4()


def _find_view3d_draw_target(context: bpy.types.Context,) -> tuple[bpy.types.Area, bpy.types.SpaceView3D, bpy.types.Region] | None:
    """Return (area, SpaceView3D, WINDOW region) from the current window."""
    win = context.window
    if not win:
        return None
    for area in win.screen.areas:
        if area.type != "VIEW_3D":
            continue
        space = area.spaces.active
        if space.type != "VIEW_3D":
            continue
        for region in area.regions:
            if region.type == "WINDOW":
                return area, space, region
    return None


def _ubyte_buffer_to_pixels(buffer: gpu.types.Buffer, width: int, height: int) -> list[float]:
    """Convert UBYTE RGBA framebuffer readback to 0–1 floats for bpy.types.Image.pixels."""
    count = width * height * 4
    buffer.dimensions = count
    if hasattr(buffer, "to_list"):
        raw = buffer.to_list()
    else:
        raw = [buffer[i] for i in range(count)]
    return [v / 255.0 for v in raw]


def _capture_view3d_offscreen(
    context: bpy.types.Context,
    scene: bpy.types.Scene,
    view_layer: bpy.types.ViewLayer,
    space: bpy.types.SpaceView3D,
    region: bpy.types.Region,
    cam_obj: bpy.types.Object,
    width: int,
    height: int,
    *,
    transparent_background: bool,
    ) -> list[float]:
    """
    Draw the 3D view into a GPU off-screen buffer and read RGBA pixels into RAM.

    Uses the same readback pattern as Blender's GPU off-screen example
    (GPUOffScreen.bind → read_color → normalize UBYTE to image pixels).
    """
    depsgraph = context.evaluated_depsgraph_get()
    view_matrix = cam_obj.matrix_world.inverted()
    projection_matrix = cam_obj.calc_matrix_camera(depsgraph, x=width, y=height)

    offscreen = gpu.types.GPUOffScreen(width, height)
    try:
        with offscreen.bind():
            offscreen.draw_view3d(
                scene,
                view_layer,
                space,
                region,
                view_matrix,
                projection_matrix,
                do_color_management=True,
                draw_background=not transparent_background,
            )
            fb = gpu.state.active_framebuffer_get()
            buffer = fb.read_color(0, 0, width, height, 4, 0, "UBYTE")
    finally:
        offscreen.free()

    return _ubyte_buffer_to_pixels(buffer, width, height)


def _assign_pixels(image: bpy.types.Image, pixels: list[float]) -> None:
    try:
        image.pixels.foreach_set(pixels)
    except (TypeError, ValueError, AttributeError):
        image.pixels = pixels


class BLENDERRAIL_OT_render_selected_thumbnail(bpy.types.Operator):
    bl_idname = "blenderrail.render_selected_thumbnail"
    bl_label = "Render Selection Thumbnail"
    bl_description = (
        "Off-screen viewport render of the selected objects; saves a packed image "
        "in this .blend for use in the Image Editor"
    )
    bl_options = {"REGISTER", "UNDO"}

    resolution: bpy.props.IntProperty(
        name="Size",
        description="Square render resolution in pixels",
        default=256,
        min=64,
        max=4096,
    )
    transparent_film: bpy.props.BoolProperty(
        name="Transparent Background",
        description="Clear alpha in the thumbnail background",
        default=True,
    )
    open_image_editor: bpy.props.BoolProperty(
        name="Show in Image Editor",
        description="Assign the new image to an Image Editor area when possible",
        default=True,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return (
            context.mode == "OBJECT"
            and len(context.selected_objects) > 0
        )

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene = context.scene
        view_layer = context.view_layer
        selected = list(context.selected_objects)
        bounds = _world_bounds_min_max(selected)
        if bounds is None:
            self.report({"ERROR"}, "Could not compute bounds for selection")
            return {"CANCELLED"}

        draw_target = _find_view3d_draw_target(context)
        if draw_target is None:
            self.report({"ERROR"}, "Open a 3D Viewport window to capture the thumbnail")
            return {"CANCELLED"}
        _area, space, region = draw_target

        min_c, max_c = bounds
        center = (min_c + max_c) * 0.5
        dimensions = max_c - min_c

        orig_cam = scene.camera
        hide_viewport_backup: dict[bpy.types.Object, bool] = {}
        temp_objects: list[bpy.types.Object] = []

        try:
            for obj in scene.objects:
                hide_viewport_backup[obj] = obj.hide_viewport
                obj.hide_viewport = obj not in selected

            cam_data = bpy.data.cameras.new("BR_ThumbCamData")
            cam_obj = bpy.data.objects.new(_unique_object_name("BR_ThumbCam"), cam_data)
            scene.collection.objects.link(cam_obj)
            temp_objects.append(cam_obj)

            _fit_camera_to_bounds(cam_data, cam_obj, center, dimensions)
            scene.camera = cam_obj

            has_light = any(
                o.type == "LIGHT"
                for o in scene.objects
                if not o.hide_viewport
            )
            if not has_light:
                light_data = bpy.data.lights.new("BR_ThumbSunData", type="SUN")
                light_data.energy = 3.0
                light_obj = bpy.data.objects.new(_unique_object_name("BR_ThumbSun"), light_data)
                scene.collection.objects.link(light_obj)
                light_obj.matrix_world = Matrix.Translation(center + Vector((2.0, -4.0, 6.0)))
                light_obj.rotation_euler = (math.radians(45.0), 0.0, math.radians(25.0))
                temp_objects.append(light_obj)

            size = self.resolution
            pixels = _capture_view3d_offscreen(
                context,
                scene,
                view_layer,
                space,
                region,
                cam_obj,
                size,
                size,
                transparent_background=self.transparent_film,
            )
            if len(pixels) != size * size * 4:
                self.report({"ERROR"}, "Off-screen capture did not produce pixel data")
                return {"CANCELLED"}

            base_name = selected[0].name
            if len(selected) > 1:
                base_name = f"{base_name}_plus_{len(selected) - 1}"
            img_name = _sanitize_image_name(base_name)
            new_img = bpy.data.images.new(
                img_name,
                width=size,
                height=size,
                alpha=self.transparent_film,
            )
            _assign_pixels(new_img, pixels)
            new_img.pack()
            new_img.use_fake_user = True
            new_img.colorspace_settings.name = "sRGB"

            if self.open_image_editor:
                shown = False
                for window in context.window_manager.windows:
                    for win_area in window.screen.areas:
                        if win_area.type == "IMAGE_EDITOR":
                            win_area.spaces.active.image = new_img
                            shown = True
                            break
                    if shown:
                        break
                if not shown:
                    self.report(
                        {"INFO"},
                        f"Packed image '{new_img.name}' — open Image Editor and pick it from the image list",
                    )
                else:
                    self.report({"INFO"}, f"Packed image '{new_img.name}' and shown in Image Editor")
            else:
                self.report({"INFO"}, f"Packed image '{new_img.name}'")

            return {"FINISHED"}

        finally:
            for obj in temp_objects:
                data = obj.data
                bpy.data.objects.remove(obj, do_unlink=True)
                if data is not None and data.users == 0:
                    if isinstance(data, bpy.types.Camera):
                        bpy.data.cameras.remove(data)
                    elif isinstance(data, bpy.types.Light):
                        bpy.data.lights.remove(data)

            for obj, was_hidden in hide_viewport_backup.items():
                obj.hide_viewport = was_hidden

            scene.camera = orig_cam

