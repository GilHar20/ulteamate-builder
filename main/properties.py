import bpy
from . import operators
from ..utilities import gn_sockets



# ------------------------
# Property groups: Segment
# ------------------------

class BLENDERRAIL_PG_collect_objects(bpy.types.PropertyGroup):
    def _correct_uv_element(self, context):
        host_curve = self.host_curve
        obj = self.object
        for modifier in host_curve.modifiers:
            if modifier.type != "NODES" or "BLENDERRAIL_CurveElements_GN" not in modifier.name:
                continue
            if gn_sockets._get_socket_value(modifier, "Socket_4") == obj:
                gn_sockets._set_socket_value(modifier, "Socket_11", self.correct_uv)
                host_curve.update_tag()
                return
            
    def _up_stretch_element(self, context):
        host_curve = self.host_curve
        obj = self.object
        for modifier in host_curve.modifiers:
            if modifier.type != "NODES" or "BLENDERRAIL_CurveElements_GN" not in modifier.name:
                continue
            if gn_sockets._get_socket_value(modifier, "Socket_4") == obj:
                gn_sockets._set_socket_value(modifier, "Socket_6", self.up_stretched)
                host_curve.update_tag()
                return

    object : bpy.props.PointerProperty(
        name = "Element Object",
        description = "Pointer to object used for this element",
        type = bpy.types.Object
    )

    element_type : bpy.props.StringProperty(
        name = "Element Type",
        description = "What type of element is object used for",
        default = ""
    )

    host_curve : bpy.props.PointerProperty(
        name = "Host Curve",
        description = "Curve object of the curve PropertyGroup that holds the modifier referencing this object",
        type = bpy.types.Object
    )

    is_empty : bpy.props.BoolProperty(
        name = "Empty Element",
        description = "Instead of assigning an object, set element bounds to fill length on the curve",
        default = False
    )

    empty_bounds : bpy.props.FloatVectorProperty(
        name = "Empty Bounds",
        description = "Bounds of the empty element, used to fill length on the curve",
        default = (1.0, 0.2, 3.4),
        subtype = 'XYZ',
        size = 3,
    )

    correct_uv : bpy.props.BoolProperty(
        name = "Correct UV",
        description = "Stretch the element's UV attribute to match the scaling on the curve",
        default = True,
        update = _correct_uv_element
    )

    uv_name : bpy.props.StringProperty(
        name = "UV Name",
        description = "Name of UV attribute to correct, in case of the geometry stretching",
        default = "UVMap"
    )

    up_stretched : bpy.props.BoolProperty(
        name = "Is Stretched",
        description = "When true, the element will scale itself upwards to the height of the curve it is instancing on",
        default = False,
        update = _up_stretch_element
    )


