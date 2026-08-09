# Changelog

All notable changes to toolroom are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project follows
[SemVer](https://semver.org/) — pre-1.0, minor versions may include
breaking changes.

## [Unreleased]

### Added

- **claude** joins the curated tools — Claude Code, read from the
  `@anthropic-ai/claude-code` package on the node tier. The headless
  surface is the root call, so `tools.claude("explain this", print=True,
  output_format="json", model="sonnet")` types and completes; the stubbed
  verbs are the ones a task reaches for around it (`mcp.*`, `plugin.*`,
  `auth.*`, `agents`, `doctor`, `update`).
- **A Colour page**, listing how each curated tool is talked into (and
  out of) colour over a pipe. It renders from the checked-in colour data
  on every docs build, so it needs no tool on PATH and cannot drift from
  what ships — the rule the per-tool pages already follow. The table came
  over from footman, where it was left orphaned by the split: its data
  lives here, so its page does too.
- The docs resolve **footman's symbol inventory**, so a mention of
  `run()` or `Result` links straight into footman's API reference (and
  footman's site resolves toolroom's, the other way).

### Changed

- `fm tools.color` reads only what was provisioned. A verdict is a claim
  about a release, so it has to come from a release someone fetched: with
  a `--prefix` a tool the prefix does not carry is skipped rather than
  falling through to the host's copy, and without one the probe still
  prints its table but writes nothing. The write also *folds* into the
  checked-in data instead of replacing it — git and the other tools read
  from their manuals have no binary in any prefix, and a run that wrote
  only what it saw would have dropped git's `-c color.ui=always` and
  taken the bridge's colour forcing with it.

### Fixed

- An option a tool spells two ways now takes its keyword from the
  spelling Python is written in. Claude Code prints `--allowedTools,
  --allowed-tools`, and the first one won, so the stub suggested
  `allowedTools=`. Sameness folds case and dashes away before choosing,
  which is what keeps a *neighbour* from being mistaken for a dialect:
  markdownlint-cli2's `--configPointer, --config` are two different
  options its column alignment runs into one block, and git prints
  `--column[=<options>], --no-column` the same way.
- The stub generator no longer writes a line its own gate refuses. A
  summary with no `Args:` block under it is folded onto one line by the
  formatter, closing quotes and all, and the wrap left room for only the
  opening ones — so a summary landing in a two-character band came out at
  89. An alone summary is now wrapped for both.
- `fm tools.color --write` writes `src/toolroom/_colordata.py` again. It
  had been writing `src/_colordata.py` since the split — the module moved
  into the package and the path did not follow — so a re-probe wrote a
  file nothing imports and left the real data untouched.

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
