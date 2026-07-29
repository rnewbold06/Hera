# Hera™

**Capture planning and SfM preprocessing for 360° reality capture, in one file.**

Hera plans the walk before you shoot, generates the fiducial control points you place, and turns the resulting 360° footage into reconstruction-ready imagery. It is a single Python file with no dependencies beyond the standard library and FFmpeg.

Built as the software companion to the [Argus](https://github.com/rnewbold06/Argus) multi-camera rig, and developed for the *Inside Out* digital twin research project at Salisbury University. An RCL Services product.

```
python3 hera.py
```

No pip install. No virtualenv. Download `hera.py`, make sure FFmpeg is on PATH, and run it.

---

## Contents

- [Why this exists](#why-this-exists)
- [Tools](#tools)
  - [KapturPlan™ — capture planner](#kapturplan--capture-planner)
  - [AprilTag generator](#apriltag-generator)
  - [Extraction and preprocessing](#extraction-and-preprocessing)
- [How tag spacing is derived](#how-tag-spacing-is-derived)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [End-to-end workflow](#end-to-end-workflow)
- [Output layout](#output-layout)
- [Configuration](#configuration)
- [Self-test](#self-test)
- [Non-goals](#non-goals)
- [Related projects](#related-projects)
- [Citing](#citing)
- [License](#license)

---

## Why this exists

Indoor Structure-from-Motion with consumer 360° cameras fails in predictable ways: the operator appears in every frame, corridors are visually repetitive enough to produce false matches, reconstructions drift without scale constraints, and capture is usually planned by walking around and hoping.

Hera addresses each of those before and during preprocessing rather than after reconstruction has already gone wrong.

<!-- TODO: add a screenshot of the main window here -->
<!-- ![Hera main window](docs/img/hera-main.png) -->

---

## Tools

### KapturPlan™ — capture planner

An interactive 2D scene editor that produces a printable field plan.

**Scene building.** Drag rectangular and circular rooms from a palette. Place obstacles (islands, tables, fixtures). Walls snap live as you drag; handles resize; sizes can be typed directly. Define connections between rooms as passages, openings with a settable gap width, or bridge clusters. Undo/redo, zoom, pan, and scene save/load as JSON. Metres or feet.

**Three modes.**

| Mode | Plans |
|---|---|
| Indoor rooms | Room-by-room path with doorway junction handling |
| Outdoor open area | Coverage pattern over an open footprint |
| Building perimeter | A loop outside the building envelope |

**Computed output.**

- A walking path routed around obstacles, room by room, with junctions tying components together
- Camera heights for all three rig positions, derived from operator height and rig offsets, clamped against ceiling height
- Walking speed, from station spacing and your planned sampling rate
- Wall, floor, and doorway tag positions at a spacing derived from detection physics (see below)
- Ground control point placement
- Suggested scale-constraint pairs: two tag-to-tag distances to measure by hand and enter as known constraints, chosen to lock scale and, where possible, tie separate components together
- Estimated capture time
- Warnings when the geometry is unworkable — tags too small for the room, bottom camera above the middle, top camera close enough to the ceiling that it will mostly see ceiling

**Export.** A vector PDF field plan with the map, a metadata block, the constraint table, capture tips, and literature references. Written by a PDF generator implemented in the standard library, so there is no ReportLab dependency.

<!-- TODO: add a screenshot of KapturPlan with a computed multi-room plan -->
<!-- TODO: add a sample exported capture plan PDF under docs/ and link it here -->

---

### AprilTag generator

Produces printable fiducial sheets for indoor control networks.

- Full **tag36h11** family, 587 tags, embedded in the script
- Vector **PDF** or **SVG** output, so tags stay crisp at any print size
- Physical tag size specified in millimetres; what you type is what you measure
- Paper sizes: Letter, A4, Legal, A3, A5
- Templated captions (`Hera • tag {id}` by default), optional cut marks, optional branding image
- ID selection by range or list (`0-15`, `0,4,9,20-24`)
- Live preview before export

Print at 100% scale with no page fitting. Measure a printed tag before deploying a whole set; a printer that silently scales to 96% will quietly corrupt every scale constraint downstream.

---

### Extraction and preprocessing

**Cubemap conversion.** Equirectangular 360° video to cubemap faces via FFmpeg's `v360` filter, with:

- Independent yaw, pitch, and roll per camera
- Selectable faces, so you can drop faces contaminated by the operator or rig
- Configurable face FOV above 90°, to build deliberate inter-face overlap for the matcher
- Six interpolation kernels: nearest, linear, cubic, lanczos, spline16, gaussian
- Configurable face size, or native

**Frame extraction.** Equirectangular frames, cube faces, or both, at any sampling rate. Independent format and quality settings for each (JPEG quality, PNG compression level).

**Blur rejection.** A per-frame gate using FFmpeg's `blurdetect` filter (FFmpeg 5.1+), which estimates blur from edge widths using the Marziliano method and writes it as frame metadata. Frames above your threshold are dropped before they reach the matcher. Lower threshold means stricter.

**COLMAP intrinsics.** Every cube face is a distortion-free pinhole rendering with a square, known FOV, so the intrinsics are exact rather than estimated:

$$f_x = f_y = \frac{W/2}{\tan(\text{FOV}/2)}, \qquad c_x = c_y = W/2$$

Hera writes a ready-to-import `cameras.txt` with the correct `PINHOLE` parameters and the matching `feature_extractor` invocation in the header comments. Fixing calibration instead of solving for it removes a large family of failure modes in feature-poor interiors.

**Operator and rig masking.** The feature that matters most for handheld 360° work.

You paint a mask once, in equirectangular space, marking yourself and the rig. Hera then projects that single mask through the *identical* cubemap transform used for the imagery, producing a correctly oriented mask for every face of every frame. Because the operator is static relative to the camera, one painted mask covers the entire capture.

Supports mask dilation in pixels, both polarities (black-ignore or white-ignore), sidecar naming patterns to match your SfM tool's expectations, and optional alpha baking directly into the images.

**Rig support.** Three camera slots (top, middle, low) matching Argus, each with independent orientation and face selection. A live 2D rig schematic shows the configuration, and a multi-camera test render extracts the first frame from every camera so you can verify orientation before committing to a full pass.

---

## How tag spacing is derived

Tag spacing is not a guess. `tag36h11` is an 8×8 module pattern (6×6 data plus a one-module border). Reliable detection at moderate viewing angles needs roughly 5 pixels per module, or about 40 pixels across the black square.

For an equirectangular frame of width $W_{eq}$ pixels covering 360°, the angular resolution is $W_{eq}/2\pi$ pixels per radian. A tag of physical edge length $s$ at distance $d$ subtends approximately $s/d$ radians, so it occupies $s W_{eq} / (2 \pi d)$ pixels. Setting that equal to the 40 pixel floor and solving for distance:

$$d_{max} = \frac{s \cdot W_{eq}}{2\pi \cdot p_{min}}, \qquad p_{min} = 40$$

KapturPlan places tags at $0.6 \, d_{max}$, clamped to a practical 0.4–8.0 m, and warns you when $d_{max}$ falls below 1.5 m, which is the point where a tag size is effectively unusable for the room you have drawn.

A worked example: a 100 mm tag on 7680 px equirectangular footage gives $d_{max} \approx 3.1$ m, so tags land about every 1.8 m. Halve the tag size and you halve the range; the planner will tell you before you print 40 sheets at the wrong size.

The 5-px-per-module floor follows the detection-rate characterisations in:

- Olson, E. (2011). AprilTag: A robust and flexible visual fiducial system. *ICRA*.
- Wang, J. & Olson, E. (2016). AprilTag 2: Efficient and robust fiducial detection. *IROS*.
- Kalaitzakis, M. et al. (2021). Fiducial markers for pose estimation: overview, applications and experimental comparison. *Journal of Intelligent & Robotic Systems*.

These are conservative starting points for planning, not guarantees. Lighting, motion blur, print quality, and viewing angle all move the real threshold.

---

## Requirements

| | |
|---|---|
| **Python** | 3.8 or newer, with Tk 8.6. Standard library only at runtime. Tkinter ships with the standard CPython installers on Windows and macOS; on Debian/Ubuntu install `python3-tk`. |
| **FFmpeg** | On PATH. Developed against 6.1.1. Blur rejection needs 5.1+ for the `blurdetect` filter. |
| **Optional** | [`tkinterdnd2`](https://pypi.org/project/tkinterdnd2/) enables OS-level drag-and-drop of video files. Hera falls back to standard file dialogs without it. |

Hera will tell you if FFmpeg is missing or too old, and links to the download page.

---

## Quick start

```bash
git clone https://github.com/rnewbold06/Hera.git
cd Hera
python3 hera.py
```

Or download `hera.py` on its own. It is self-contained; logos and the full AprilTag pattern set are embedded as base64.

---

## End-to-end workflow

**1. Plan.** Open KapturPlan. Draw the space, set your ceiling height, your own height, rig offsets, tag size, and the resolution you will shoot at. Compute the plan, read the warnings, adjust, and export the PDF.

**2. Print tags.** Open the AprilTag generator, request the ID range your plan calls for at the size your plan specified, and export to PDF. Print at 100% scale. Verify with a ruler.

**3. Deploy and capture.** Place tags per the plan. Walk the planned path at the planned speed. Measure the two suggested constraint distances and write them on the printed plan.

**4. Export footage.** Stitch to equirectangular in Insta360 Studio or your tool of choice. Hera works on equirectangular video, not raw `.insv`.

**5. Paint a mask.** Grab one equirectangular frame, paint over yourself and the rig, and save it alongside the video using the configured naming pattern.

**6. Extract.** Load the videos into the three camera slots, set orientation per camera, drop contaminated faces, set your sampling rate and blur threshold, enable mask projection and COLMAP export, and run.

**7. Reconstruct.** Point COLMAP or RealityScan at the output folder. Import `cameras.txt`, use the projected masks, and enter your measured distances as scale constraints.

---

## Output layout

```
output/
  w1_equirect/            # optional equirectangular frames
  w1_topF/                # per-camera, per-face cube frames
  w1_topL/
  w1_midF/
  w1_lowF/
  ...
  masks/                  # projected per-face masks, if enabled
  cameras.txt             # COLMAP intrinsics, if enabled
```

Prefixes are configurable. The default `w1`, `w2` scheme is per-walk.

---

## Configuration

Settings persist to `~/.hera_config.json`, including per-camera orientation, face selection, and mask paths. Rig configurations and KapturPlan scenes save and load as separate JSON files so you can keep a library per building.

**Reset to Defaults** in the toolbar clears everything back to a known state.

---

## Self-test

```bash
python3 hera.py --selftest
```

Runs headless validation of the filtergraph construction, projection maths, tag decoding, PDF generation, and planner geometry. Useful in CI and after any FFmpeg upgrade.

---

## Non-goals

Deliberately out of scope, with reasons documented in the app:

- **Stitching.** Use the manufacturer's tool. Hera starts from equirectangular video.
- **Reconstruction.** Hera prepares data for COLMAP, RealityScan, and Metashape rather than replacing them.
- **AprilTag family selector.** tag36h11 only, to keep the embedded pattern set small.
- **Auto-orient YPR.** Orientation is set explicitly and verified with the test render.
- **EXIF/GPS embedding, batch queueing, multiprocessing, rig calibration helper.** Not yet implemented.

Anything requiring NumPy, OpenCV, or Pillow is out of scope by design. The single-file, zero-install property is the point; keeping it costs some features and that trade is intentional.

---

## Related projects

- **[Argus](https://github.com/rnewbold06/Argus)** — the multi-height Insta360 X4 rig Hera was built to support
- *Inside Out* — digital twin research, Department of Geography and Geosciences, Salisbury University
- [RCL Services](https://sites.google.com/view/rclservices/home) — Rusty's Creation Lab

---

## Citing

See [CITATION.cff](CITATION.cff). If Hera contributes to published work, a citation is appreciated.

---

## Contributing

Issues and pull requests are welcome. Two constraints on contributions:

1. **No new runtime dependencies.** Standard library only.
2. **`--selftest` must pass.** Add coverage for anything new.

---

## License

MIT. See [LICENSE](LICENSE).

Hera™ and KapturPlan™ are products of Rusty's Creation Lab (RCL) Services, developed independently and not affiliated with or endorsed by any institution.

© 2026 Rustin C. Newbold
