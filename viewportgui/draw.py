import bpy
import gpu
import blf
import math
from ..utilities import resolve_building_object as resolve
from gpu_extras.batch import batch_for_shader
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Vector



TITLE_HEIGHT = 30
BUTTON_HEIGHT = 28
BUTTON_GAP = 4
PADDING = 10
PANEL_WIDTH = 300


panel_state = {
    'x': 80,
    'y': 500,
    'dragging': False,
    'drag_offset': (0, 0),
    'hover_index': -1,
}



# --------------------------
# Data helpers
# --------------------------

def get_active_curve():
    context = bpy.context
    resolved = resolve._resolve_building_object(context)
    if resolved is None:
        return None
    _, building = resolved

    floor = building.floors[building.active_floor_index]
    if len(floor.curves) == 0:
        return None

    return floor.curves[floor.active_curve_index]


def get_element_names():
    curve = get_active_curve()
    if curve is None:
        return []

    names = []

    if len(curve.main_elements.objects) == 0:
        return[]
    for element in curve.main_elements.objects:
        if element.object != None:
            names.append(element.object.name)
        else:
            names.append( "- empty -")

    return names


def get_selected_segment_indices():
    curve = get_active_curve()
    if curve is None or curve.curve_object is None:
        return []

    if curve.curve_object.type != 'CURVE':
        return []
    
    curve_data = curve.curve_object.data

    selected = []
    flat_index = 0
    for spline in curve_data.splines:
        if spline.type == 'BEZIER':
            for point in spline.bezier_points:
                if point.select_control_point:
                    selected.append(flat_index)
                flat_index += 1
        else:
            for point in spline.points:
                if point.select:
                    selected.append(flat_index)
                flat_index += 1
    return selected


def _get_curve_segments_positions():
    curve = get_active_curve()
    curve_object = curve.curve_object

    matrix = curve_object.matrix_world
    curve_data = curve_object.data
    positions = []

    for spline in curve_data.splines:
        if spline.type == 'BEZIER':
            for point in spline.bezier_points:
                positions.append(matrix @ point.co)
        else:
            for point in spline.points:
                positions.append(matrix @ Vector(point.co[:3]))

    return positions


def set_element_id_for_selected(element_id):
    curve = get_active_curve()
    if curve is None:
        return
    for idx in get_selected_segment_indices():
        if 0 <= idx < len(curve.segments):
            curve.segments[idx].element_index = element_id
    obj = curve.curve_object
    if obj is not None:
        obj.update_tag()



# --------------------------
# Low-level draw primitives
# --------------------------

def _draw_rect(x, y, w, h, color, radius=5, corner_segments=8):
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    clamped_radius = max(0.0, min(radius, w * 0.5, h * 0.5))

    if clamped_radius <= 0.0:
        perimeter = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]

    else:
        arcs = (
            (x +     clamped_radius, y +     clamped_radius,       math.pi, 1.5 * math.pi),  # bottom-left
            (x + w - clamped_radius, y +     clamped_radius, 1.5 * math.pi, 2.0 * math.pi),  # bottom-right
            (x + w - clamped_radius, y + h - clamped_radius, 0.0,           0.5 * math.pi),  # top-right
            (x +     clamped_radius, y + h - clamped_radius, 0.5 * math.pi,       math.pi),  # top-left
        )
        perimeter = []
        for cx, cy, a0, a1 in arcs:
            for i in range(corner_segments + 1):
                t = i / corner_segments
                a = a0 + (a1 - a0) * t
                perimeter.append((cx + math.cos(a) * clamped_radius, cy + math.sin(a) * clamped_radius))
    center = (x + w * 0.5, y + h * 0.5)
    verts = [center] + perimeter + [perimeter[0]]
    indices = [(0, i, i + 1) for i in range(1, len(verts) - 1)]
    batch = batch_for_shader(shader, 'TRIS', {"pos": verts}, indices=indices)
    shader.uniform_float("color", color)
    batch.draw(shader)


def _draw_rect_outline(x, y, w, h, color, width=1.0):
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    verts = ((x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y))
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": verts})
    gpu.state.line_width_set(width)
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.line_width_set(1.0)


def _draw_text(text, x, y, size=14, color=(1, 1, 1, 1)):
    font_id = 0
    blf.size(font_id, size)
    blf.color(font_id, *color)
    blf.position(font_id, x, y, 0)
    blf.draw(font_id, text)


def _text_dims(text, size=14):
    font_id = 0
    blf.size(font_id, size)
    return blf.dimensions(font_id, text)


LABEL_OFFSET_Y = 18
LABEL_SIZE = 13
LABEL_COLOR = (0.9, 0.9, 0.9, 1.0)
LABEL_COLOR_SELECTED = (1.0, 0.8, 0.2, 1.0)

