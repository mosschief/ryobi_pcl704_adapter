"""Rebuild ryobi-pcl704-adapter.stl from the Printables v8 model.

Source: https://www.printables.com/model/1639014-ryobi-pcl702-replacement-adapter-to-1-14
(download "Ryobi_vaccum_adapter_ v8.stl").

Changes applied to v8:
  1. Oval plug past the flange shortened by 15 mm.
  2. Oval plug outside grown by FIT mm per side for a snug fit in the PCL704.
  3. 1-1/2" section added next to the flange, stepping down (45 deg) to the
     original 1-1/4" spigot.
  4. Interior rebuilt as a smooth loft from the round bore to the oval bore,
     so it prints without internal supports.

Usage:  python build.py "Ryobi_vaccum_adapter_ v8.stl" [out.stl] [--fit 0.3]
Needs:  pip install numpy trimesh manifold3d shapely networkx
"""
import argparse
import numpy as np
import shapely
import trimesh
import manifold3d as mf

# v8 geometry (mm, v8 coordinates: round spigot at low Z, oval tip at high Z)
OVAL_OUT = (42.4 / 2, 27.7 / 2)   # oval plug outer semi-axes
OVAL_IN = (37.4 / 2, 22.68 / 2)   # oval bore semi-axes
R_BORE = 26.3 / 2                 # round bore radius
SMALL_OD = 31.3                   # 1-1/4" spigot OD

# 1. shorten: remove a slab from the straight part of the oval
CUT_Z, SHORTEN = 207.0, 15.0

# 3. 1-1/2" section
STEP_Z, TOP_Z = 125.0, 160.0
OD_TOP, OD_BOT = 38.4, 37.8       # slight friction taper

# 4. smooth interior
LOFT_Z0, LOFT_Z1 = 160.0, 185.0   # round -> oval bore
FILL_Z0, FILL_Z1 = 158.0, 205.0   # region where the old stepped interior is replaced
SLICE = 0.5


def to_mf(t):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32),
                               tri_verts=np.asarray(t.faces, np.uint32)))


def to_tm(m):
    g = m.to_mesh()
    return trimesh.Trimesh(g.vert_properties[:, :3], g.tri_verts)


def box(z0, z1, w=200):
    return mf.Manifold.cube([w, w, z1 - z0]).translate([-w / 2, -w / 2, z0])


def shorten(m):
    bot = m ^ box(0, CUT_Z + 0.05)
    top = (m ^ box(CUT_Z + SHORTEN, 400)).translate([0, 0, -SHORTEN])
    return bot + top


def grow_oval(m, fit):
    a, b = OVAL_OUT
    ell = mf.Manifold.cylinder(300, 1, 1, 256).scale([a + 0.02, b + 0.02, 1]).translate([0, 0, 178])
    oval = (m ^ ell).scale([(a + fit) / a, (b + fit) / b, 1])
    return m + oval


def big_spigot():
    cham = (OD_BOT - SMALL_OD) / 2
    s = mf.Manifold.cylinder(TOP_Z - STEP_Z, OD_BOT / 2, OD_TOP / 2, 256).translate([0, 0, STEP_Z])
    s += mf.Manifold.cylinder(cham, SMALL_OD / 2, OD_BOT / 2, 256).translate([0, 0, STEP_Z - cham])
    return s - mf.Manifold.cylinder(400, 29.5 / 2, 29.5 / 2, 256)


def solid_fill(t):
    """Stack of slabs following the part's outer outline (holes filled), inset so
    the stair steps stay buried in the wall. The small closing also seals a
    hairline gap in v8 between the tilted flange and the oval wall."""
    parts = []
    for z in np.arange(FILL_Z0, FILL_Z1, SLICE):
        s = t.section(plane_origin=[0, 0, z + SLICE / 2], plane_normal=[0, 0, 1])
        polys = [shapely.Polygon(e[:, :2]).buffer(0) for e in s.discrete]
        u = shapely.unary_union([p for p in polys if p.area > 1]).buffer(0.3).buffer(-1.3)
        for g in getattr(u, 'geoms', [u]):
            if g.is_empty:
                continue
            g = shapely.geometry.polygon.orient(shapely.Polygon(g.exterior), 1)
            cs = mf.CrossSection([np.asarray(g.exterior.coords)[:-1].tolist()])
            parts.append(mf.Manifold.extrude(cs, SLICE + 0.05).translate([0, 0, z]))
    return mf.Manifold.batch_boolean(parts, mf.OpType.Add)


def smooth_bore():
    circ = mf.CrossSection.circle(R_BORE, 256)
    sx, sy = OVAL_IN[0] / R_BORE, OVAL_IN[1] / R_BORE
    v = mf.Manifold.extrude(circ, LOFT_Z0 - FILL_Z0 + 5).translate([0, 0, FILL_Z0 - 5])
    v += mf.Manifold.extrude(circ, LOFT_Z1 - LOFT_Z0, 64, 0, (sx, sy)).translate([0, 0, LOFT_Z0])
    v += mf.Manifold.extrude(circ, FILL_Z1 + 5 - LOFT_Z1).scale([sx, sy, 1]).translate([0, 0, LOFT_Z1])
    return v ^ box(FILL_Z0 - 5, FILL_Z1 + 5)


def build(src, fit):
    m = grow_oval(shorten(to_mf(trimesh.load(src))), fit)
    fill = solid_fill(to_tm(m))
    return to_tm(m + big_spigot() + fill - smooth_bore())


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('out', nargs='?', default='ryobi-pcl704-adapter.stl')
    ap.add_argument('--fit', type=float, default=0.3, help='oval growth per side, mm')
    a = ap.parse_args()
    t = build(a.src, a.fit)
    t.export(a.out)
    print(a.out, 'watertight' if t.is_watertight else 'NOT watertight')
