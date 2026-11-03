import re

import bpy

from . import operators, resolve_building_object as resolve
from ..utilities import gn_sockets


_FLOOR_ID_FROM_NAME = re.compile(r"_Floor(\d+)(?:_|$)")


_CURVE_ATTRIBUTE_FIELDS = (
    ("Socket_10", "inset"),
    ("Socket_4", "height"),
    ("Socket_5", "floor_ceiling"),
    ("Socket_15", "thickness"),
    ("Socket_16", "direction_bottom"),
    ("Socket_17", "direction_top"),
    ("Socket_11", "select_method"),
    ("Socket_14", "select_per_segment"),
    ("Socket_12", "sequence_offset"),
    ("Socket_13", "random_index"),
    ("Socket_19", "top_material"),
    ("Socket_20", "sides_material"),
    ("Socket_21", "bottom_material"),
)


def _set_pg_property(pg, prop_name, value):
    prop = pg.bl_rna.properties.get(prop_name)
    if prop is None:
        return
    if prop.type == "ENUM" and isinstance(value, int):
        identifiers = [item.identifier for item in prop.enum_items]
        if 0 <= value < len(identifiers):
            value = identifiers[value]
    try:
        setattr(pg, prop_name, value)
    except (TypeError, ValueError):
        pass


def _sync_curve_attributes(curve, modifier):
    for socket_id, field_name in _CURVE_ATTRIBUTE_FIELDS:
        value = gn_sockets._get_socket_value(modifier, socket_id)
        _set_pg_property(curve, field_name, value)

    curve_id = gn_sockets._get_socket_value(modifier, "Socket_22")
    if isinstance(curve_id, int):
        curve.ID = curve_id


def _sync_curve_element(curve, curve_obj, modifier):
    element_type = gn_sockets._get_socket_value(modifier, "Socket_5")
    elements = getattr(curve, element_type)
    elements.collect_method = "OBJECTS"
    element = elements.objects.add()
    element.ID = len(elements.objects) - 1
    element.element_type = element_type
    element.host_curve = curve_obj
    element.object = gn_sockets._get_socket_value(modifier, "Socket_4")
    element.is_empty = bool(gn_sockets._get_socket_value(modifier, "Socket_9"))
    element.empty_bounds = gn_sockets._get_socket_value(modifier, "Socket_10")
    element.up_stretched = bool(gn_sockets._get_socket_value(modifier, "Socket_6"))
    element.correct_uv = bool(gn_sockets._get_socket_value(modifier, "Socket_11"))


def _read_segment_settings(modifier):
    return {
        "ID": gn_sockets._get_socket_value(modifier, "Socket_2"),
        "element_ID": gn_sockets._get_socket_value(modifier, "Socket_3"),
        "fit_method": gn_sockets._get_socket_value(modifier, "Socket_4"),
        "fixed_number": gn_sockets._get_socket_value(modifier, "Socket_5"),
    }


def _apply_segment_settings(curve, segment_settings):
    operators._sync_segments_to_curves(curve)

    for index, settings in enumerate(segment_settings):
        if index >= len(curve.segments):
            break
        segment = curve.segments[index]
        segment.ID = index
        if isinstance(settings.get("ID"), int):
            segment.ID = settings["ID"]
        _set_pg_property(segment, "element_ID", settings.get("element_ID", 0))
        _set_pg_property(segment, "fit_method", settings.get("fit_method", "FIT"))
        _set_pg_property(segment, "fixed_number", settings.get("fixed_number", 1))


def _sync_curve_from_modifiers(curve, curve_obj):
    curve.main_elements.objects.clear()
    curve.corner_elements.objects.clear()
    curve.segments.clear()

    segment_settings = []

    for modifier in curve_obj.modifiers:
        if modifier.type != "NODES":
            continue
        if "CurveAttributes_GN" in modifier.name:
            _sync_curve_attributes(curve, modifier)
        elif "CurveElements_GN" in modifier.name:
            _sync_curve_element(curve, curve_obj, modifier)
        elif "ElementID_GN" in modifier.name:
            segment_settings.append(_read_segment_settings(modifier))

    _apply_segment_settings(curve, segment_settings)



