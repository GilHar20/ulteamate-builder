from __future__ import annotations

import math
import re

import bpy
import gpu
from mathutils import Matrix, Vector



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
        space.overlay.show_overlays = False
        for region in area.regions:
            if region.type == "WINDOW":
                return area, space, region
    return None


def _fit_camera_to_bounds(cam_data: bpy.types.Camera, cam_obj: bpy.types.Object, center: Vector, dimensions: Vector) -> None:
    cam_data.type = "PERSP"
    cam_data.lens = 140
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


def _capture_view3d_offscreen(context: bpy.types.Context, space: bpy.types.SpaceView3D, region: bpy.types.Region, cam_obj: bpy.types.Object, size: int, transparent_background: bool) -> list[float]:

    scene = context.scene
    view_layer = context.view_layer

    depsgraph = context.evaluated_depsgraph_get()
    view_matrix = cam_obj.matrix_world.inverted()
    projection_matrix = cam_obj.calc_matrix_camera(depsgraph, x = size, y = size)

    offscreen = gpu.types.GPUOffScreen(size, size)
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
            buffer = fb.read_color(0, 0, size, size, 4, 0, "UBYTE")
    finally:
        offscreen.free()

    count = size * size * 4
    buffer.dimensions = count
    if hasattr(buffer, "to_list"):
        raw = buffer.to_list()
    else:
        raw = [buffer[i] for i in range(count)]
    return [v / 255.0 for v in raw]


def _assign_pixels(image: bpy.types.Image, pixels: list[float]) -> None:
    try:
        image.pixels.foreach_set(pixels)
    except (TypeError, ValueError, AttributeError):
        image.pixels = pixels


class UTMBUILDER_OT_render_selected_thumbnail(bpy.types.Operator):
    bl_idname = "utmbuilder.render_selected_thumbnail"
    bl_label = "Render Selection Thumbnail"
    bl_description = "Render an element thumbnail and save it as an image"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    resolution: bpy.props.IntProperty(
        name = "Size",
        description = "Square render resolution in pixels",
        default = 256,
        min = 64,
        max = 4096,
    )
    transparent_film: bpy.props.BoolProperty(
        name = "Transparent Background",
        description = "Clear alpha in the thumbnail background",
        default = False,
    )
    open_image_editor: bpy.props.BoolProperty(
        name = "Show in Image Editor",
        description = "Assign the new image to an Image Editor area when possible",
        default = True,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return (
            context.mode == "OBJECT"
            and len(context.selected_objects) > 0
        )

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene = context.scene
        orig_cam = scene.camera
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

        cam_data = bpy.data.cameras.new("Thumbnail_Camera_Data")
        cam_obj = bpy.data.objects.new(selected[0].name + "_Thumbnail_Camera", cam_data)
        scene.collection.objects.link(cam_obj)
        scene.camera = cam_obj
        bpy.ops.view3D.localview()

        _fit_camera_to_bounds(cam_data, cam_obj, center, dimensions)
        size = self.resolution
        pixels = _capture_view3d_offscreen(
            context,
            space,
            region,
            cam_obj,
            size,
            self.transparent_film,
        )
        if len(pixels) != size * size * 4:
            self.report({"ERROR"}, "Off-screen capture did not produce pixel data")
            return {"CANCELLED"}

        image_name = selected[0].name + "_Thumbnail"
        new_image = bpy.data.images.get(image_name)
        if new_image is None:
            new_image = bpy.data.images.new(image_name, width = size, height = size, alpha = self.transparent_film)
        elif new_image.size[0] != size or new_image.size[1] != size:
            new_image.scale(size, size)

        _assign_pixels(new_image, pixels)
        new_image.pack()
        new_image.use_fake_user = True
        new_image.colorspace_settings.name = "sRGB"

        self.report({"INFO"}, f"Packed image '{new_image.name}")
        
        bpy.ops.view3D.localview()
        space.overlay.show_overlays = True
        bpy.data.objects.remove(cam_obj, do_unlink=True)
        bpy.data.cameras.remove(cam_data)
        scene.camera = orig_cam

        return {"FINISHED"}

