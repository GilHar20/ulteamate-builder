import bpy
from . import operators
from ..utilities import gn_sockets, resolve_building_object as resolve



# ---------------
# Property groups
# ---------------

class UTMBUILDER_PG_utm_element(bpy.types.PropertyGroup):
    def _get_curve_modifier(self, context):
        resolved = resolve._resolve_building_object(context)
        _, building = resolved
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        modifier = gn_sockets.curve_elements_modifier(curve, self.ID, self.element_type)
        return modifier

    def _update_ID(self, context):
        modifier = self._get_curve_modifier(context)
        gn_sockets._set_socket_value(modifier, "ID", self.ID)
        self.host_curve.update_tag()
        return

    def _update_object(self, context):
        modifier = self._get_curve_modifier(context)
        gn_sockets._set_socket_value(modifier, "object", self.object)
        self.host_curve.update_tag()
        return

    def _update_element_type(self, context):
        modifier = self._get_curve_modifier(context)
        gn_sockets._set_socket_value(modifier, "element_type", self.element_type)
        self.host_curve.update_tag()
        return

    def _update_is_empty(self, context):
        modifier = self._get_curve_modifier(context)
        gn_sockets._set_socket_value(modifier, "is_empty", self.is_empty)
        self.host_curve.update_tag()
        return

    def _update_empty_bounds(self, context):
        modifier = self._get_curve_modifier(context)
        gn_sockets._set_socket_value(modifier, "empty_bounds", self.empty_bounds)
        self.host_curve.update_tag()
        return

    def _update_correct_uv(self, context):
        modifier = self._get_curve_modifier(context)
        gn_sockets._set_socket_value(modifier, "correct_uv", self.correct_uv)
        self.host_curve.update_tag()
        return

    def _update_up_stretched(self, context):
        modifier = self._get_curve_modifier(context)
        gn_sockets._set_socket_value(modifier, "up_stretched", self.up_stretched)
        self.host_curve.update_tag()
        return

    ID : bpy.props.IntProperty(
        name = "Element ID",
        default = 0,
        min = 0,
        max = 10000,
        update = _update_ID
    )

    is_selected : bpy.props.BoolProperty(
        name = "Is Selected",
        description = "Element is selected",
        default = False
    )

    object : bpy.props.PointerProperty(
        name = "Element Object",
        description = "Pointer to object used for this element",
        type = bpy.types.Object,
        update = _update_object
    )

    element_type : bpy.props.StringProperty(
        name = "Element Type",
        description = "What type of element is object used for",
        default = "",
        update = _update_element_type
    )

    host_curve : bpy.props.PointerProperty(
        name = "Host Curve",
        description = "Curve object of the curve PropertyGroup that holds the modifier referencing this object",
        type = bpy.types.Object
    )

    is_empty : bpy.props.BoolProperty(
        name = "Empty Element",
        description = "Instead of assigning an object, set element bounds to fill length on the curve",
        default = False,
        update = _update_is_empty,
    )

    empty_bounds : bpy.props.FloatVectorProperty(
        name = "Empty Bounds",
        description = "Bounds of the empty element, used to fill length on the curve",
        default = (1.0, 0.2, 3.4),
        subtype = 'XYZ',
        size = 3,
        update = _update_empty_bounds,
    )

    correct_uv : bpy.props.BoolProperty(
        name = "Correct UV",
        description = "Stretch the element's UV attribute to match the scaling on the curve",
        default = True,
        update = _update_correct_uv
    )

    uv_name : bpy.props.StringProperty(
        name = "UV Name",
        description = "Name of UV attribute to correct, in case of the geometry stretching",
        default = "UVMap"
    )

    up_stretched : bpy.props.BoolProperty(
        name = "Is Stretched",
        description = "When true, the element will scale itself upwards to the height of the curve it is instancing on",
        default = True,
        update = _update_up_stretched
    )


