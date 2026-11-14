import bpy
from . import draw
from ..utilities import resolve_building_object as resolve


class UTMBUILDER_OT_viewport_panel(bpy.types.Operator):
    bl_idname = "utmbuilder.viewport_panel"
    bl_label = "Toggle Viewport Elements Panel"
    bl_description = "Show or hide the floating elements panel in the 3D viewport"

    _handle = None

    @classmethod
    def is_running(cls):
        return cls._handle is not None

    @classmethod
    def _redraw_view3d_areas(cls, context):
        screen = getattr(context, "screen", None)
        if screen is None:
            if context.area and context.area.type == "VIEW_3D":
                context.area.tag_redraw()
            return
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()

    @classmethod
    def poll(cls, context):
        resolved = resolve._resolve_building_object(context)
        if resolved is None:
            return False
        else:
            return True

    def invoke(self, context, event):
        cls = type(self)

        if cls.is_running():
            cls._remove(context)
            return {'FINISHED'}

        resolved = resolve._resolve_building_object(context)
        if resolved is None:
            self.report({"ERROR"}, "No building found")
            return {"CANCELLED"}
        _, building = resolved

        floor = building.floors[building.active_floor_index]
        if len(floor.curves) == 0:
            self.report({'WARNING'}, "Active floor has no curve assigned")
            return {'CANCELLED'}

        curve = floor.curves[floor.active_curve_index]
        curve_obj = curve.curve_object
        if curve_obj is None:
            self.report({'WARNING'}, "Active curve has no curve object")
            return {'CANCELLED'}
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = curve_obj
        curve_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')

        draw.place_panel_default(context)
        cls._handle = bpy.types.SpaceView3D.draw_handler_add(draw.draw_callback, (), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        cls._redraw_view3d_areas(context)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        cls = type(self)
        if not cls.is_running():
            return {'FINISHED'}

        state = draw.panel_state
        names = draw.get_element_names()
        count = len(names)

        if event.type in {"MOUSEMOVE", "LEFTMOUSE"} and context.area is None:
            cls._redraw_view3d_areas(context)
            return {"PASS_THROUGH"}

        mouse_x, mouse_y = event.mouse_region_x, event.mouse_region_y

        if event.type == 'MOUSEMOVE':
            cls._redraw_view3d_areas(context)

            if state['dragging']:
                offset_x, offset_y = state['drag_offset']
                state['x'] = mouse_x - offset_x
                state['y'] = mouse_y - offset_y
                return {'RUNNING_MODAL'}

            state['hover_index'] = -1
            for i in range(count):
                if draw.point_in_rect(mouse_x, mouse_y, draw.button_rect(i)):
                    state['hover_index'] = i
                    break

            if draw.point_in_rect(mouse_x, mouse_y, draw.full_rect(count)):
                return {'RUNNING_MODAL'}
            return {'PASS_THROUGH'}

        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                if draw.point_in_rect(mouse_x, mouse_y, draw.title_rect()):
                    state['dragging'] = True
                    state['drag_offset'] = (mouse_x - state['x'], mouse_y - state['y'])
                    return {'RUNNING_MODAL'}

                for i in range(count):
                    if draw.point_in_rect(mouse_x, mouse_y, draw.button_rect(i)):
                        draw.set_element_id_for_selected(i)
                        return {'RUNNING_MODAL'}

                if not draw.point_in_rect(mouse_x, mouse_y, draw.full_rect(count)):
                    return {'PASS_THROUGH'}
                return {'RUNNING_MODAL'}

            if event.value == 'RELEASE':
                if state['dragging']:
                    state['dragging'] = False
                    return {'RUNNING_MODAL'}
                return {'PASS_THROUGH'}

        if event.type == 'ESC' and event.value == 'PRESS':
            cls._remove(context)
            bpy.ops.object.mode_set(mode='OBJECT')
            return {'FINISHED'}

        if context.object is None or context.object.mode != 'EDIT':
            cls._remove(context)
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    @classmethod
    def _remove(cls, context):
        if cls._handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(cls._handle, 'WINDOW')
            cls._handle = None
        draw.panel_state['hover_index'] = -1
        draw.panel_state['dragging'] = False
        cls._redraw_view3d_areas(context)

    @classmethod
    def shutdown(cls):
        if cls._handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(cls._handle, 'WINDOW')
            cls._handle = None
