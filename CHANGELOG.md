# Changelog

All notable changes to Hera are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning is [semantic](https://semver.org/): breaking changes to output
layout, config schema, or scene file format bump the major version.

## [Unreleased]

<!-- Add entries here as you work. Move them into a version block on release. -->

## [2.12.0] - 2026-07-28

<!-- TODO: reconstruct the real history from your commits. The entries below are
     structural placeholders showing the intended level of detail. Delete or
     rewrite them; do not ship them as-is. -->

### Added
- `<TODO>`

### Changed
- `<TODO>`

### Fixed
- `<TODO>`

---

## Writing entries

Keep entries user-facing. "Refactored the filtergraph builder" tells a user
nothing; "Cube faces now honour face FOV above 90 degrees, so you can build
inter-face overlap for the matcher" tells them what changed for them.

Flag anything that invalidates existing files:

- **Config schema changes** — note whether `~/.hera_config.json` needs deleting
- **Scene format changes** — note whether saved KapturPlan scenes still load
- **Output layout changes** — note whether existing folder structures still work
