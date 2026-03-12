import bpy

from .parser import check_ifcopenshell, parse_ifc



# ---------------------------------------------------------------------------
# Operator: Import IFC file
# ---------------------------------------------------------------------------

class BLENDERRAIL_OT_import_ifc(bpy.types.Operator):
    bl_idname = "blenderrail.import_ifc"
    bl_label = "Import IFC to BlenderRail"
    bl_description = "Parse an IFC file and populate BlenderRail buildings"
    bl_options = {"REGISTER", "UNDO"}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    filter_glob: bpy.props.StringProperty(
        default="*.ifc",
        options={"HIDDEN"},
    )

    def invoke(self, context, event):
        if not check_ifcopenshell():
            self.report(
                {"ERROR"},
                "ifcopenshell not found. Place the ifcopenshell package in ifcimporter/libs/"
            )
            return {"CANCELLED"}

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if not self.filepath:
            self.report({"WARNING"}, "No file selected")
            return {"CANCELLED"}

        try:
            ifc_buildings = parse_ifc(self.filepath)
        except Exception as e:
            self.report({"ERROR"}, f"Failed to parse IFC: {e}")
            return {"CANCELLED"}

        if not ifc_buildings:
            self.report({"WARNING"}, "No buildings found in IFC file")
            return {"CANCELLED"}

        scene = context.scene
        created_count = 0

        for ifc_bld in ifc_buildings:
            bpy.ops.blenderrail.generate_building()
            building = scene.buildings[scene.active_building_index]

            for ifc_floor in ifc_bld["floors"]:
                floor = building.floors.add()
                floor.height = ifc_floor["height"]
                floor.total_height = ifc_floor["elevation"]

                curve_obj = _create_floor_curve(
                    ifc_floor, ifc_bld["name"], context
                )
                if curve_obj:
                    floor.curve = curve_obj

                for wall in ifc_floor["walls"]:
                    segment = floor.segments.add()
                    segment.ID = len(floor.segments) - 1

            created_count += 1

        scene.active_building_index = max(0, len(scene.buildings) - 1)

        self.report(
            {"INFO"},
            f"Imported {created_count} building(s) from IFC"
        )
        return {"FINISHED"}



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_floor_curve(ifc_floor, building_name, context):
    """
    Build a Blender curve object from wall axis points on a floor.
    Connects wall axes into a single polyline curve.
    """
    all_points = []
    for wall in ifc_floor["walls"]:
        all_points.extend(wall["axis_points"])

    if not all_points:
        return None

    curve_data = bpy.data.curves.new(
        name=f"{building_name}_{ifc_floor['name']}_curve",
        type="CURVE"
    )
    curve_data.dimensions = "3D"

    spline = curve_data.splines.new("POLY")
    spline.points.add(len(all_points) - 1)

    for i, pt in enumerate(all_points):
        x, y, z = pt
        spline.points[i].co = (x, y, z, 1.0)

    curve_obj = bpy.data.objects.new(curve_data.name, curve_data)
    context.collection.objects.link(curve_obj)

    return curve_obj
