# Changelog

All notable changes to toolroom are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project follows
[SemVer](https://semver.org/) — pre-1.0, minor versions may include
breaking changes.

## [Unreleased]

## [0.1.1] — 2026-08-05

### Fixed

- `.opts(env=…)` standalone now means what it means hosted: the child's
  **whole** environment, never a merge over the parent's. The divergence
  was a portability trap between the two lanes, caught by a consumer's
  sweep.
- Host detection keys on **orchestration, not presence**: a call routes
  through footman only when a footman context is live (a task body, a
  `parallel()` worker, a `recording()` block). A bare call in a process
  that merely imported footman — a pytest run auto-loading footman's
  plugin, say — now takes the standalone lane deterministically, so which
  exception a failure raises never depends on what some other module
  imported. The same sweep caught this one.

## [0.1.0] — 2026-08-05

### Added

- The bridge, extracted from footman (`footman.tools` → `toolroom`) and
  reworked to stand alone: typed handles for command-line tools with
  mechanical keyword-to-flag translation, subcommand chaining,
  `.flags()` / `.opts()` / `.at()` / `.argv`, the `off` sentinel, and
  `installed_version()`.
- The seam (`toolroom._host`): host detection plus a plain subprocess
  executor. Standalone, calls answer in toolroom's own `Result` and
  failures raise `ToolError` unless `nofail`; with footman present in
  the process, the same calls route through footman's `run()` and
  inherit capture, replay-on-failure, dry-run, `recording()`, and
  `--json` receipts. Neither package depends on the other.
- The typed surface: a hand stub and generated per-tool stubs anchored
  on `toolroom`, with `Argv`, `Result`, and `ToolError` declared
  locally so type-checking toolroom never requires footman installed.

### Changed

- **djlint 1.44.0** adds `--allow-empty-input`.

## [0.0.1] — 2026-08-05

### Added

- Name reservation on PyPI: an empty typed module and the
  trusted-publishing release workflow. Nothing importable of substance.

[Unreleased]: https://github.com/willemkokke/toolroom/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/willemkokke/toolroom/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/willemkokke/toolroom/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/willemkokke/toolroom/releases/tag/v0.0.1
