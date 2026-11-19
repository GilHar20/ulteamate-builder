import bpy


_USE_PROPERTIES_API = bpy.app.version >= (5, 2, 0)

_UTM_GN_CONSTRUCT = "UTM.Builder_Construct_GN"
_UTM_GN_LINK_FLOOR = "UTM.Builder_LinkFloor_GN"

_UTM_GN_MARKER = (
    "UTM.Builder_CurveAttributes_GN",
    "UTM.Builder_CurveElements_GN",
    "UTM.Builder_ElementID_GN",
)

CONSTRUCT_SOCKETS = {
    "floors_collection": "Socket_2",
}

CURVE_ATTRIBUTES_SOCKETS = {
    "floor_visibility": "Socket_18",
    "array": "Socket_3",
    "maximum_height": "Socket_23",
    "ID": "Socket_22",
    "main_inset": "Socket_10",
    "floor_inset": "Socket_24",
    "ceiling_inset": "Socket_25",
    "height": "Socket_4",
    "floor_ceiling": "Socket_5",
    "thickness": "Socket_15",
    "direction_bottom": "Socket_16",
    "direction_top": "Socket_17",
    "top_material": "Socket_19",
    "sides_material": "Socket_20",
    "bottom_material": "Socket_21",
}

CURVE_ELEMENTS_SOCKETS = {
    "object": "Socket_4",
    "element_type": "Socket_5",
    "up_stretched": "Socket_6",
    "is_empty": "Socket_9",
    "empty_bounds": "Socket_10",
    "correct_uv": "Socket_11",
}

SEGMENT_SOCKETS = {
    "segment_index": "Socket_2",
    "fit_method": "Socket_4",
    "fixed_number": "Socket_5",
    "select_method": "Socket_6",
    "select_per_segment": "Socket_7",
    "sequence_offset": "Socket_8",
    "random_index": "Socket_9",
    "element_index": "Socket_3",
}

LINK_FLOOR_SOCKETS = {
    "curves_collection": "Socket_2",
    "height_offset": "Socket_3",
    "floor_visibility": "Socket_4",
}


def _match_enum_item(enum_items, value):
    if enum_items is None or len(enum_items) == 0:
        return None
    if isinstance(value, int):
        if 0 <= value < len(enum_items):
            return enum_items[value]
        return None
    if not isinstance(value, str):
        return None
    raw = value.strip()
    upper = raw.upper()
    for item in enum_items:
        if item.identifier == raw or item.identifier.upper() == upper:
            return item
        if item.name == raw or item.name.upper() == upper:
            return item
    return None


def _coerce_for_socket_input(modifier, socket_id, value):
    """PropertyGroup / RNA value -> modifier socket value (e.g. BOTTOM -> Bottom)."""
    socket_inp = getattr(modifier.properties.inputs, socket_id)
    if socket_inp is not None:
        enum_items = getattr(socket_inp, "enum_items", None)
        item = _match_enum_item(enum_items, value)
        if item is not None:
            return item.identifier
    if isinstance(value, str) and value.isascii() and value.isupper():
        return value.capitalize()
    return value


def coerce_value_for_pg_property(pg, prop_name, value):
    """Modifier socket value -> PropertyGroup enum identifier (e.g. Bottom -> BOTTOM)."""
    prop = pg.bl_rna.properties.get(prop_name)
    if prop is None or prop.type != "ENUM":
        return value
    item = _match_enum_item(prop.enum_items, value)
    if item is not None:
        return item.identifier
    return value


def set_pg_property(pg, prop_name, value):
    value = coerce_value_for_pg_property(pg, prop_name, value)
    setattr(pg, prop_name, value)


def _get_socket_identifier(modifier, property_name: str):
    if "UTM.Builder_Construct_GN" in modifier.name:
        return CONSTRUCT_SOCKETS[property_name]
    if "UTM.Builder_CurveAttributes_GN" in modifier.name:
        return CURVE_ATTRIBUTES_SOCKETS[property_name]
    if "UTM.Builder_CurveElements_GN" in modifier.name:
        return CURVE_ELEMENTS_SOCKETS[property_name]
    if "UTM.Builder_ElementID_GN" in modifier.name:
        return SEGMENT_SOCKETS[property_name]
    if "UTM.Builder_LinkFloor_GN" in modifier.name:
        return LINK_FLOOR_SOCKETS[property_name]
    raise KeyError(
        "Unknown modifier %r or property %r" % (modifier.name, property_name)
    )


def _get_socket_value(modifier, property_name: str):
    socket_id = _get_socket_identifier(modifier, property_name)
    if _USE_PROPERTIES_API:
        return getattr(modifier.properties.inputs, socket_id).value
    return modifier[socket_id]


def _set_socket_value(modifier, property_name: str, value):
    socket_id = _get_socket_identifier(modifier, property_name)
    new_value = _coerce_for_socket_input(modifier, socket_id, value)
    if _USE_PROPERTIES_API:
        getattr(modifier.properties.inputs, socket_id).value = new_value
    else:
        modifier[socket_id] = value


def _input_driver_path(modifier_name: str, identifier: str) -> str:
    """Deprecated: used by drivers; remove when evaluate_building is migrated."""
    if _USE_PROPERTIES_API:
        return f'modifiers["{modifier_name}"].properties.inputs.{identifier}.value'
    else:
        return f'modifiers["{modifier_name}"]["{identifier}"]'


def _is_utm_modifier(modifier):
    if modifier.type != "NODES":
        return False
    return any(marker in modifier.name for marker in _UTM_GN_MARKER)


def construct_modifier(obj):
    for modifier in obj.modifiers:
        if modifier.type != "NODES":
            continue
        if _UTM_GN_CONSTRUCT in modifier.name:
            return modifier
    return None


def filter_all_curve_modifiers(curve_pg, index=None):
    curve_obj = curve_pg.curve_object
    modifiers = [mod for mod in curve_obj.modifiers if _is_utm_modifier(mod)]
    if index is None:
        return modifiers
    if index < 0:
        return modifiers[0]
    if index >= len(modifiers):
        return modifiers[len(modifiers) - 1]
    return modifiers[index]


def curve_attributes_modifier(curve_pg):
    return filter_all_curve_modifiers(curve_pg, 0)


def _element_counts(curve_pg):
    main = curve_pg.main_elements.objects if curve_pg.main_elements else ()
    corner = curve_pg.corner_elements.objects if curve_pg.corner_elements else ()
    return len(main), len(corner)


def curve_elements_modifier(curve_pg, element_index, element_type):
    main_count, _ = _element_counts(curve_pg)
    base = 1
    if element_type == "corner_elements":
        base += main_count
    index = base + element_index
    return filter_all_curve_modifiers(curve_pg, index)


def element_id_modifier(curve_pg, segment_index):
    main_count, corner_count = _element_counts(curve_pg)
    index = 1 + main_count + corner_count + segment_index
    return filter_all_curve_modifiers(curve_pg, index)


def link_floor_modifier(instance_obj):
    for modifier in instance_obj.modifiers:
        if modifier.type != "NODES":
            continue
        if _UTM_GN_LINK_FLOOR in modifier.name:
            return modifier
    return None
