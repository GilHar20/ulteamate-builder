# ULTEAMMATE Builder

A blender plugin for streamlined creation of procedural building.

## Version 0.9.0 beta:

### Fixes

* `sync_from_modifier_stack` saves element selection settings per segment, as those settings are now per segment and not per curve.
* `sync_from_modifier_stack` saves linked_ID, the new property for linked floor to document the ID of source floor they were linked from.

### Cleanup

* Prefenreces show correct masaage if not asset library recognized: `"Asset library is not recognized"`
* Removed `_set_attribute_driver()` function from `main/operators.py`. Drivers are not used in the plugin anymore.
* Blender version dropped to 5.2 instead of 5.3. Addon not using any 5.3 exclusive features at the moment.

### Known Limits

* **Corner Elements** currently only have the ability to be randomly selected. Option to choose between `SEQUENCE0`, `RANDOM` and `INPUT` like **Main Elements** to be added in future updates.
* Viewport GUI can show elements added to a curve, but will only take effect on segments set to select method `INPUT`. More comprehensive viewport GUI panel will be implemented in future updates.