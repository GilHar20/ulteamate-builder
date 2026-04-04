import bpy

# Full path to the .blend file
blend_path = r"C:\Users\iTeroFlex\Desktop\GN\GeometryNodesModifiers\GeoNodesModifiers_MASTER.blend"

# Name of the node group inside that file
node_name = "Street_PRESET"


# Load the node group
with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
    if node_name in data_from.node_groups:
        data_to.node_groups.append(node_name)
    else:
        raise Exception(f"Node group '{node_name}' not found in file")


# Get the appended node group
node_group = bpy.data.node_groups.get(node_name)


# Ensure it's Geometry Nodes
if node_group and node_group.bl_idname == "GeometryNodeTree":
    print("✅ Loaded Geometry Node:", node_group.name)

    # Optional: assign to active object
    obj = bpy.context.active_object
    if obj:
        mod = obj.modifiers.new(name=node_group.name, type='NODES')
        mod.node_group = node_group
else:
    print("❌ Not a Geometry Node group")