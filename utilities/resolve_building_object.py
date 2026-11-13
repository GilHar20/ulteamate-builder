def _resolve_building_object(context):
    if not context.view_layer.objects.active:
        return None
    active_object = context.view_layer.objects.active
    if not active_object.utm_building.is_utm_building:
        if not active_object.parent:
            return None
        if not active_object.parent.utm_building.is_utm_building:
            return None
        else:
            building = active_object.parent.utm_building
            return active_object.parent, building
    
    building = active_object.utm_building
    return active_object, building


def _is_utm_building(obj):
    if obj is None:
        return False
    building = getattr(obj, "utm_building", None)
    if building is None:
        return False
    return bool(getattr(building, "is_utm_building", False))
