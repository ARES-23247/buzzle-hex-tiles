// ========================================================================
// Parametric Dual-Color Hexagonal "Hive" 3D Printable Tile
// OpenSCAD Customizer Compatible
// ========================================================================

/* [Tile Dimensions] */
// Flat-to-flat diameter in mm (33.02 mm = 1.3 inches)
tile_flat_to_flat = 33.02; // [20.0:0.1:100.0]

// Total tile height/thickness in mm
tile_height = 4.8; // [2.0:0.1:15.0]

// 45-degree top perimeter chamfer size in mm
chamfer = 0.8; // [0.0:0.1:3.0]

// Recessed inlay depth for the insect glyph in mm
inlay_depth = 0.8; // [0.2:0.1:3.0]

// Additional raised emboss height above tile surface (0 for flush)
emboss_height = 0.0; // [0.0:0.1:3.0]

/* [Insect Selection] */
// Choose the insect piece to render
insect_type = "queen_bee"; // [queen_bee:Queen Bee, spider:Spider, beetle:Beetle, grasshopper:Grasshopper, ant:Soldier Ant, mosquito:Mosquito, ladybug:Ladybug, pillbug:Pillbug]

/* [Rendering & Multi-Material Mode] */
// Select which parts to render
render_mode = "both"; // [both:Dual Color Assembly, base_only:Base Tile Only, insect_only:Insect Inlay Only]

// Preview color for base tile (Ivory or Carbon Black)
color_base = "Ivory";

// Preview color for insect inlay (e.g. Gold, Red, Green, Blue, Black)
color_insect = "#E65100";

/* [Hidden] */
$fn = 6; // Regular hexagon

// Calculate Hexagon radii
r_flat = tile_flat_to_flat / 2.0;
r_vertex = r_flat / cos(30);

r_top_flat = (tile_flat_to_flat - 2 * chamfer) / 2.0;
r_top_vertex = r_top_flat / cos(30);

// --- 2D Hexagon Profile ---
module hex_profile(radius) {
    rotate([0, 0, 30])
    circle(r = radius, $fn = 6);
}

// --- Solid Chamfered Base Hexagon ---
module solid_hex_base() {
    hull() {
        linear_extrude(height = max(0.01, tile_height - chamfer))
            hex_profile(r_vertex);
            
        translate([0, 0, tile_height - 0.01])
            linear_extrude(height = 0.01)
                hex_profile(r_top_vertex);
    }
}

// --- 2D Insect Outlines ---
module insect_queen_bee_2d() {
    // Head & Crown
    translate([0, 4.8, 0]) circle(r = 1.8, $fn=32);
    polygon([[-2.0, 5.2], [-2.0, 8.0], [-1.0, 6.6], [0, 8.6], [1.0, 6.6], [2.0, 8.0], [2.0, 5.2]]);
    // Thorax
    translate([0, 1.8, 0]) scale([2.5/2, 2.0/2, 1]) circle(r=2, $fn=32);
    // Abdomen with stripes
    difference() {
        offset(r = 0.8) polygon([[0, -7.5], [-3.0, -1.0], [3.0, -1.0]]);
        translate([-4, -2.4, 0]) square([8, 0.7]);
        translate([-3.5, -4.3, 0]) square([7, 0.7]);
        translate([-2.5, -6.0, 0]) square([5, 0.6]);
    }
    // Wings
    translate([-5.8, 3.0, 0]) rotate([0, 0, -35]) scale([5.0/2, 1.8/2, 1]) circle(r=2, $fn=32);
    translate([5.8, 3.0, 0]) rotate([0, 0, 35]) scale([5.0/2, 1.8/2, 1]) circle(r=2, $fn=32);
    translate([-5.0, 1.0, 0]) rotate([0, 0, -55]) scale([3.8/2, 1.4/2, 1]) circle(r=2, $fn=32);
    translate([5.0, 1.0, 0]) rotate([0, 0, 55]) scale([3.8/2, 1.4/2, 1]) circle(r=2, $fn=32);
}

module insect_spider_2d() {
    translate([0, 3.0, 0]) circle(r = 1.7, $fn=32);
    translate([0, -2.5, 0]) scale([3.2/2, 4.2/2, 1]) circle(r=2, $fn=32);
    // 8 Legs
    for (s = [-1, 1]) {
        scale([s, 1, 1]) {
            hull() { translate([1.0, 2.8, 0]) circle(r=0.45, $fn=16); translate([4.5, 6.2, 0]) circle(r=0.45, $fn=16); }
            hull() { translate([4.5, 6.2, 0]) circle(r=0.45, $fn=16); translate([7.5, 8.8, 0]) circle(r=0.45, $fn=16); }
            hull() { translate([1.2, 1.8, 0]) circle(r=0.45, $fn=16); translate([6.5, 3.8, 0]) circle(r=0.45, $fn=16); }
            hull() { translate([6.5, 3.8, 0]) circle(r=0.45, $fn=16); translate([9.5, 4.2, 0]) circle(r=0.45, $fn=16); }
            hull() { translate([1.2, 0.5, 0]) circle(r=0.45, $fn=16); translate([6.8, -1.0, 0]) circle(r=0.45, $fn=16); }
            hull() { translate([6.8, -1.0, 0]) circle(r=0.45, $fn=16); translate([9.0, -3.5, 0]) circle(r=0.45, $fn=16); }
            hull() { translate([1.0, -1.0, 0]) circle(r=0.45, $fn=16); translate([5.5, -4.5, 0]) circle(r=0.45, $fn=16); }
            hull() { translate([5.5, -4.5, 0]) circle(r=0.45, $fn=16); translate([7.0, -8.5, 0]) circle(r=0.45, $fn=16); }
        }
    }
}

module insect_2d() {
    if (insect_type == "queen_bee") insect_queen_bee_2d();
    else if (insect_type == "spider") insect_spider_2d();
    else insect_queen_bee_2d(); // fallback
}

// --- 3D Modules ---
module insect_inlay_3d() {
    z_start = tile_height - inlay_depth;
    total_h = inlay_depth + emboss_height;
    
    translate([0, 0, z_start])
    linear_extrude(height = total_h, convexity = 10)
        insect_2d();
}

module base_tile_3d() {
    difference() {
        solid_hex_base();
        
        translate([0, 0, tile_height - inlay_depth - 0.01])
        linear_extrude(height = inlay_depth + 1.0, convexity = 10)
            insect_2d();
    }
}

// --- Render Pipeline ---
if (render_mode == "both") {
    color(color_base) base_tile_3d();
    color(color_insect) insect_inlay_3d();
}
else if (render_mode == "base_only") {
    base_tile_3d();
}
else if (render_mode == "insect_only") {
    insect_inlay_3d();
}