class UTMBUILDER_OT_sync_from_modifier_stack(bpy.types.Operator):
    bl_idname = "utmbuilder.sync_from_modifier_stack"
    bl_label = "Sync from modifier stack"
    bl_description = "Sync the building from the outliner hierarchy and objects modifier to property groups"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}


    def _floor_curves_sorted(self, floor_collection):
        curves = []
        for obj in floor_collection.objects:
            if obj.type != "CURVE":
                continue
            for modifier in obj.modifiers:
                if modifier.type == "NODES" and "CurveAttributes_GN" in modifier.name:
                    curves.append(obj)
                    break
        return sorted(curves, key = lambda obj: obj.location.z)


    def _find_link_floor(self, floor_collection):
        for obj in floor_collection.objects:
            for modifier in obj.modifiers:
                if modifier.type == "NODES" and "LinkFloor_GN" in modifier.name:
                    return obj, modifier
        return None, None


    def _floor_id_from_collection(self, floor_collection):
        match = _FLOOR_ID_FROM_NAME.search(floor_collection.name)
        if match:
            return int(match.group(1))
        legacy = re.search(r"Floor_(\d+)_Curves", floor_collection.name, re.IGNORECASE)
        if legacy:
            return int(legacy.group(1))
        return 10 ** 9


    def _floor_array_from_collection(self, curves_collection):
        if curves_collection is None:
            return 1
        for obj in curves_collection.objects:
            if obj.type != "CURVE":
                continue
            for modifier in obj.modifiers:
                if modifier.type == "NODES" and "CurveAttributes_GN" in modifier.name:
                    value = gn_sockets._get_socket_value(modifier, "Socket_3")
                    if isinstance(value, int):
                        return value
                    if isinstance(value, float):
                        return int(value)
        return 1


    def _floors_ordered(self, floors_parent_collection):
        """
        Floor order follows collection names (build_*_FloorN), not world Z.
        Linked floors are detected by LinkFloor_GN on an object in the collection.
        Curve Z is only used to order curves within a source floor.
        """
        ordered = []
        for floor_collection in floors_parent_collection.children:
            if not floor_collection.objects:
                continue

            floor_name_id = self._floor_id_from_collection(floor_collection)
            instance_obj, link_modifier = self._find_link_floor(floor_collection)
            if link_modifier is not None:
                ordered.append((
                    "linked",
                    floor_collection,
                    [],
                    instance_obj,
                    link_modifier,
                    floor_name_id,
                ))
                continue

            curves = self._floor_curves_sorted(floor_collection)
            if not curves:
                continue

            ordered.append((
                "source",
                floor_collection,
                curves,
                None,
                None,
                floor_name_id,
            ))

        ordered.sort(key = lambda item: (item[5], item[1].name))
        return ordered

    def get_parent_collection(self, target_collection):
        for coll in bpy.data.collections:
            if target_collection.name in coll.children:
                return coll
        return None

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

        floor_collection = gn_sockets._get_socket_value(construct_modifier, "Socket_2")
        building_collection = self.get_parent_collection(floor_collection)
        if building_collection is None:
            self.report({"ERROR"}, "Construct modifier has no building collection")
            return {"CANCELLED"}
    
        elements_collection = None
        for collection in building_collection.children:
            if "_Elements" in collection.name:
                elements_collection = collection

        if floor_collection is None or elements_collection is None:
            self.report({"ERROR"}, "Floors or elements collections are missing! Cannot proceed")
            return {"CANCELLED"}

        floors_ordered = self._floors_ordered(floor_collection)

        building = base_object.utm_building
        building.is_utm_building = True
        building.base_object = base_object
        building.building_collection = building_collection
        building.floors_collection = floor_collection
        building.elements_collection = elements_collection

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
                source_collection = gn_sockets._get_socket_value(link_modifier, "Socket_2")
                floor.array = self._floor_array_from_collection(source_collection)
                continue

            floor.is_linked = False
            floor.instance_object = None
            floor.array = self._floor_array_from_collection(curves_collection)

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