class UTMBUILDER_PG_utm_elements_group(bpy.types.PropertyGroup):   
    def _clamp_active_element_index(self, context):
        if self.active_element_index > len(self.objects) - 1:
            self.active_element_index = len(self.objects) - 1

    group_element_type : bpy.props.StringProperty(
        name = "Element Type",
        description = "What type of element is object used for",
        default = ""
    )

    objects : bpy.props.CollectionProperty(
        name = "Element Object",
        description = "Objects to insert into the Tartget Collection",
        type = UTMBUILDER_PG_utm_element
    )

    active_element_index : bpy.props.IntProperty(
        name = "Active Element Index",
        default = 0,
        min = 0,
        max = 10000,
        update = _clamp_active_element_index
    )


class UTMBUILDER_PG_utm_curve_segment(bpy.types.PropertyGroup):   
    def _get_segment_modifier(self, context):
        building = self.id_data.utm_building
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        modifier = gn_sockets.element_id_modifier(curve, self.ID)
        return modifier

    def _get_active_curve(self, context):
        building = self.id_data.utm_building
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        return curve

    def _update_segment_ID(self, context):
        modifier = self._get_segment_modifier(context)
        gn_sockets._set_socket_value(modifier, "segment_index", self.ID)
        curve = self._get_active_curve(context)
        curve.curve_object.update_tag()
        return
    
    def _update_fit_method(self, context):
        modifier = self._get_segment_modifier(context)
        gn_sockets._set_socket_value(modifier, "fit_method", self.fit_method)
        curve = self._get_active_curve(context)
        curve.curve_object.update_tag()
        return
    
    def _update_fixed_number(self, context):
        if self.fixed_number < 1:
            self.fixed_number = 1
        modifier = self._get_segment_modifier(context)
        gn_sockets._set_socket_value(modifier, "fixed_number", self.fixed_number)
        curve = self._get_active_curve(context)
        curve.curve_object.update_tag()
        return

    def _update_select_method(self, context):
        modifier = self._get_segment_modifier(context)
        gn_sockets._set_socket_value(modifier, "select_method", self.select_method)
        curve = self._get_active_curve(context)
        curve.curve_object.update_tag()
        return

    def _update_select_per_segment(self, context):
        modifier = self._get_segment_modifier(context)
        gn_sockets._set_socket_value(modifier, "select_per_segment", self.select_per_segment)
        curve = self._get_active_curve(context)
        curve.curve_object.update_tag()
        return

    def _update_sequence_offset(self, context):
        modifier = self._get_segment_modifier(context)
        gn_sockets._set_socket_value(modifier, "sequence_offset", self.sequence_offset)
        curve = self._get_active_curve(context)
        curve.curve_object.update_tag()
        return

    def _update_random_index(self, context):
        modifier = self._get_segment_modifier(context)
        gn_sockets._set_socket_value(modifier, "random_index", self.random_index)
        curve = self._get_active_curve(context)
        curve.curve_object.update_tag()
        return
    
    def _update_element_ID(self, context):
        modifier = self._get_segment_modifier(context)
        gn_sockets._set_socket_value(modifier, "element_index", self.element_index)
        curve = self._get_active_curve(context)
        curve.curve_object.update_tag()
        return
    
    ID : bpy.props.IntProperty(
        name = "Segment ID",
        default = 0,
        min = 0,
        max = 10000,
        update = _update_segment_ID
    )

    is_selected : bpy.props.BoolProperty(
        name = "Is Selected",
        description = "Segment is selected",
        default = False
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

    fit_method : bpy.props.EnumProperty(
        name = "Fit Method",
        description = "Methos for fitting element instances on the spline",
        items = [
        ('ORIGINAL', "Original", "Keep original length, no scaling, bisect element on spline ends", 0),
        ('FIT', "Fit", "Fit length of elements to the spline length, a=scale if necessary", 1),
        ('FIXED', "Fixed", "Fit fixed number of elements, scale elements accordingly", 2),
        ],
        default = 'FIT',
        update = _update_fit_method
    )

    fixed_number : bpy.props.IntProperty(
        name = "Fixed Number",
        default = 5,
        min = 0,
        max = 10000,
        update = _update_fixed_number
    )

    select_method : bpy.props.EnumProperty(
        name = "Select Method",
        description = "Methos for selecting elements to instance on splines",
        items = [
        ('SEQUENCE', "Sequence", "Assign element for segment by order of the elements selection", 0),
        ('RANDOM', "Random", "Randomly assign elements for each segment", 1),
        ('INPUT', "Input", "Select specific element index for the segment", 2),
        ],
        default = 'INPUT',
        update = _update_select_method
    )

    select_per_segment : bpy.props.BoolProperty(
        name = "Select Per Segment",
        description = "When True, a specific element will be set for each segment. Otherwise, a segment can instance multiple different elements",
        default = False,
        update = _update_select_per_segment
    )

    sequence_offset : bpy.props.IntProperty(
        name = "Sequece Offset",
        default = 0,
        min = -10000,
        max = 10000,
        update = _update_sequence_offset
    )

    random_index : bpy.props.IntProperty(
        name = "Random Index",
        default = 0,
        min = -10000,
        max = 10000,
        update = _update_random_index
    )

    element_index : bpy.props.IntProperty(
        name = "Element ID",
        default = 0,
        min = 0,
        max = 10000,
        update = _update_element_ID
    )


class UTMBUILDER_PG_utm_curve(bpy.types.PropertyGroup):
    def _clamp_active_segment_index(self, context):
        if self.active_segment_index > len(self.segments) - 1:
            self.active_segment_index = len(self.segments) - 1

    def _update_inset(self, context):
        modifier = gn_sockets.curve_attributes_modifier(self)
        gn_sockets._set_socket_value(modifier, "inset", self.inset)
        self.curve_object.update_tag()
        return

    def _update_total_height(self, context):
        building = self.id_data.utm_building
        operators._calculate_floors_start_height(context, building.floors, False)

        modifier = gn_sockets.curve_attributes_modifier(self)
        gn_sockets._set_socket_value(modifier, "height", self.height)

        floor = building.floors[building.active_floor_index]
        for curve_pg in floor.curves:
            modifier = gn_sockets.curve_attributes_modifier(curve_pg)
            gn_sockets._set_socket_value(modifier, "maximum_height", floor.maximum_height)
            curve_pg.curve_object.update_tag()
        return

    def _update_floor_ceiling(self, context):
        modifier = gn_sockets.curve_attributes_modifier(self)
        gn_sockets._set_socket_value(modifier, "floor_ceiling", self.floor_ceiling)
        self.curve_object.update_tag()
        return

    def _update_thickness(self, context):
        modifier = gn_sockets.curve_attributes_modifier(self)
        gn_sockets._set_socket_value(modifier, "thickness", self.thickness)
        self.curve_object.update_tag()
        return

    def _update_direction_bottom(self, context):
        modifier = gn_sockets.curve_attributes_modifier(self)
        gn_sockets._set_socket_value(modifier, "direction_bottom", self.direction_bottom)
        self.curve_object.update_tag()
        return

    def _update_direction_top(self, context):
        modifier = gn_sockets.curve_attributes_modifier(self)
        gn_sockets._set_socket_value(modifier, "direction_top", self.direction_top)
        self.curve_object.update_tag()
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

    is_selected : bpy.props.BoolProperty(
        name = "Is Selected",
        description = "Curve is selected",
        default = False
    )

    curve_object : bpy.props.PointerProperty(
        name = "Input curve object",
        description = "Input curve geometry",
        type = bpy.types.Object
    )

    segments : bpy.props.CollectionProperty(
        name = "Segments",
        description = "Segments of the curve object",
        type = UTMBUILDER_PG_utm_curve_segment
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
        default = 0.2,
        min = -10.0,
        max = 10.0,
        update = _update_inset
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
        default = 'BOTTOM',
        update = _update_floor_ceiling
    )

    thickness : bpy.props.FloatProperty(
        name = "Thickness",
        description = "Thickness of the floor surface extrude",
        default = 0.3,
        min = 0.0,
        max = 10.0,
        update = _update_thickness
    )

    direction_bottom : bpy.props.FloatProperty(
        name = "Direction Bottom",
        description = "Direction of the curve's bottom floor exturde, 1 = up, -1 = down",
        default = 1.0,
        min = -1.0,
        max = 1.0,
        update = _update_direction_bottom
    )

    direction_top : bpy.props.FloatProperty(
        name = "Direction Top",
        description = "Direction of the curve's top ceiling exturde, 1 = up, -1 = down",
        default = -1.0,
        min = -1.0,
        max = 1.0,
        update = _update_direction_top
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

    main_elements : bpy.props.PointerProperty(
        name = "Main Elements",
        description = "Group of main elements",
        type = UTMBUILDER_PG_utm_elements_group
    )

    corner_elements : bpy.props.PointerProperty(
        name = "Corner Elements",
        description = " Group of corner elements",
        type = UTMBUILDER_PG_utm_elements_group
    )


class UTMBUILDER_PG_utm_floor(bpy.types.PropertyGroup):
    def _update_total_height(self, context):
        for curve_pg in self.curves:
            modifier = gn_sockets.curve_attributes_modifier(curve_pg)
            gn_sockets._set_socket_value(modifier, "array", self.array)
        building = self.id_data.utm_building
        operators._calculate_floors_start_height(context, building.floors, False)
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

    linked_ID : bpy.props.IntProperty(
        name = "Source Floor ID",
        description = "ID of the source floor",
        default = -1,
        min = -1
    )

    instance_object : bpy.props.PointerProperty(
        name = "Instance Collection Object",
        description = "Collection object linked from the source floor curves_collection",
        type = bpy.types.Object
    )

    floor_visibility : bpy.props.BoolProperty(
        name = "Floor Visibility",
        description = "Turn floor visibility on and off",
        default = True
    )

    array : bpy.props.IntProperty(
        name = "Floor Array",
        description = "Number of floor exact duplicate to stack vertically",
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

    maximum_height : bpy.props.FloatProperty(
        name = "Maximum Height",
        description = "The height distane between the floor's lowest and heighst point, across all its curve object's heights",
        default = 0,
        min = 0.0,
        max = 10000.0
    )

    total_height : bpy.props.FloatProperty(
        name = "Total Height",
        description = "The overall height the floor occupies. Calculated as maximum height * array",
        default = 0,
        min = 0.0,
        max = 10000.0
    )

    start_height : bpy.props.FloatProperty(
        name = "Total Height",
        description = "Height vakue (Z) of the first floor curve",
        default = 0,
        min = 0.0,
        max = 10000.0
    )

    curves_collection : bpy.props.PointerProperty(
        name = "Curves Collection",
        description = "Collection to store all floor's curves",
        type = bpy.types.Collection
    )

    curves : bpy.props.CollectionProperty(
        name = "Input curve object",
        description = "Input curve geometry",
        type = UTMBUILDER_PG_utm_curve
    )

    active_curve_index : bpy.props.IntProperty(
        name = "Active Floor Index",
        default = 0,
        min = 0,
        max = 10000
    )


class UTMBUILDER_PG_utm_building(bpy.types.PropertyGroup):
    def _update_base_object_name(self, context):
        base_object = self.base_object if self.base_object else self.id_data
        if base_object and getattr(base_object, "type", None) == 'MESH':
            base_object.name = self.name + "_Constructor"
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

    is_utm_building : bpy.props.BoolProperty(
        name = "Valid UTM Building",
        description = "Makes this object is a valid ULTEAMMATE Builder base object",
        default = False,
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
        type = UTMBUILDER_PG_utm_floor
    )

    active_floor_index : bpy.props.IntProperty(
        name = "Active Floor Index",
        default = 0,
        min = 0,
        max = 10000
    )

    show_segments_grid : bpy.props.BoolProperty(
        name = "Show Segments Grid",
        default = True,
    )

    segments_grid_columns : bpy.props.IntProperty(
        name = "Segments Grid Columns",
        default = 6,
        min = 1,
        max = 10,
    )

