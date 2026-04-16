import bpy
from . import operators



# ------------------------
# Property groups: Segment
# ------------------------

class BLENDERRAIL_PG_collect_objects(bpy.types.PropertyGroup):   
    object : bpy.props.PointerProperty(
        name = "Element Object",
        type = bpy.types.Object
    )


class BLENDERRAIL_PG_elements_collection(bpy.types.PropertyGroup):   
    collect_method : bpy.props.EnumProperty(
        name = "Collect Method",
        description = "Method of assigning elements to the Target Collection of the floor",
        items = [
        ('OBJECTS', "Objects", "Select objects and create a collection", 0),
        ('EXISTING', "Existing", "Choose existing Target Collection", 1),
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

    target_collection : bpy.props.PointerProperty(
        name = "Target Collection",
        description = "Collection of elements to instance along the curve splines",
        type = bpy.types.Collection
    )


class BLENDERRAIL_PG_segment(bpy.types.PropertyGroup):   
    def _element_ID_update(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        curve.curve_object.update_tag()
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
        max = 10000
    )


class BLENDERRAIL_PG_curve(bpy.types.PropertyGroup):
    def _update_total_height(self, context):
        operators._calculate_floors_start_height(context, None)
        return

    ID : bpy.props.IntProperty(
        name = "Segment ID",
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


    inset : bpy.props.FloatProperty(
        name = "Inset",
        description = "Inset the curve inside or outside its normal",
        default = -0.2,
        min = -10.0,
        max = 10.0
    )

    curve_object : bpy.props.PointerProperty(
        name = "Input curve object",
        description = "Input curve geometry",
        type = bpy.types.Object
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
        max = 10000
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
        default = True
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
        operators._calculate_floors_start_height(context, None)
        return

    ID : bpy.props.IntProperty(
        name = "Floor ID",
        default = 0,
        min = 0,
        max = 10000
    )

    uid : bpy.props.StringProperty(
        name = "Floor uuid",
        default = "",
    )

    source_uid : bpy.props.StringProperty(
        name = "Source Floor uuid",
        default = "",
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
    
