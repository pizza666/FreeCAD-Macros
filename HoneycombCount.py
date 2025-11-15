import FreeCAD as App
import Part
import math

class Honeycomb:
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "Honeycomb"
        self.obj = obj

        # Parameter
        obj.addProperty("App::PropertyInteger", "hex_x", "Honeycomb",
                        "Number of hexes in x-direction").hex_x = 5
        obj.addProperty("App::PropertyInteger", "hex_y", "Honeycomb",
                        "Number of hexes in y-direction").hex_y = 7
        obj.addProperty("App::PropertyFloat", "side", "Honeycomb",
                        "Hexagon side length").side = 15.6
        obj.addProperty("App::PropertyFloat", "wall", "Honeycomb",
                        "Wall thickness of hex walls").wall = 0.9
        obj.addProperty("App::PropertyFloat", "thickness", "Honeycomb",
                        "Extrusion thickness").thickness = 60.0
        obj.addProperty("App::PropertyFloat", "angle_deg", "Honeycomb",
                        "Extrusion angle in degrees").angle_deg = 10.0
        obj.addProperty("App::PropertyEnumeration", "angle_axis", "Honeycomb",
                        "Axis of extrusion tilt").angle_axis = ["x", "y"]
        obj.angle_axis = "x"
        obj.addProperty("App::PropertyBool", "outer_wall", "Honeycomb",
                        "Add reinforced outer wall").outer_wall = True
        obj.addProperty("App::PropertyBool", "fuse_result", "Honeycomb",
                        "Fuse all hexes and outer wall into one solid").fuse_result = False

    def execute(self, fp):
        hex_x = fp.hex_x
        hex_y = fp.hex_y
        side = fp.side
        wall = fp.wall
        thickness = fp.thickness
        angle_deg = fp.angle_deg
        angle_axis = fp.angle_axis
        outer_wall = fp.outer_wall
        fuse_result = fp.fuse_result

        # Hexagon-Abstände
        w = math.sqrt(3) * side
        h = 2 * side
        row_step = 0.75 * h
        col_step = w

        # --- Hexagon Punkte ---
        def hex_points(cx, cy, r):
            return [App.Vector(
                cx + r * math.cos(math.radians(60*i + 30)),
                cy + r * math.sin(math.radians(60*i + 30)),
                0
            ) for i in range(6)]

        # --- Hex-Ring mit Löchern ---
        def make_hex_ring(cx, cy, r, wall_thickness):
            outer_pts = hex_points(cx, cy, r)
            inner_pts = hex_points(cx, cy, max(r - wall_thickness, 0))

            outer_wire = Part.makePolygon(outer_pts + [outer_pts[0]])
            inner_wire = Part.makePolygon(inner_pts + [inner_pts[0]])

            outer_face = Part.Face(outer_wire)
            inner_face = Part.Face(inner_wire)

            return outer_face.cut(inner_face)

        # --- 1) Innere Waben ---
        rings = []
        for row in range(hex_y):
            for col in range(hex_x):
                xoff = (w / 2) if (row % 2) else 0
                cx = col * col_step + xoff
                cy = row * row_step
                rings.append(make_hex_ring(cx, cy, side, wall/2))  # halbe Wandstärke

        # --- 2) Außenwand ---
        outer_rings = []
        if outer_wall:
            for row in range(hex_y):
                for col in range(hex_x):
                    is_border = row == 0 or row == hex_y-1 or col == 0 or col == hex_x-1
                    if not is_border:
                        continue
                    xoff = (w / 2) if (row % 2) else 0
                    cx = col * col_step + xoff
                    cy = row * row_step
                    # halbe Wandstärke außen → Gesamtwand = wall
                    outer_rings.append(make_hex_ring(cx, cy, side + wall/2, wall/2))

        # --- 3) Alle Faces zusammenführen ---
        all_faces = rings + outer_rings

        if fuse_result:
            # Fuse sicherer mit kleinen Schritten
            try:
                fused = all_faces[0]
                for f in all_faces[1:]:
                    fused = fused.fuse(f)
                compound_2D = fused
            except Exception as e:
                App.Console.PrintError("Fusion fehlgeschlagen: {}\n".format(e))
                compound_2D = Part.makeCompound(all_faces)
        else:
            compound_2D = Part.makeCompound(all_faces)

        # --- 4) Extrusionsvektor ---
        angle_rad = math.radians(angle_deg)
        if angle_axis.lower() == 'x':
            extrude_vec = App.Vector(thickness * math.sin(angle_rad), 0, thickness * math.cos(angle_rad))
        elif angle_axis.lower() == 'y':
            extrude_vec = App.Vector(0, thickness * math.sin(angle_rad), thickness * math.cos(angle_rad))
        else:
            extrude_vec = App.Vector(0, 0, thickness)

        # --- 5) Extrusion ---
        fp.Shape = compound_2D.extrude(extrude_vec)


# --- Erzeugung des Objekts ---
def makeHoneycomb():
    doc = App.ActiveDocument
    obj = doc.addObject("Part::FeaturePython", "Honeycomb")
    Honeycomb(obj)
    obj.ViewObject.Proxy = 0
    doc.recompute()
    return obj


if __name__ == "__main__":
    makeHoneycomb()
