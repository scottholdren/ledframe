// KenLED v2 baffle grid — one light-tight cell per LED, printed as tiles.
// Prints standing up, no supports (the strip notches are short bridges).
// Black PETG. Tiles butt edge-to-edge: outer walls are half thickness so
// two neighbours make one full wall and pitch stays exact across seams.
//
//   openscad -D cols=2 -D rows=2 -o baffle-2x2.stl baffle.scad     (optical test box)
//   openscad -D cols=6 -D rows=6 -o baffle-6x6.stl baffle.scad     (production tile)
//   openscad -D cols=6 -D rows=3 -o baffle-6x3.stl baffle.scad     (27 = 6+6+6+6+3)

// ---- grid (mm) ----
pitch  = 1000 / 30;   // 33.333 — WS2812B-ECO 30 LED/m
cols   = 2;           // cells across (strip direction)
rows   = 2;           // cells down
depth  = 20;          // LED-to-diffuser distance; >= pitch/2 for even cells

// ---- walls ----
wall   = 1.2;         // 3 perimeters @ 0.4 nozzle
// ---- LED strip channel (strips run along X through each row's centre) ----
strip_w = 10 + 1.0;   // 10 mm PCB + slip
strip_h = 2.6;        // PCB + LED package + adhesive
// ---- mounting tabs (optional): small feet at the outer corners, M3 / VHB ----
tabs      = true;
tab       = 8;        // tab square
tab_t     = 1.2;
tab_hole  = 3.2;

$fn = 32;
eps = 0.01;

W = cols * pitch;
H = rows * pitch;

module tile() {
  difference() {
    union() {
      // walls along X (between rows) — at every row boundary incl. tile edges
      for (r = [0 : rows])
        translate([0, r * pitch - wall / 2, 0]) cube([W, wall, depth]);
      // walls along Y (between columns) — bridge over the strip
      for (c = [0 : cols])
        translate([c * pitch - wall / 2, 0, 0]) cube([wall, H, depth]);
    }
    // trim the outer half-walls so the tile footprint is exactly W x H
    translate([-pitch, -pitch, -1]) cube([pitch, H + 2 * pitch, depth + 2]);
    translate([W,      -pitch, -1]) cube([pitch, H + 2 * pitch, depth + 2]);
    translate([-pitch, -pitch, -1]) cube([W + 2 * pitch, pitch, depth + 2]);
    translate([-pitch, H,      -1]) cube([W + 2 * pitch, pitch, depth + 2]);
    // strip notches through the Y-walls at each row centre
    for (r = [0 : rows - 1])
      translate([-1, r * pitch + pitch / 2 - strip_w / 2, -1])
        cube([W + 2, strip_w, strip_h + 1]);
  }
  if (tabs)
    for (x = [0, W - tab], y = [0, H - tab])
      difference() {
        translate([x, y, 0]) cube([tab, tab, tab_t]);
        translate([x + tab / 2, y + tab / 2, -1]) cylinder(h = tab_t + 2, d = tab_hole);
      }
}

tile();

echo(str("tile ", cols, "x", rows, " = ", W, " x ", H, " mm, depth ", depth,
         ", cell clear ", pitch - wall, " mm, notch ", strip_w, "x", strip_h));