class BLENDERRAIL_PG_elements_collection(bpy.types.PropertyGroup):   
    def _correct_uv_element(self, context):
        host_curve = self.host_curve
        obj = self.object
        for modifier in host_curve.modifiers:
            if modifier.type != "NODES" or "BLENDERRAIL_CurveElements_GN" not in modifier.name:
                continue
            if gn_sockets._get_socket_value(modifier, "Socket_4") == obj:
                gn_sockets._set_socket_value(modifier, "Socket_11", self.correct_uv)
                host_curve.update_tag()
                return

    def _up_stretch_element(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        host_curve = curve.curve_object
        for modifier in host_curve.modifiers:
            if modifier.type != "NODES" or "BLENDERRAIL_CurveElements_GN" not in modifier.name:
                continue
            gn_sockets._set_socket_value(modifier, "Socket_6", self.up_stretched)
            host_curve.update_tag()
            return    

    def _clamp_active_element_index(self, context):
        if self.active_element_index > len(self.objects) - 1:
            self.active_element_index = len(self.objects) - 1

    collect_method : bpy.props.EnumProperty(
        name = "Collect Method",
        description = "Method of assigning elements to the Target Collection of the floor",
        items = [
        ('OBJECTS', "Separate Objects", "Select objects and create a collection", 0),
        ('EXISTING', "Existing Collection", "Choose existing Target Collection", 1),
        ],
        default = 'OBJECTS'
    )

    objects : bpy.props.CollectionProperty(
        name = "Element Object",
        description = "Objects to insert into the Tartget Collection",
        type = BLENDERRAIL_PG_collect_objects
    )

    existing_collection : bpy.props.PointerProperty(
        name = "Existing Collection",
        description = "Collection of objects to insert into the Tartget Collection",
        type = bpy.types.Collection
    )

    active_element_index : bpy.props.IntProperty(
        name = "Active Element Index",
        default = 0,
        min = 0,
        max = 10000,
        update = _clamp_active_element_index
    )

    correct_uv : bpy.props.BoolProperty(
        name = "Correct UV",
        description = "Stretch the element's UV attribute to match the scaling on the curve",
        default = False,
        update = _correct_uv_element
    )

    up_stretched : bpy.props.BoolProperty(
        name = "Is Stretched",
        description = "When true, the element will scale itself upwards to the height of the curve it is instancing on",
        default = False,
        update = _up_stretch_element
    )


class BLENDERRAIL_PG_segment(bpy.types.PropertyGroup):   
    def _element_ID_update(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        curve.curve_object.update_tag()
        return

    def _clamp_fixed_number(self, context):
        if self.fixed_number < 1:
            self.fixed_number = 1
        return
    
    ID : bpy.props.IntProperty(
        name = "Segment ID",
        default = 0,
        min = 0,
        max = 10000
    )

    spline_ID : bpy.props.IntProperty(
        name = "Spline ID",
        default = 0,
        min = 0,
        max = 10000
    )

    spline_factor : bpy.props.FloatProperty(
        name = "Curve Factor",
        default = 0.0,
        min = 0.0,
        max = 1.0
    )

    spline_length : bpy.props.FloatProperty(
        name = "Curve Length",
        default = 0.0
    )

    element_ID : bpy.props.IntProperty(
        name = "Element ID",
        default = 0,
        min = 0,
        max = 10000,
        update = _element_ID_update
    )

    fit_method : bpy.props.EnumProperty(
        name = "Fit Method",
        description = "Methos for fitting element instances on the spline",
        items = [
        ('ORIGINAL', "Original", "Keep original length, no scaling, bisect element on spline ends", 0),
        ('FIT', "Fit", "Fit length of elements to the spline length, a=scale if necessary", 1),
        ('FIXED', "Fixed", "Fit fixed number of elements, scale elements accordingly", 2),
        ],
        default = 'FIT'
    )

    fixed_number : bpy.props.IntProperty(
        name = "Fixed Number",
        default = 5,
        min = 0,
        max = 10000,
        update = _clamp_fixed_number
    )


class BLENDERRAIL_PG_curve(bpy.types.PropertyGroup):
    def _update_curve_collection(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curves_collection = floor.curves_collection

        prev_name = self.get("_prev_curve_object_name", "")
        prev_obj = bpy.data.objects.get(prev_name) if prev_name else None
        new_obj = self.curve_object
        
        if prev_obj and prev_obj != new_obj:
            if curves_collection in prev_obj.users_collection:
                curves_collection.objects.unlink(prev_obj)

        if new_obj:
            if curves_collection not in new_obj.users_collection:
                curves_collection.objects.link(new_obj)


        self["_prev_curve_object_name"] = new_obj.name if new_obj else ""
        return
    
    def _clamp_active_segment_index(self, context):
        if self.active_segment_index > len(self.segments) - 1:
            self.active_segment_index = len(self.segments) - 1

    def _update_total_height(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        operators._calculate_floors_start_height(context, floors, False)
        return

    def _update_top_material(self, context):
        modifier = self.curve_object.modifiers[0]
        gn_sockets._set_socket_value(modifier, "Socket_19", self.top_material)
        self.curve_object.update_tag()
        return

    def _update_sides_material(self, context):
        modifier = self.curve_object.modifiers[0]
        gn_sockets._set_socket_value(modifier, "Socket_20", self.sides_material)
        self.curve_object.update_tag()
        return

    def _update_bottom_material(self, context):
        modifier = self.curve_object.modifiers[0]
        gn_sockets._set_socket_value(modifier, "Socket_21", self.bottom_material)
        self.curve_object.update_tag()
        return

    ID : bpy.props.IntProperty(
        name = "Curve ID",
        default = 0,
        min = 0,
        max = 10000
    )

    floor_ID : bpy.props.IntProperty(
        name = "Floor ID",
        default = 0,
        min = 0,
        max = 10000
    )

    curve_object : bpy.props.PointerProperty(
        name = "Input curve object",
        description = "Input curve geometry",
        type = bpy.types.Object,
        update = _update_curve_collection
    )

    segments : bpy.props.CollectionProperty(
        name = "Segments",
        description = "Segments of the curve object",
        type = BLENDERRAIL_PG_segment
    )

    active_segment_index : bpy.props.IntProperty(
        name = "Active Segment Index",
        default = 0,
        min = 0,
        max = 10000,
        update = _clamp_active_segment_index
    )

    inset : bpy.props.FloatProperty(
        name = "Inset",
        description = "Inset the curve inside or outside its normal",
        default = -0.2,
        min = -10.0,
        max = 10.0
    )

    height : bpy.props.FloatProperty(
        name = "Height",
        default = 3.4,
        min = 0.0,
        max = 100.0,
        update = _update_total_height
    )

    floor_ceiling : bpy.props.EnumProperty(
        name = "Floor Ceiling",
        description = "Select adding floor, ceiling or both",
        items = [
        ('NONE', "None", "None", 0),
        ('BOTTOM', "Bottom", "Add floor", 1),
        ('TOP', "Top", "Add ceiling", 2),
        ('BOTH', "Both", "Add ceiling and floor", 3),
        ],
        default = 'BOTTOM'
    )

    thickness : bpy.props.FloatProperty(
        name = "Thickness",
        description = "Thickness of the floor surface extrude",
        default = 0.3,
        min = 0.0,
        max = 10.0
    )

    direction_bottom : bpy.props.FloatProperty(
        name = "Direction Bottom",
        description = "Direction of the curve's bottom floor exturde, 1 = up, -1 = down",
        default = 1.0,
        min = -1.0,
        max = 1.0
    )

    direction_top : bpy.props.FloatProperty(
        name = "Direction Top",
        description = "Direction of the curve's top ceiling exturde, 1 = up, -1 = down",
        default = -1.0,
        min = -1.0,
        max = 1.0
    )

    top_material : bpy.props.PointerProperty(
        name = "Top Material",
        description = "Material for the top surface of the floor",
        type = bpy.types.Material,
        update = _update_top_material
    )

    sides_material : bpy.props.PointerProperty(
        name = "Sides Material",
        description = "Material for the sides surface of the floor",
        type = bpy.types.Material,
        update = _update_sides_material
    )

    bottom_material : bpy.props.PointerProperty(
        name = "Bottom Material",
        description = "Material for the bottom surface of the floor",
        type = bpy.types.Material,
        update = _update_bottom_material
    )

    select_method : bpy.props.EnumProperty(
        name = "Select Method",
        description = "Methos for selecting elements to instance on splines",
        items = [
        ('SEQUENCE', "Sequence", "Assign element for segment by order of the elements selection", 0),
        ('RANDOM', "Random", "Randomly assign elements for each segment", 1),
        ('CUSTOM', "Custom", "Manually select elements for each segment", 2),
        ],
        default = 'CUSTOM'
    )

    select_per_segment : bpy.props.BoolProperty(
        name = "Select Per Segment",
        description = "When True, a specific element will be set for each segment. Otherwise, a segment can instance multiple different elements",
        default = False
    )

    sequence_offset : bpy.props.IntProperty(
        name = "Sequece Offset",
        default = 0,
        min = -10000,
        max = 10000
    )

    random_index : bpy.props.IntProperty(
        name = "Random Index",
        default = 0,
        min = -10000,
        max = 10000
    )

    main_elements : bpy.props.PointerProperty(
        name = "Main Elements",
        description = "Collection of main elements",
        type = BLENDERRAIL_PG_elements_collection
    )

    corner_elements : bpy.props.PointerProperty(
        name = "Main Elements",
        description = "Collection of main elements",
        type = BLENDERRAIL_PG_elements_collection
    )


class BLENDERRAIL_PG_floor(bpy.types.PropertyGroup):
    def _update_total_height(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        operators._calculate_floors_start_height(context, floors, False)
        return

    ID : bpy.props.IntProperty(
        name = "Floor ID",
        default = 0,
        min = 0,
        max = 10000
    )

    is_linked : bpy.props.BoolProperty(
        name = "Floor Linked",
        description = "True if floor is linked to another floor",
        default = False
    )

    floor_visibility : bpy.props.BoolProperty(
        name = "Floor Visibility",
        description = "Turn floor visibility on and off",
        default = True
    )

    array : bpy.props.IntProperty(
        name = "Floor Array",
        default = 1,
        min = 1,
        max = 1000,
        update = _update_total_height
    )

    show_array : bpy.props.BoolProperty(
        name = "Show Array",
        description = "Show floor's levels from an array",
        default = False
    )

    total_height : bpy.props.FloatProperty(
        name = "Total Height",
        default = 0,
        min = 0.0,
        max = 10000.0
    )

    start_height : bpy.props.FloatProperty(
        name = "Total Height",
        default = 0,
        min = 0.0,
        max = 10000.0
    )

    curves_collection : bpy.props.PointerProperty(
        name = "Curves Collection",
        description = "Collection to store all floor's curves",
        type = bpy.types.Collection
    )

    instance_object : bpy.props.PointerProperty(
        name = "Instance Collection Object",
        description = "Collection object linked from the source floor curves_collection",
        type = bpy.types.Object
    )

    curves : bpy.props.CollectionProperty(
        name = "Input curve object",
        description = "Input curve geometry",
        type = BLENDERRAIL_PG_curve
    )

    active_curve_index : bpy.props.IntProperty(
        name = "Active Floor Index",
        default = 0,
        min = 0,
        max = 10000
    )


class BLENDERRAIL_PG_building(bpy.types.PropertyGroup):
    def _update_base_object_name(self, context):
        object = self.base_object
        object.name = self.name + "_Constructor"
        return
    
    ID : bpy.props.IntProperty(
        name = "Building ID",
        default = 0,
        min = 0,
        max = 10000
    )

    name : bpy.props.StringProperty(
        name = "Building Name",
        description = "Name of the building",
        default = "build",
        update = _update_base_object_name
    )
    
    base_object : bpy.props.PointerProperty(
        name = "Building",
        description = "Base geometry to hold the constract modifier",
        type = bpy.types.Object
    )

    # all_curves is not used. Will be in the future
    all_curves : bpy.props.CollectionProperty(
        name = "Input curve object",
        description = "Input curve geometry",
        type = BLENDERRAIL_PG_collect_objects
    )

    building_collection : bpy.props.PointerProperty(
        name = "Building Collection",
        description = "Main collection to hold all assets for the building",
        type = bpy.types.Collection
    )

    floors_collection : bpy.props.PointerProperty(
        name = "Floors Collection",
        description = "Collection to hold floors collection and their curve for the Construct node gorup",
        type = bpy.types.Collection
    )

    elements_collection : bpy.props.PointerProperty(
        name = "Elements Collection",
        description = "Collection to hold ALL building's elements linked to it",
        type = bpy.types.Collection
    )

    floors : bpy.props.CollectionProperty(
        name = "Floors",
        description = "List of all the floors in the building",
        type = BLENDERRAIL_PG_floor
    )

    active_floor_index : bpy.props.IntProperty(
        name = "Active Floor Index",
        default = 0,
        min = 0,
        max = 10000
    )
    
