# Printables interactive color investigation — September 5, 2026

Status: unresolved in Printables; publication files restored after testing.

Anson Liu's first-hand December 2023 implementation report identifies Material
Extension `m:colorgroup` as the encoding Printables reads, unlike core base
materials alone. The seasick color tool uses the same extension with face
properties and an object default. Our standard files already contain color
groups, per-face color references, and separate slicer filament metadata.

Three live A-tile experiments remained orange:
1. Set each mesh object's default property to the color group.
2. Remove slicer metadata/base materials and use six-digit color values.
3. Merge the colored preview into one mesh with explicit triangle colors.

The cited positive control, Ninja Pot 01, also rendered entirely orange when
its low and high 3MF files were opened in the current Printables viewer. Its
stored gallery thumbnail still shows multiple colors. This suggests a current
viewer problem, but does not establish its cause, scope, or an official outage.
No verified current internet workaround was found. Do not claim color support
is universally absent or that these print files lack filament assignments.

The experimental extra download was removed, and the standard A tile was
restored. BUZZLE has 47 models and 3 guides; BUZZELLO has 7 models and 3 guides.
Both galleries retain accurate geometry-rendered color images and both color
guides explain the viewer limitation. Printer colors still require checking
the sliced preview. No successful native-viewer fix is claimed.

Sources:
- https://ansonliu.com/2023/12/adding-blender-color-groups-support-for-printables/
- https://github.com/seasick/3mf-color-changer/blob/main/src/utils/3mf/changeColors.ts
- https://seasick.github.io/3mf-color-changer/
- https://www.printables.com/model/228038-ninja-pot-01

A useful next support report would include the A tile, the reference-model URL,
and screenshots showing their orange interactive previews. No support message
has been sent.
