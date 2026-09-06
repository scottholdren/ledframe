// KenLED v2 baffle grid — one light-tight cell per LED, printed as tiles.
// Black PETG, prints standing up, no supports.
//
// L-TILES: every wall is full thickness. A tile carries the walls on its
// x=0 and y=0 edges plus all interior walls, and is OPEN on its far edges;
// the neighbouring tile's edge walls close those cells. No half-walls, no
// seams inside a wall, pitch stays exact across the panel. The panel's two
// far edges are closed by the frame's inner rail (or set close_x/close_y).
//
//   openscad -D cols=2 -D rows=2 -D close_x=true -D close_y=true -o baffle-2x2-closed.stl baffle.scad
//   openscad -D cols=5 -D rows=5 -o baffle-5x5.stl baffle.scad

// ---- grid (mm) ----
pitch  = 1000 / 30;   // 33.333 — WS2812B-ECO 30 LED/m
cols   = 2;           // cells across (strip direction, X)
rows   = 2;           // cells down (Y)
depth  = 20;          // LED-to-diffuser distance; >= pitch/2 for even cells

// ---- walls ----
wall   = 1.2;         // 3 perimeters @ 0.4 nozzle (or 2 @ 0.6)
close_x = false;      // add the far X wall (last tile column, if the frame doesn't close it)
close_y = false;      // add the far Y wall (last tile row)

// ---- LED strip channel (strips run along X through each row's centre) ----
strip_w = 10 + 1.0;   // 10 mm PCB + slip
strip_h = 2.6;        // PCB + LED package + adhesive

// ---- mounting tabs: small feet in the cell corners next to the tile's own walls ----
tabs      = true;
tab       = 8;
tab_t     = 1.2;
tab_hole  = 3.2;

$fn = 32;

W = cols * pitch;
H = rows * pitch;
nx = cols + (close_x ? 1 : 0);   // number of Y-direction walls
ny = rows + (close_y ? 1 : 0);   // number of X-direction walls

module tile() {
  difference() {
    union() {
      // walls along X (row boundaries): at y = 0, pitch, ... ; far one only if close_y
      for (r = [0 : ny - 1])
        translate([0, r * pitch, 0]) cube([W + (close_x ? wall : 0), wall, depth]);
      // walls along Y (column boundaries): at x = 0, pitch, ... ; far one only if close_x
      for (c = [0 : nx - 1])
        translate([c * pitch, 0, 0]) cube([wall, H + (close_y ? wall : 0), depth]);
    }
    // strip notches through every Y-wall at each row centre (flat bridge, full-width wall)
    for (r = [0 : rows - 1])
      translate([-1, r * pitch + wall + (pitch - wall) / 2 - strip_w / 2, -1])
        cube([W + wall + 2, strip_w, strip_h + 1]);
  }
  if (tabs)
    for (c = [0 : cols - 1], r = [0 : rows - 1])
      if ((c + r) % 2 == 0)   // every other cell is plenty
        difference() {
          translate([c * pitch + wall, r * pitch + wall, 0]) cube([tab, tab, tab_t]);
          translate([c * pitch + wall + tab / 2, r * pitch + wall + tab / 2, -1])
            cylinder(h = tab_t + 2, d = tab_hole);
        }
}

tile();

echo(str("L-tile ", cols, "x", rows, " footprint ", W, " x ", H,
         " (+wall on closed edges), depth ", depth, ", wall ", wall,
         ", cell clear ", pitch - wall, ", notch ", strip_w, "x", strip_h));
