# Ryobi PCL704 vacuum adapter (1-1/4" and 1-1/2")

Adapter that plugs into the Ryobi PCL704 hand vacuum and accepts standard
1-1/4" and 1-1/2" vacuum attachments.

Remix of [Ryobi PCL702 replacement adapter to 1-1/4"](https://www.printables.com/model/1639014-ryobi-pcl702-replacement-adapter-to-1-14) (v8).

## Changes from the original

- Oval plug past the flange is 15 mm shorter.
- Oval plug is 0.3 mm larger per side (43.0 x 28.3 mm) for a snug fit in the PCL704.
- Added a 1-1/2" section (37.8-38.4 mm OD, slight taper) next to the flange that
  steps down at 45 deg to the original 1-1/4" section (31.3 mm OD).
- Interior blends smoothly from the round bore to the oval bore, so no internal
  supports are needed.

## Printing

Print with the round end down. The only overhang is the tilted flange.

## Rebuilding

`build.py` regenerates the STL from the original v8 file (not included here):

```
pip install numpy trimesh manifold3d shapely networkx
python build.py "Ryobi_vaccum_adapter_ v8.stl" --fit 0.3
```

`--fit` sets how much the oval plug is grown per side (mm); 0.2 is looser, 0.4 tighter.