def _draw_segment_labels():
    region = bpy.context.region
    rv3d = bpy.context.region_data
    if region is None or rv3d is None:
        return

    positions = _get_curve_segments_positions()
    if not positions:
        return

    selected = set(get_selected_segment_indices())

    for i, world_pos in enumerate(positions):
        screen_pos = location_3d_to_region_2d(region, rv3d, world_pos)
        if screen_pos is None:
            continue

        label = str(i)
        tw, th = _text_dims(label, LABEL_SIZE)
        is_selected = i in selected
        color = LABEL_COLOR_SELECTED if is_selected else LABEL_COLOR
        bg = (0.15, 0.15, 0.15, 0.8) if is_selected else (0.15, 0.15, 0.15, 0.6)

        pad = 4
        rx = screen_pos.x - tw / 2 - pad
        ry = screen_pos.y + LABEL_OFFSET_Y - pad
        _draw_rect(rx, ry, tw + pad * 2, th + pad * 2, bg)
        _draw_rect_outline(rx, ry, tw + pad * 2, th + pad * 2, color, 1.0)
        _draw_text(label, screen_pos.x - tw / 2, screen_pos.y + LABEL_OFFSET_Y,
                   LABEL_SIZE, color)



# --------------------------
# Geometry queries
# --------------------------

def _content_height(count):
    return max(count, 1) * (BUTTON_HEIGHT + BUTTON_GAP) + PADDING * 2


def _total_height(count):
    return TITLE_HEIGHT + _content_height(count)


def _window_region(context):
    area = getattr(context, "area", None)
    if area is None or area.type != "VIEW_3D":
        return None
    region = getattr(context, "region", None)
    if region is not None and region.type == "WINDOW":
        return region
    for reg in area.regions:
        if reg.type == "WINDOW":
            return reg
    return None


def place_panel_default(context):
    """Position the elements panel beside the toolbar, vertically centered in the 3D View."""
    region = _window_region(context)
    if region is None:
        return

    space = context.space_data
    if isinstance(space, bpy.types.SpaceView3D):
        space.show_region_toolbar = True

    count = len(get_element_names())
    panel_height = _total_height(count)
    region_h = region.height

    margin_x = PADDING * 10
    y_center = region_h * 0.5
    panel_top = y_center + panel_height * 0.5
    panel_bottom = panel_top - panel_height

    if panel_bottom < 0:
        panel_top = panel_height
    elif panel_top > region_h:
        panel_top = region_h

    panel_state["x"] = margin_x
    panel_state["y"] = panel_top
    panel_state["hover_index"] = -1
    panel_state["dragging"] = False


def button_rect(i):
    state = panel_state
    button_x = state['x'] + PADDING
    button_y = state['y'] - TITLE_HEIGHT - PADDING - (i + 1) * (BUTTON_HEIGHT + BUTTON_GAP) + BUTTON_GAP
    return (button_x, button_y, PANEL_WIDTH - PADDING * 2, BUTTON_HEIGHT)


def title_rect():
    s = panel_state
    return (s['x'], s['y'] - TITLE_HEIGHT, PANEL_WIDTH, TITLE_HEIGHT)


def full_rect(count):
    state = panel_state
    height = _total_height(count)
    return (state['x'], state['y'] - height, PANEL_WIDTH, height)


def point_in_rect(mouse_x, mouse_y, rectangle):
    rectangle_x, rectangle_y, rectangle_w, rectangle_h = rectangle
    width_position = rectangle_x <= mouse_x <= rectangle_x + rectangle_w
    height_position = rectangle_y <= mouse_y <= rectangle_y + rectangle_h
    return True if width_position and height_position else False



# --------------------------
# Main draw callback
# --------------------------

def draw_callback():
    names = get_element_names()
    s = panel_state
    px, py = s['x'], s['y']
    h = _total_height(len(names))

    gpu.state.blend_set('ALPHA')

    _draw_rect(px, py - h, PANEL_WIDTH, h, (0.1, 0.1, 0.2, 0.5))
    _draw_rect_outline(px, py - h, PANEL_WIDTH, h, (0.4, 0.4, 0.4, 0.8))

    _draw_rect(px, py - TITLE_HEIGHT, PANEL_WIDTH, TITLE_HEIGHT, (0.28, 0.28, 0.28, 1.0))
    _draw_text("Elements", px + PADDING, py - TITLE_HEIGHT + 9, 14, (0.85, 0.85, 0.85, 1))

    if not names:
        _draw_text("No elements", px + PADDING, py - TITLE_HEIGHT - PADDING - 14,
                    12, (0.5, 0.5, 0.5, 1))

    else:
        for i, name in enumerate(names):
            bx, by, bw, bh = button_rect(i)
            hovered = (i == s['hover_index'])
            bg = (0.38, 0.38, 0.38, 0.9) if hovered else (0.26, 0.26, 0.26, 0.9)
            _draw_rect(bx, by, bw, bh, bg)
            _draw_rect_outline(bx, by, bw, bh, (0.45, 0.45, 0.45, 0.6))

            tw, th = _text_dims(name, 13)
            _draw_text(name, bx + (bw - tw) / 2, by + (bh - th) / 2, 13)

    _draw_segment_labels()

    gpu.state.blend_set('NONE')
