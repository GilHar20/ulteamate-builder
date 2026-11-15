# ULTEAMMATE Builder

A Blender add-on for streamlined creation of spline-based procedural buildings.

**Requirements:** Blender 5.2 or newer.

## Beta disclaimer

This is a **beta** release (see [CHANGELOG.md](CHANGELOG.md)). Features and workflows may change. **Save your `.blend` files often** and keep backups before testing on production scenes. Report problems using the contact channel below.

## License

ULTEAMMATE Builder is free software licensed under the **GNU General Public License v3**. See [LICENSE](LICENSE) for the full text. Copyright (C) Gilad Harnik.

## Installation

Install using standard Blender add-on methods:

- Drag and drop the `.zip` onto the Blender window, or
- **Edit → Preferences → Add-ons** → install menu → **Install from disk…** → select the zip.

Enable **ULTEAMMATE Builder** in the add-ons list.

**After installation:** set up the asset library (below) before using the main panel.

## Asset library setup

The add-on registers an asset library named **ULTEAMMATE** in Blender’s File Paths.

1. Open **Edit → Preferences → Add-ons → ULTEAMMATE Builder** (expand the add-on).
2. Set **Asset Library Path** if needed (default uses Blender’s user Assets folder).
3. Click **Register Asset Library** or **Update Asset Library** to copy node groups and category files into the library folder.

If the library is not registered, the **ULTEAMMATE** sidebar panel shows a warning and a shortcut to the addon's preferences for proper library setup.

## Quick start

Open the **3D View** sidebar (press **N**) → category **ULTEAMMATE** → **ULTEAMMATE Builder**.

1. **Add New Building**: Creates a new base object with first floor and one circular curve. Creates collection hierarchy.
2. **Floor**: Use **Floors** list **+** to add floors. You can select the active floor to work on as needed. The **gear** icon is floor settings, you can array a floor upwards.
3. **Curve**: On the active floor, use **+** button to add a curve object. You can either create or pick an existing curve object. The **gear** icon is curve settings. You can control height, floor and cieling generation and materials.
4. **Elements**: On the active curve, use **+** button to add an element and choose its settings. You can change settings later by pressing the **gear** icon element settings. You can control element's reaction to  curve's height and stretching, you can set element as **empty**.
    The two types of elements:
    1. **Main Elements**: Elements to be arrayed accros the spline. Make up the majority of the building.
    2. **Corner Elements**: Elements to be placed at the ends of segments. This will trim curve length, reducing the space for **main elements**.
5. **Refresh**: Sometimes results may be unexpected. Click **Refresh** to recalculate the entire building.

6. (**Optional**) Press **Live Edit** for selecting elements per segment while in edit mode. This will react to the current control point selection. Currently only works for segment with **INPUT** set as their **Select Method**

## Contact and issues

**Author:** Gilad Harnik

**Beta feedback and bugs:** Report issues on the [project tracker](https://github.com/GilHar20/ulteamate-builder/issues). Include Blender version, add-on version, steps to reproduce, and a sample `.blend` if possible.
