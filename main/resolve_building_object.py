import bpy



# Flip to True when generate_building writes Object.utm_building instead of Scene.buildings.
_USE_OBJECT_STORAGE = False


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
            return building
    
    building = active_object.utm_building
    return building


def is_utm_constructor(obj):
    if obj is None:
        return False
    building = getattr(obj, "utm_building", None)
    if building is None:
        return False
    return bool(getattr(building, "is_utm_building", False))


def resolve_building_object(context, obj=None):
    """Return the constructor Object for the current building context, or None."""
    if obj is None:
        if context is None:
            return None
        obj = context.view_layer.objects.active

    if obj is None:
        return None

    if is_utm_constructor(obj):
        return obj

    parent = obj.parent
    while parent is not None:
        if is_utm_constructor(parent):
            return parent
        parent = parent.parent

    return None


def active_building(context):
    """Return BLENDERRAIL_PG_building for the active building, or None."""
    if context is None:
        return None

    if _USE_OBJECT_STORAGE:
        constructor = resolve_building_object(context)
        if constructor is None:
            return None
        return constructor.utm_building

    scene = context.scene
    if not hasattr(scene, "buildings"):
        return None
    buildings = scene.buildings
    if len(buildings) == 0:
        return None

    index = scene.active_building_index
    if index < 0 or index >= len(buildings):
        return None

    return buildings[index]


def active_building_object(context):
    """Return the constructor Object when using object storage, else base_object from scene PG."""
    if _USE_OBJECT_STORAGE:
        return resolve_building_object(context)

    building = active_building(context)
    if building is None:
        return None
    return getattr(building, "base_object", None)
