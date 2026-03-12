import bpy
import gpu
import blf
from gpu_extras.batch import batch_for_shader


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

def get_active_floor():
    scene = bpy.context.scene
    if not hasattr(scene, 'buildings') or len(scene.buildings) == 0:
        return None

    idx = scene.active_building_index
    if idx < 0 or idx >= len(scene.buildings):
        return None

    building = scene.buildings[idx]
    if len(building.floors) == 0:
        return None

    fi = building.active_floor_index
    if fi < 0 or fi >= len(building.floors):
        return None

    return building.floors[fi]


def get_element_names():
    floor = get_active_floor()
    if floor is None:
        return []

    names = []
    if floor.element_method == 'COLLECTION':
        if floor.element_collection:
            for obj in floor.element_collection.objects:
                names.append(obj.name)
    else:
        for entry in floor.element_object:
            names.append(entry.object.name if entry.object else "- empty -")
    return names


def get_selected_segment_indices():
    floor = get_active_floor()
    if floor is None or floor.curve is None:
        return []

    curve_data = floor.curve.data
    if floor.curve.type != 'CURVE':
        return []

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


def set_element_id_for_selected(element_id):
    floor = get_active_floor()
    if floor is None:
        return
    for idx in get_selected_segment_indices():
        if 0 <= idx < len(floor.segments):
            floor.segments[idx].element_ID = element_id



# --------------------------
# Low-level draw primitives
# --------------------------

def _draw_rect(x, y, w, h, color):
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    verts = ((x, y), (x + w, y), (x + w, y + h), (x, y + h))
    indices = ((0, 1, 2), (0, 2, 3))
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



# --------------------------
# Geometry queries
# --------------------------

def _content_height(count):
    return max(count, 1) * (BUTTON_HEIGHT + BUTTON_GAP) + PADDING * 2


def _total_height(count):
    return TITLE_HEIGHT + _content_height(count)


def button_rect(i):
    s = panel_state
    bx = s['x'] + PADDING
    by = s['y'] - TITLE_HEIGHT - PADDING - (i + 1) * (BUTTON_HEIGHT + BUTTON_GAP) + BUTTON_GAP
    return (bx, by, PANEL_WIDTH - PADDING * 2, BUTTON_HEIGHT)


def title_rect():
    s = panel_state
    return (s['x'], s['y'] - TITLE_HEIGHT, PANEL_WIDTH, TITLE_HEIGHT)


def full_rect(count):
    s = panel_state
    h = _total_height(count)
    return (s['x'], s['y'] - h, PANEL_WIDTH, h)


def point_in_rect(mx, my, rect):
    rx, ry, rw, rh = rect
    return rx <= mx <= rx + rw and ry <= my <= ry + rh



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

    _draw_rect(px, py - TITLE_HEIGHT, PANEL_WIDTH, TITLE_HEIGHT, (0.28, 0.28, 0.28, 0.95))
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

    gpu.state.blend_set('NONE')
