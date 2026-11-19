'''
Operator to sync a building from the modifier stack and collaetion hierarchy.
Useful for moving .blend files between computers without worrying about the addon being installed.
Or in any case were the addon is disabled, possibly in a version jump without backwards compatibility.

This file acts as an entity of its own, thus presumes nothing, and will not rely on any other files.
It will try to build the entire property group structure from scratch, all on its own.
'''


import re
import bpy

from ..utilities import gn_sockets
from . import operators



_FLOOR_ID_FROM_NAME = re.compile(r"_Floor(\d+)(?:_|$)")
_CURVE_ATTRIBUTE_FIELDS = (
    ("Socket_10", "main_inset"),
    ("Socket_24", "floor_inset"),
    ("Socket_25", "ceiling_inset"),
    ("Socket_4", "height"),
    ("Socket_5", "floor_ceiling"),
    ("Socket_15", "thickness"),
    ("Socket_16", "direction_bottom"),
    ("Socket_17", "direction_top"),
    ("Socket_19", "top_material"),
    ("Socket_20", "sides_material"),
    ("Socket_21", "bottom_material"),
)


def _sync_curve_from_modifiers(curve, curve_obj):
    curve.main_elements.objects.clear()
    curve.corner_elements.objects.clear()
    curve.segments.clear()

    segment_settings = []

    for modifier in curve_obj.modifiers:
        if modifier.type != "NODES":
            continue

        if "CurveAttributes_GN" in modifier.name:
            for _socket_id, field_name in _CURVE_ATTRIBUTE_FIELDS:
                value = gn_sockets._get_socket_value(modifier, field_name)
                gn_sockets.set_pg_property(curve, field_name, value)

            curve_id = gn_sockets._get_socket_value(modifier, "ID")
            if isinstance(curve_id, int):
                curve.ID = curve_id

        elif "CurveElements_GN" in modifier.name:
            element_type = gn_sockets._get_socket_value(modifier, "element_type")
            elements = getattr(curve, element_type)
            element = elements.objects.add()
            element.ID = len(elements.objects) - 1
            element.element_type = element_type
            element.host_curve = curve_obj
            element.object = gn_sockets._get_socket_value(modifier, "object")
            element.is_empty = gn_sockets._get_socket_value(modifier, "is_empty")
            element.empty_bounds = gn_sockets._get_socket_value(modifier, "empty_bounds")
            element.up_stretched = gn_sockets._get_socket_value(modifier, "up_stretched")
            element.correct_uv = gn_sockets._get_socket_value(modifier, "correct_uv")

        elif "ElementID_GN" in modifier.name:
            segment_settings.append({
                "ID": gn_sockets._get_socket_value(modifier, "segment_index"),
                "fit_method": gn_sockets._get_socket_value(modifier, "fit_method"),
                "fixed_number": gn_sockets._get_socket_value(modifier, "fixed_number"),
                "select_method": gn_sockets._get_socket_value(modifier, "select_method"),
                "select_per_segment": gn_sockets._get_socket_value(modifier, "select_per_segment"),
                "sequence_offset": gn_sockets._get_socket_value(modifier, "sequence_offset"),
                "random_index": gn_sockets._get_socket_value(modifier, "random_index"),
                "element_index": gn_sockets._get_socket_value(modifier, "element_index"),
            })

    operators._sync_segments_to_curves(curve)

    for index, settings in enumerate(segment_settings):
        if index >= len(curve.segments):
            break
        segment = curve.segments[index]
        segment.ID = index
        if isinstance(settings.get("ID"), int):
            segment.ID = settings["ID"]
        gn_sockets.set_pg_property(segment, "fit_method", settings.get("fit_method", "FIT"))
        gn_sockets.set_pg_property(segment, "fixed_number", settings.get("fixed_number", 1))
        gn_sockets.set_pg_property(segment, "select_method", settings.get("select_method", "SEQUENCE0"))
        gn_sockets.set_pg_property(segment, "select_per_segment", settings.get("select_per_segment", 1))
        gn_sockets.set_pg_property(segment, "sequence_offset", settings.get("sequence_offset", 0))
        gn_sockets.set_pg_property(segment, "random_index", settings.get("random_index", 0))
        gn_sockets.set_pg_property(segment, "element_index", settings.get("element_index", 0))


def _floor_array_from_collection(curves_collection):
    for obj in curves_collection.objects:
        if obj.type != "CURVE":
            continue
        for modifier in obj.modifiers:
            if modifier.type == "NODES" and "CurveAttributes_GN" in modifier.name:
                value = gn_sockets._get_socket_value(modifier, "array")
                if isinstance(value, int):
                    return value
                if isinstance(value, float):
                    return int(value)
    return 1


