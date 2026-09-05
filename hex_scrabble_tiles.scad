// ========================================================================
// Parametric Dual-Color Hexagonal Scrabble 3D Printable Tile
// OpenSCAD Customizer Compatible
// ========================================================================

/* [Tile Dimensions] */
// Flat-to-flat diameter in mm (33.02 mm = 1.3 inches)
tile_flat_to_flat = 33.02; // [20.0:0.1:100.0]

// Total tile height/thickness in mm
tile_height = 4.8; // [2.0:0.1:15.0]

// 45-degree top perimeter chamfer size in mm
chamfer = 0.8; // [0.0:0.1:3.0]

// Recessed inlay depth for the glyphs in mm
inlay_depth = 0.8; // [0.2:0.1:3.0]

// Additional raised emboss height above tile surface (0 for flush)
emboss_height = 0.0; // [0.0:0.1:3.0]

/* [Text & Glyphs] */
// Main letter, number, or symbol
char_letter = "A";

// Scrabble score subscript (leave empty for none)
char_score = "1";

// Main character font size
letter_size = 18.0; // [8.0:0.5:30.0]

// Score subscript font size
score_size = 7.5; // [4.0:0.5:15.0]

// Font name and style
font_name = "Trebuchet MS:style=Bold";

/* [Rendering & Multi-Material Mode] */
// Select which parts to render
render_mode = "both"; // [both:Dual Color Assembly, base_only:Base Tile Only, text_only:Text Inlay Only, cutaway:Cross Section View]

// Preview color for base tile
color_base = "Ivory";

// Preview color for text
color_text = "#151515";

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
        // Lower straight portion (z = 0 to z = tile_height - chamfer)
        linear_extrude(height = max(0.01, tile_height - chamfer))
            hex_profile(r_vertex);
            
        // Upper chamfered portion (z = tile_height - chamfer to z = tile_height)
        translate([0, 0, tile_height - 0.01])
            linear_extrude(height = 0.01)
                hex_profile(r_top_vertex);
    }
}

// --- 2D Text & Score Layout ---
module glyphs_2d() {
    // Main letter
    if (len(char_letter) > 0) {
        shift_x = (len(char_score) > 0 && char_score != "0") ? -2.8 : 0.0;
        shift_y = (len(char_score) > 0 && char_score != "0") ? 1.0 : 0.0;
        
        translate([shift_x, shift_y, 0])
        text(
            text = char_letter,
            size = letter_size,
            font = font_name,
            halign = "center",
            valign = "center"
        );
    }
    
    // Subscript score
    if (len(char_score) > 0 && char_score != "0") {
        translate([9.2, -8.5, 0])
        text(
            text = char_score,
            size = score_size,
            font = font_name,
            halign = "center",
            valign = "center"
        );
    }
}

// --- 3D Text Inlay Mesh ---
module text_inlay_3d() {
    z_start = tile_height - inlay_depth;
    total_text_h = inlay_depth + emboss_height;
    
    translate([0, 0, z_start])
    linear_extrude(height = total_text_h, convexity = 10)
        glyphs_2d();
}

// --- 3D Base Tile with Cavity ---
module base_tile_3d() {
    difference() {
        solid_hex_base();
        
        // Subtract glyph cavity from the top
        translate([0, 0, tile_height - inlay_depth - 0.01])
        linear_extrude(height = inlay_depth + 1.0, convexity = 10)
            glyphs_2d();
    }
}

// --- Main Assembly Renderer ---
if (render_mode == "both") {
    color(color_base)
        base_tile_3d();
        
    color(color_text)
        text_inlay_3d();
}
else if (render_mode == "base_only") {
    base_tile_3d();
}
else if (render_mode == "text_only") {
    text_inlay_3d();
}
else if (render_mode == "cutaway") {
    difference() {
        union() {
            color(color_base) base_tile_3d();
            color(color_text) text_inlay_3d();
        }
        // Cut front half
        translate([-50, 0, -5])
            cube([100, 50, 20]);
    }
}
