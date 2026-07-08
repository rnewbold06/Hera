# Hera

**360° video to SfM-ready imagery, in one file.**

Hera is a single-file, pure-stdlib Python GUI that wraps FFmpeg to convert 360° equirectangular video into Structure-from-Motion-ready image sets. It was built for the *Inside Out* digital twin research project at Salisbury University and is developed under RCL Services (Rusty's Creation Lab).

No pip installs. No dependencies beyond Python 3 and FFmpeg. Download `hera.py`, run it, go.

## What it does

- **Cubemap extraction**: converts equirectangular 360° video into cubemap face JPEGs (105° face FOV) and/or raw equirectangular frames at a configurable sampling interval
- **Face-drop presets**: Indoor and Outdoor modes that automatically exclude faces contaminated by the operator or rig (with the documented indoor exception for the top camera's up-face)
- **COLMAP integration**: auto-generates `cameras.txt` with correct pinhole intrinsics (fx = (W/2)/tan(FOV/2)) and sequential-matching pair lists to mitigate false matches in repetitive corridors
- **AprilTag sheet generator**: prints tag36h11 fiducial sheets for control networks and datum bridging
- **Capture planner**: multi-room scene builder with rectangular and circular rooms, drag-and-drop snapping, and doorway junction detection
- **Rig profiles and scenes**: save/load rig configurations and capture scenes as JSON
- **Workflow tips**: built-in reference window documenting capture best practices

## Requirements

- Python 3.10+ (stdlib only; Tkinter ships with standard CPython installers)
- [FFmpeg](https://ffmpeg.org/) on PATH (developed against 6.1.1)
- Optional: [tkinterdnd2](https://pypi.org/project/tkinterdnd2/) for OS-level drag-and-drop. Hera falls back to stdlib file dialogs if it is not installed.

## Quick start

```
python hera.py
```

1. Point Hera at your equirectangular video export (e.g., from Insta360 Studio)
2. Pick a rig profile or configure cameras manually
3. Select Indoor or Outdoor face-drop preset
4. Set your frame interval and output directory
5. Extract, then feed the output folder to COLMAP or RealityScan

## Deferred features

The following are intentionally out of scope for now, with reasons documented in-app: AprilTag family selector, auto-orient YPR, blur detection (requires OpenCV, which breaks the stdlib-only constraint), EXIF/GPS embedding, batch/queue processing, parallel multi-processing, and a rig calibration helper.

## Related projects

- [Argus](ARGUS_REPO_URL): the three-camera Insta360 X4 rig this tool was built to support
- The *Inside Out* research project, Department of Geography and Geosciences, Salisbury University

## Citing

See [CITATION.cff](CITATION.cff). If you use Hera in published work, a citation is appreciated.

## License

MIT. See [LICENSE](LICENSE).