def _floor_curves_sorted(floor_collection):
    curves = []
    for obj in floor_collection.objects:
        if obj.type != "CURVE":
            continue
        for modifier in obj.modifiers:
            if modifier.type == "NODES" and "CurveAttributes_GN" in modifier.name:
                curves.append(obj)
                break
    return sorted(curves, key = lambda obj: obj.location.z)


def _find_link_floor(floor_collection):
    for obj in floor_collection.objects:
        for modifier in obj.modifiers:
            if modifier.type == "NODES" and "LinkFloor_GN" in modifier.name:
                return obj, modifier
    return None, None


def _floors_ordered(floors_collection):
    """Floor order follows collection names (build_*_FloorN), not world Z. Linked floors are detected by LinkFloor_GN"""

    ordered = []
    for curves_collection in floors_collection.children:
        if not curves_collection.objects:
            continue

        match = _FLOOR_ID_FROM_NAME.search(curves_collection.name)
        floor_name_id = int(match.group(1)) if match else 10 ** 9
        instance_obj, link_modifier = _find_link_floor(curves_collection)
        if link_modifier is not None:
            ordered.append((
                "linked",
                curves_collection,
                [],
                instance_obj,
                link_modifier,
                floor_name_id,
            ))
            continue

        curves = _floor_curves_sorted(curves_collection)
        if not curves:
            continue

        ordered.append((
            "source",
            curves_collection,
            curves,
            None,
            None,
            floor_name_id,
        ))

    ordered.sort(key = lambda item: (item[5], item[1].name))
    return ordered


class UTMBUILDER_OT_sync_from_modifier_stack(bpy.types.Operator):
    bl_idname = "utmbuilder.sync_from_modifier_stack"
    bl_label = "Sync from modifier stack"
    bl_description = "Sync the building from the outliner hierarchy and objects modifier to property groups"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}


    def execute(self, context):
        base_object = context.view_layer.objects.active
        if base_object is None:
            self.report({"ERROR"}, "No object selected for syncing")
            return {"CANCELLED"}

        construct_modifier = None
        for modifier in base_object.modifiers:
            if modifier.type == "NODES" and "Construct_GN" in modifier.name:
                construct_modifier = modifier
                break

        if construct_modifier is None:
            self.report({"ERROR"}, "Object does not have construct modifier!")
            return {"CANCELLED"}

        building = base_object.utm_building
        building_collection = None
        floors_collection = gn_sockets._get_socket_value(construct_modifier, "floors_collection")
        for collection in bpy.data.collections:
            if floors_collection.name in collection.children:
                building_collection = collection
        if building_collection is None:
            self.report({"ERROR"}, "Construct modifier has no building collection")
            return {"CANCELLED"}

        if floors_collection is None:
            self.report({"ERROR"}, "Floors collection is missing! Cannot proceed")
            return {"CANCELLED"}

        elements_collection = None
        for collection in building_collection.children:
            if "_Elements" in collection.name:
                elements_collection = collection

        if elements_collection is None:
            self.report({"ERROR"}, "Elements collection is missing! Cannot proceed")
            return {"CANCELLED"}

        building.is_utm_building = True
        building.base_object = base_object
        building.building_collection = building_collection
        building.floors_collection = floors_collection
        building.elements_collection = elements_collection
            
        floors_ordered = _floors_ordered(floors_collection)

        source_index_by_collection = {}
        for idx, spec in enumerate(floors_ordered):
            if spec[0] == "source":
                source_index_by_collection[spec[1]] = idx

        building.floors.clear()
        for floor_index, floor_spec in enumerate(floors_ordered):
            kind = floor_spec[0]
            curves_collection = floor_spec[1]
            curve_objects = floor_spec[2]
            instance_obj = floor_spec[3]
            link_modifier = floor_spec[4]

            floor = building.floors.add()
            floor.ID = floor_index
            floor.curves_collection = curves_collection

            if kind == "linked":
                floor.is_linked = True
                floor.instance_object = instance_obj
                source_collection = gn_sockets._get_socket_value(link_modifier, "curves_collection")
                floor.linked_ID = source_index_by_collection.get(source_collection, -1)
                floor.array = 1
                continue

            floor.is_linked = False
            floor.instance_object = None
            floor.array = _floor_array_from_collection(curves_collection)

            for curve_index, curve_obj in enumerate(curve_objects):
                curve = floor.curves.add()
                curve.ID = curve_index
                curve.floor_ID = floor_index
                curve.curve_object = curve_obj
                _sync_curve_from_modifiers(curve, curve_obj)

        building.active_floor_index = 0

        bpy.ops.utmbuilder.evaluate_building()

        self.report({"INFO"}, "Synced %d floor(s) from modifier stack" % len(floors_ordered))
        return {"FINISHED"}
