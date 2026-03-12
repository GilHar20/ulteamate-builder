import os
import sys


LIBS_PATH = os.path.join(os.path.dirname(__file__), "libs")


def _ensure_libs_path():
    """Add the bundled libs/ folder to sys.path if not already there."""
    if LIBS_PATH not in sys.path:
        sys.path.insert(0, LIBS_PATH)


def check_ifcopenshell():
    """Returns True if ifcopenshell is importable (bundled or system)."""
    _ensure_libs_path()
    try:
        import ifcopenshell
        return True
    except ImportError:
        return False


def parse_ifc(filepath):
    """Parse an IFC file and return a simplified building dictionary."""

    _ensure_libs_path()
    import ifcopenshell
    import ifcopenshell.util.placement

    ifc = ifcopenshell.open(filepath)

    buildings = []
    for ifc_building in ifc.by_type("IfcBuilding"):
        building_data = {
            "name": ifc_building.Name or "Building",
            "floors": [],
        }

        storeys = _get_storeys(ifc_building)

        for i, storey in enumerate(storeys):
            next_elevation = storeys[i + 1]["elevation"] if i + 1 < len(storeys) else None
            height = (next_elevation - storey["elevation"]) if next_elevation else 3.0

            walls = _get_storey_walls(storey["entity"], ifc)

            building_data["floors"].append({
                "name": storey["name"],
                "height": height,
                "elevation": storey["elevation"],
                "walls": walls,
            })

        buildings.append(building_data)

    return buildings



# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_storeys(ifc_building):
    """Get sorted list of storeys for a building."""
    storeys = []

    for rel in ifc_building.IsDecomposedBy or []:
        for obj in rel.RelatedObjects:
            if obj.is_a("IfcBuildingStorey"):
                storeys.append({
                    "entity": obj,
                    "name": obj.Name or f"Storey {len(storeys)}",
                    "elevation": obj.Elevation or 0.0,
                })

    storeys.sort(key=lambda s: s["elevation"])
    return storeys


def _get_storey_walls(storey_entity, ifc):
    """Extract wall data from a storey."""
    walls = []

    for rel in storey_entity.ContainsElements or []:
        for element in rel.RelatedElements:
            if not element.is_a("IfcWall"):
                continue

            wall_data = _extract_wall(element, ifc)
            if wall_data:
                walls.append(wall_data)

    return walls


def _extract_wall(wall_entity, ifc):
    """Extract simplified wall data from an IfcWall."""
    wall_type = _get_type_name(wall_entity)
    axis_points = _get_wall_axis(wall_entity)
    thickness = _get_wall_thickness(wall_entity)

    height = None
    for rel in wall_entity.IsDefinedBy or []:
        if rel.is_a("IfcRelDefinesByProperties"):
            pset = rel.RelatingPropertyDefinition
            if hasattr(pset, "HasProperties"):
                for prop in pset.HasProperties:
                    if hasattr(prop, "Name") and prop.Name == "Height":
                        height = _get_nominal_value(prop)

    return {
        "type_name": wall_type,
        "axis_points": axis_points,
        "thickness": thickness or 0.2,
        "height": height,
    }


def _get_type_name(element):
    """Get the type name of an IFC element."""
    for rel in element.IsDefinedBy or []:
        if rel.is_a("IfcRelDefinesByType"):
            element_type = rel.RelatingType
            return element_type.Name or "Unnamed Type"
    return element.Name or "Unknown"


def _get_wall_axis(wall_entity):
    """
    Extract the wall centerline axis as a list of (x, y, z) points.
    Looks for the 'Axis' representation, falls back to placement.
    """
    if wall_entity.Representation:
        for rep in wall_entity.Representation.Representations:
            if rep.RepresentationIdentifier == "Axis":
                return _extract_polyline_points(rep)

    placement = wall_entity.ObjectPlacement
    if placement:
        try:
            import ifcopenshell.util.placement
            matrix = ifcopenshell.util.placement.get_local_placement(placement)
            origin = (matrix[0][3], matrix[1][3], matrix[2][3])
            return [origin]
        except Exception:
            pass

    return []


def _extract_polyline_points(representation):
    """Extract points from a polyline representation."""
    points = []
    for item in representation.Items:
        if item.is_a("IfcPolyline"):
            for pt in item.Points:
                coords = pt.Coordinates
                if len(coords) == 2:
                    points.append((coords[0], coords[1], 0.0))
                else:
                    points.append(tuple(coords))
        elif item.is_a("IfcTrimmedCurve"):
            basis = item.BasisCurve
            if basis.is_a("IfcLine"):
                pnt = basis.Pnt.Coordinates
                points.append(tuple(pnt) if len(pnt) == 3 else (pnt[0], pnt[1], 0.0))
    return points


def _get_wall_thickness(wall_entity):
    """Try to extract wall thickness from material layer set."""
    for rel in wall_entity.HasAssociations or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            mat = rel.RelatingMaterial
            layer_set = None

            if mat.is_a("IfcMaterialLayerSetUsage"):
                layer_set = mat.ForLayerSet
            elif mat.is_a("IfcMaterialLayerSet"):
                layer_set = mat

            if layer_set:
                total = sum(
                    layer.LayerThickness
                    for layer in layer_set.MaterialLayers
                    if layer.LayerThickness
                )
                return total if total > 0 else None

    return None


def _get_nominal_value(prop):
    """Safely extract a numeric nominal value from an IFC property."""
    if hasattr(prop, "NominalValue") and prop.NominalValue:
        val = prop.NominalValue.wrappedValue
        if isinstance(val, (int, float)):
            return float(val)
    return None
