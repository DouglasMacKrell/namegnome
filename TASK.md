# namegnome v2 — TASK.md

> **Prompt to AI:** "Update TASK.md to mark XYZ as done and add ABC as a new task."

---

## 1 · Sprint 0 (MVP 0.1 "Dry‑Run Scanner" — Fully Expanded)

Each ticket is self‑contained so Cursor can tackle them sequentially.

### 0.1 Repo Bootstrap, Pre‑commit & CI

* **Goal:** Scaffold project with enforced lint and test gates.
* **Steps:**

  1. Initialise Poetry project (`poetry init --name namegnome`).
  2. Add dev dependencies in `pyproject.toml` → `[tool.poetry.group.dev.dependencies]`: `ruff`, `mypy`, `pytest`, `pytest-cov`, `pre‑commit`.
  3. Create `.pre‑commit-config.yaml` with hooks in this order: `ruff‑format`, `ruff`, `mypy --strict`, `pytest -q`.
  4. Commit and push; set up GitHub Actions workflow running pre‑commit and `pytest --cov=namegnome --cov-fail-under=80` on OS matrix `ubuntu‑latest`, `macos‑latest`, `windows‑latest`.
* **Done when:** Local `pre‑commit run --all-files` is clean and CI workflow passes.

### 0.2 Package Skeleton

* **Goal:** Create importable project layout.
* **Steps:**

  1. Make directories: `namegnome/`, `namegnome/core/`, `namegnome/models/`, `namegnome/rules/`.
  2. Add empty `__init__.py` files; expose `__version__` in top‑level init.
  3. Add Typer `app` object in `namegnome/cli.py` with a no‑op root command.
* **Done when:** `python -m namegnome --help` prints CLI help.

### 0.3 Domain Models

* **Goal:** Define core data classes with pydantic v2.
* **Steps:**

  1. Implement `MediaFile`, `RenamePlanItem`, `RenamePlan`, and `ScanResult`.
  2. Include enums for `MediaType` and `PlanStatus`.
  3. Write param tests asserting JSON (de)serialisation and validation errors.
* **Done when:** All model tests pass and coverage ≥ 90 % for `models` module.

### 0.4 Rule Engine Prototype

* **Goal:** Produce first target‑path generator.
* **Steps:**

  1. Create `rules/base.py` with abstract `RuleSet` class and `target_path(media_file)`.
  2. Implement `PlexRuleSet` using naming guide; regex for movies and episodic TV.
  3. Add fixture files and tests that expected paths match.
* **Done when:** PlexRuleSet passes all naming tests.

### 0.5 Metadata Provider Stubs

* **Goal:** Framework for future API clients without network I/O.
* **Steps:**

  1. Create `metadata/clients/base.py` with async abstract methods.
  2. Implement `StubTMDBClient` & `StubTVDBClient` loading static JSON under `tests/fixtures/stubs/`.
  3. Register factory in `metadata/__init__.py`.
  4. Unit tests validate mapping to `MediaMetadata` dataclass.
* **Done when:** Stubs return deterministic metadata in tests.

### 0.6 Directory Scanner

* **Goal:** Convert file system into `ScanResult`.
* **Steps:**

  1. Walk root with `Path.rglob()` gathering media extensions.
  2. Instantiate `MediaFile` with guessed `MediaType`.
  3. Collate into `ScanResult` (list + summary stats).
  4. Tests cover mixed media, hidden files, and non‑UTF8 names.
* **Done when:** Scanner classifies ≥ 95 % fixtures correctly.

### 0.7 Rename Planner

* **Goal:** Produce conflict‑aware rename plan.
* **Steps:**

  1. Iterate `ScanResult` → `RuleSet` → proposed target.
  2. Detect collisions and mark status `CONFLICT`.
  3. Serialize `RenamePlan` to JSON file.
  4. Tests compare plan snapshot against expected JSON.
* **Done when:** Plan JSON passes snapshot tests.

### 0.8 Rich Diff Renderer & CLI UX

* **Goal:** User‑friendly diff view and status feedback.
* **Steps:**

  1. Build `render_diff()` using `rich.table.Table` with colour key.
  2. Add status spinners for expensive steps.
  3. Implement `--json` flag to emit raw JSON.
  4. Enable pretty traceback globally.
  5. Tests capture console output; ensure ANSI removed when `--no-color`.
* **Done when:** CLI renders coloured table and passes no‑color test.

### 0.9 CLI `scan` Command

* **Goal:** Wire everything together.
* **Steps:**

  1. Add Typer command `scan` with options: `root`, `platform`, `media-type`, `verify`, `json`, `llm-model`.
  2. Invoke scanner → planner → renderer.
  3. Save plan file under `.namegnome/plans/`.
  4. Exit codes: 0 success, 2 manual needed, 1 error.
* **Done when:** Manual smoke test produces plan file and diff output.

### 0.10 Rollback Plan Store

* **Goal:** Persist artifacts for future undo.
* **Steps:**

  1. Ensure `.namegnome/plans/` exists; create if missing.
  2. Move plan JSON; symlink `.namegnome/latest.json` to newest.
  3. When `--verify` flag used, store per‑file SHA‑256 checksums.
  4. Write `run.yaml` metadata (args, git hash).
* **Done when:** Plan and metadata files exist and schema validated in test.

### 0.11 Test Harness Expansion

* **Goal:** Reach baseline coverage.
* **Steps:**

  1. Add edge‑case tests: unicode, long filenames, weird seasons.
  2. Generate `coverage.xml`; CI enforces ≥ 80 %.
* **Done when:** Coverage threshold met in CI.

### 0.12 Docs Update

* **Goal:** Onboard contributors and users.
* **Steps:**

  1. Expand `README` with install, usage, roadmap.
  2. Add architecture diagram under `docs/`.
  3. Create `CONTRIBUTING.md` describing commit style `NGN-###`.
  4. Add CI and coverage badges.
  5. Perform a full documentation and comment sweep for all modules, ensuring Google-style docstrings, inline reasoning comments, and E501 compliance.
* **Done when:** Docs pass markdown-lint and render on GitHub.

---

## 2 · Sprint 1 (MVP 0.2 "Apply & Undo" — Fully Expanded)

The goal of this sprint is to turn the dry‑run plan into real, safe filesystem operations, with full rollback and user feedback.

### 1.1 Filesystem Abstraction Layer

* **Goal:** Provide a robust, cross‑platform, atomic file‑move helper that underpins apply/undo operations.
* **Steps:**

  1. **Module & signature** – Create `fs/operations.py` exposing

     ```python
     def atomic_move(src: Path, dst: Path, *, dry_run: bool = False, overwrite: bool = False) -> None:
         """Atomically move *src* to *dst*.

         Raises:
             FileExistsError: If dst exists and *overwrite* is False.
             FileNotFoundError: If src is missing.
             OSError: For non‑recoverable FS errors.
         """
     ```
  2. **POSIX implementation** – Use `os.rename` inside a try‑except; on `OSError` with `EXDEV`, perform streamed copy (`shutil.copy2`) + `os.unlink` to support cross‑device moves (e.g., NAS mounts).
  3. **Windows specifics** – Use `os.replace` which is atomic on NTFS; prepend `"\\?\"` to both paths when `len(path) > 259` to bypass MAX_PATH. Handle ACL inheritance by copying DACLs via `ctypes` if `overwrite`.
  4. **Dry‑run mode** – When `dry_run=True`, log intended move via `console.log` and skip filesystem ops.
  5. **Overwrite handling** – If `overwrite` and destination exists, hash‑compare source and dest; skip move when hashes identical else remove dest then move.
  6. **Unit tests** – Under `tests/fs/test_operations.py`:

     * `test_atomic_move_basic(tmp_path)` – simple rename.
     * `test_cross_device(tmp_path_factory)` – simulate by mounting tmpfs (Linux) or mocking `os.rename` to raise `EXDEV`.
     * `test_long_paths_windows(mocker)` – mock Windows platform; verify prefix added.
     * `test_dry_run_no_op(tmp_path, caplog)` – ensure no FS change.
     * `test_overwrite_with_identical_hash(tmp_path)` – dst identical file skipped.
  7. **Documentation** – Docstring examples and update `README` advanced section.
* **Done when:** All unit tests pass on Ubuntu, macOS, Windows runners; function raises appropriate errors and is used by Apply/Undo engines without modifications.

### 1.2 SHA‑256 Hash Utility

* **Goal:** Guarantee file integrity and enable duplicate‑skip logic.
* **Steps:**

  1. Implement `utils/hash.py` with `sha256sum(path: Path, chunk_size=8_388_608) -> str`.
  2. Add optional `--verify` flag to `scan` to pre‑compute hashes and embed them in each `RenamePlanItem`.
  3. During `apply`, recompute destination hash; compare to stored source hash.
  4. If mismatch, set item status `FAILED`, append to error list, trigger automatic rollback.
  5. Add `--skip-identical` flag: if destination exists and hash matches, mark item `SKIPPED` and continue.
  6. Unit tests: good copy, corrupted copy, identical dest.
* **Done when:** All hash scenarios covered and CI green.

### 1.3 Apply Engine

* **Goal:** Execute a `RenamePlan` transactionally with automatic rollback.
* **Steps:**

  1. Create `core/apply.py` with `apply_plan(plan: RenamePlan, verify_hash=False)`.
  2. Iterate plan items: call `atomic_move`; update per‑item status (`MOVED`, `SKIPPED`, `FAILED`).
  3. Maintain rollback stack of successful moves.
  4. On first failure, iterate stack in reverse calling `atomic_move` to restore.
  5. Return `ApplyResult` dataclass (success bool, failures list, duration).
  6. Unit tests: all‑success, mid‑failure triggers rollback, hash‑mismatch failure.
* **Done when:** Integration tests confirm no partial moves remain after simulated failure.

### 1.4 Undo Engine & CLI

* **Goal:** Single command to revert any stored plan.
* **Steps:**

  1. Implement `core/undo.py` with `undo_plan(plan_path: Path)`.
  2. Parse plan JSON and iterate items with reversed source/dest.
  3. Require confirmation unless `--yes` passed.
  4. Log each revert operation; stop and warn if source already exists.
  5. Expose Typer command `undo` with autocompletion of available plan IDs.
  6. Unit tests: undo restores original hashes; undo of already‑undone plan exits code 1.
* **Done when:** `namegnome undo <ID>` round‑trips library in integration test.

### 1.5 Progress & Logging

* **Goal:** Provide clear user feedback and audit trail.
* **Steps:**

  1. Create `utils/logging.py` wrapping `rich.progress.Progress` with custom columns (spinner, bar, percentage, ETA).
  2. During `apply` and `undo`, create progress task per operation.
  3. Use `progress.console.log()` to stream structured JSON lines to `runs/<id>.log` (ANSI‑free).
  4. Add `--no-progress` flag for scripting / CI.
  5. Unit test capturing console output with `caprich` fixture; ensure log file written.
* **Done when:** Sample run shows coloured progress locally and produces clean log file.

### 1.6 Integration Tests

* **Goal:** Validate real‑world workflow on all supported OSes.
* **Steps:**

  1. Under `tests/integration/`, build fixture tree with nested seasons, dotfiles, non‑ASCII names.
  2. Run CLI commands via `subprocess.run([...], check=True)` to mimic end user.
  3. Assert library state after `scan` unchanged; after `apply` reflects renamed paths; after `undo` matches original snapshot (hash compare + dircmp).
  4. Parametrise test for verify‑hash true/false and skip‑identical flag.
* **Done when:** Integration suite passes on Ubuntu, macOS, Windows CI runners.

### 1.7 Docs Update

* **Goal:** Teach users how to safely rename and roll back.
* **Steps:**

  1. Update `README.md` with `apply` / `undo` command examples, flags, and sample diff screenshot.
  2. Add a GIF (generated via `asciinema` + `svg-term`) demonstrating progress bar and rollback.
  3. Document exit codes and meanings.
  4. Include troubleshooting section for common failures (permissions, long paths).
* **Done when:** Docs render correctly on GitHub and link checker passes.

---

## 3 · Sprint 2 (MVP 0.3 "Metadata APIs" — Fully Expanded)

This sprint adds real metadata lookups, caching, and rule integration.

### 2.1 Provider Abstraction Interface

* **Goal:** Single contract for all metadata sources.
* **Steps:**

  1. Create `metadata/base.py` with `class MetadataClient(ABC)` defining async `search(title, year)` and `details(id)`.
  2. Define `MediaMetadata` dataclass (title, year, ids, episodes list, artwork URLs, runtime, plot).
  3. Provide helper `normalize_title()` and `strip_articles()` utilities.
* **Done when:** Base class documented; `MediaMetadata` JSON‑serialisable.

### 2.2 TMDB Client

* **Goal:** Primary movie/TV data source.
* **Steps:**

  1. Implement `TMDBClient` using `httpx.AsyncClient` with base URL `https://api.themoviedb.org/3`.
  2. Methods: `search_movie`, `search_tv`, `details_movie`, `details_tv`.
  3. Map results to `MediaMetadata`; pull poster/backdrop sizes w500/w780.
  4. Cache responses via decorator (see 2.9).
  5. Unit tests mock endpoints with `respx` ensuring correct mapping.
* **Done when:** `TMDBClient.search_movie("Inception",2010)` returns expected metadata in test.

### 2.3 TVDB Client

* **Goal:** Reliable episode titles & absolute numbers.
* **Steps:**

  1. Auth flow: POST `/login` with API key; store JWT expiration.
  2. Endpoints: `/search/series`, `/series/{id}/episodes/default`.
  3. Map season/episode data to `MediaMetadata.episodes` list.
  4. Handle pagination.
  5. Tests with stub JSON verify mapping and token refresh.
* **Done when:** Fixture show returns correct SxxExx titles.

### 2.4 MusicBrainz Client

* **Goal:** Album/track metadata for music renaming/tagging.
* **Steps:**

  1. Rate‑limit wrapper: 1 request per second (async sleep).
  2. Endpoints: `/recording`, `/release`, `/artist` with `inc=aliases+tags`.
  3. Resolve release by album + artist; fallback to recording search.
  4. Map to `MediaMetadata` with track positions.
  5. Tests mock two requests and assert sleep called.
* **Done when:** Album fixture yields track metadata list.

### 2.5 OMDb Client

* **Goal:** Supplement TMDB gaps (ratings, full plot).
* **Steps:**

  1. Simple GET `http://www.omdbapi.com/?apikey=KEY&t=TITLE&y=YEAR`.
  2. Merge fields into existing `MediaMetadata` if TMDB already populated.
  3. Unit test verifies merge priority (TMDB overrides OMDb conflicting fields).
* **Done when:** Combined metadata includes IMDb rating and plot.

### 2.6 Fanart.tv Client

* **Goal:** Fetch high‑quality artwork.
* **Steps:**

  1. Endpoint `https://webservice.fanart.tv/v3/movies/{tmdbid}`.
  2. Parse URL list, pick highest resolution.
  3. Cache file in `.namegnome/artwork/<tmdbid>/poster.jpg`.
  4. Provide CLI option `--artwork` to download.
* **Done when:** Poster file exists on disk after scan with flag.

### 2.7 AniList/AniDB Client

* **Goal:** Handle anime absolute numbering.
* **Steps:**

  1. Use AniList GraphQL: query by title; fetch `mediaListEntry{id,media{title,episodes}}`.
  2. Map to episode titles with absolute indices.
  3. Tests with mocked GraphQL response.
* **Done when:** Anime fixture file gets absolute number and correct title.

### 2.8 TheAudioDB Client

* **Goal:** Artist & album art for music tagging.
* **Steps:**

  1. Endpoint `https://theaudiodb.com/api/v1/json/KEY/search.php?s=ARTIST`.
  2. Save thumbnails; update `MediaMetadata.artwork` list.
* **Done when:** Album fixture downloads thumb.

### 2.9 Local Cache Layer

* **Goal:** Reduce API hits and support offline scans.
* **Steps:**

  1. Create `metadata/cache.py` with SQLite table: provider, key_hash, json_blob, expires_ts.
  2. Decorator `@cache(ttl=86400)` wraps provider methods.
  3. CLI flag `--no-cache` bypasses.
  4. Unit tests hit same endpoint twice; second call returns cached JSON.
* **Done when:** Coverage 100 % for cache module.

### 2.10 Rule Engine Integration

* **Goal:** Use metadata in naming.
* **Steps:**

  1. Extend `RuleSet` to accept optional `MediaMetadata`.
  2. For movies: include year in folder; for TV: include episode title.
  3. Update tests to expect new filenames.
* **Done when:** Planner produces title‑enriched target paths.

### 2.11 Unit Tests & Fixtures

* **Goal:** Ensure provider stability.
* **Steps:**

  1. For each client, load stub JSON under `tests/fixtures/api/{provider}`.
  2. Use `respx` to route requests.
  3. Parametrise tests for success, 404, rate‑limit error.
* **Done when:** All tests green and coverage ≥ 85 % for `metadata` package.

### 2.12 Config & Error Handling

* **Goal:** Centralise API keys and graceful failure.
* **Steps:**

  1. Implement `Settings` class via `pydantic.BaseSettings` reading `.env`.
  2. CLI command `config --show` prints resolved settings.
  3. If key missing, raise `MissingAPIKeyError` with link to docs.
* **Done when:** Running scan without keys prints clear message and exits code 1.

### 2.13 Docs Update

* **Goal:** Document provider configuration.
* **Steps:**

  1. Create `docs/providers.md` with table: provider, required key, free tier, scopes.
  2. Add `.env.example` template.
  3. Update README quick‑start to include key setup.
* **Done when:** Link checker passes; docs screenshots show provider config.

---

## 4 · Sprint 3 (MVP 0.4 "LLM Fuzzy Assist" — Fully Expanded)

This sprint introduces AI‑assisted fuzzy matching, anthology handling, and manual override workflow.

### 3.1 Ollama Wrapper Module

* **Goal:** Provide asynchronous interface to local Ollama server.
* **Steps:**

  1. Create `llm/ollama_client.py` exposing async `generate(model: str, prompt: str, stream: bool = True) -> str`.
  2. Use `httpx.AsyncClient` to POST `/api/generate` with JSON `{model,prompt,stream}`.
  3. If `stream=True`, yield chunks and accumulate; support `async for` usage.
  4. Raise custom `LLMUnavailableError` on connection timeout/refusal.
  5. Unit tests: successful stream concatenation, timeout raises error, wrong model returns 400.
* **Done when:** Wrapper passes all tests and handles 3 failure modes.

### 3.2 Model Discovery & Selection

* **Goal:** Allow users to list and choose installed models.
* **Steps:**

  1. Add `ollama_client.list_models()` calling `/api/tags`.
  2. Implement Typer command group `llm` with subcommands `list` and option `--llm-model` on `scan`.
  3. Persist default model in `~/.config/namegnome/config.toml` via `tomli-w`.
  4. Auto‑complete model names in CLI using Typer callback.
  5. Tests mock `/api/tags` response and validate persistence.
* **Done when:** `namegnome llm list` prints detected models and `--llm-model` overrides default.

### 3.3 Prompt Template System

* **Goal:** Maintain reusable, editable prompts.
* **Steps:**

  1. Add dependency `jinja2` (runtime) and create folder `prompts/`.
  2. Templates: `anthology.j2`, `title_guess.j2`, `id_hint.j2`.
  3. Create `llm/prompt_loader.py` with `render(template_name, **context)`; raise if missing var.
  4. Integrate into planner: build prompt context from filename and CLI flags.
  5. Unit tests render each template with sample context; assert placeholder replaced.
* **Done when:** All templates render without undefined errors and are 100 % covered.

### 3.4 Anthology Episode Splitter

* **Goal:** Correctly split multi‑episode files using LLM assistance.
* **Steps:**

  1. Detect patterns like `S01E01E02`, `E01-E02`, `1x01-1x02` via regex in scanner.
  2. For detected file, call `render('anthology.j2', context)` then `ollama_client.generate`.
  3. Parse JSON response `{segments:[{"title":"...","episode":"S01E01"},...]}`.
  4. Duplicate `RenamePlanItem` for each segment with appropriate episode number and title.
  5. Unit tests: fixture mp4 produces two plan items; malformed JSON triggers MANUAL flag.
* **Done when:** Dual‑episode fixture renamed into `E01` & `E02` files with correct titles.

### 3.5 Confidence Scoring & Manual Flags

* **Goal:** Prevent bad AI guesses from auto‑renaming.
* **Steps:**

  1. Expect `confidence` float in LLM JSON; default threshold 0.7 (`NGN_LLM_THRESHOLD`).
  2. If confidence < threshold, mark `RenamePlanItem.manual=True` and add reason.
  3. Modify renderer: highlight MANUAL rows in bright red; summary footer counts manual items.
  4. CLI exits code 2 if any manual items detected.
  5. Unit tests: low‑confidence response triggers manual; high passes.
* **Done when:** Planner flags low‑confidence items and CLI behaves per spec.

### 3.6 LLM Unit & Integration Tests

* **Goal:** Ensure deterministic AI behaviour in CI.
* **Steps:**

  1. Mock Ollama responses using `respx`; store fixture JSON files under `tests/llm/`.
  2. Tests for success, low confidence, invalid JSON, connection error.
  3. Integration: run `scan` on anthology tree with mock server and assert expanded plan & exit codes.
* **Done when:** Coverage for `llm/` package ≥ 90 %.

### 3.7 Performance & Safety Guards

* **Goal:** Prevent runaway prompt sizes and redundant calls.
* **Steps:**

  1. Implement size check: prompt length > 10_000 chars or > 2 MB aborts with warning.
  2. Add SQLite table `llm_cache(hash, model, response, ts)`; hash key = SHA‑1(filename+prompt).
  3. Decorate `ollama_client.generate` with cache lookup; honour `--no-cache` flag.
  4. Unit test calling same prompt twice hits cache second time.
* **Done when:** Cache reduces duplicate call count in test logs.

### 3.8 Documentation & Examples

* **Goal:** Teach users AI features and safety.
* **Steps:**

  1. Create `docs/llm.md` covering model install, list, threshold, cache path.
  2. Record asciinema of anthology file being split; embed GIF.
  3. Update README with `--llm-model` and manual flag behaviour.
* **Done when:** Docs pass lint; example commands reproduce expected output.

### 3.9 LLM Orchestration Refactor

* **Goal:** Modularize the LLM prompt orchestration code for maintainability and testability.
* **Steps:**
  1. Analyze `llm/prompt_orchestrator.py` and identify logical groupings: prompt builders, LLM orchestration, parsing/sanitization, and debug/log helpers.
  2. Create new modules under `llm/`:
     - `prompt_builders.py` (all prompt construction functions)
     - `llm_parsing.py` (all parsing/sanitization of LLM output)
     - `prompt_orchestrator.py` (high-level orchestration, public API)
     - (Optional) `llm_debug.py` (debug/log helpers, if needed)
  3. Move code from `prompt_orchestrator.py` into the appropriate new modules, updating imports and references throughout the codebase.
  4. Remove all print statements; replace with logging or Rich `console.log` only where user-facing or essential for debugging.
  5. Update or add tests for each new module, ensuring coverage for all moved functions.
  6. Verify that all CLI commands and tests still pass, and that no file exceeds 500 lines.
  7. Document the new module structure and update any affected docstrings or developer docs.
* **Done when:** All code is modularized, print statements are removed, tests pass, and documentation is up to date.

### 3.10 Apply Command Implementation

* **Goal:** Implement the `apply` CLI command to execute rename plans transactionally, with rollback and user feedback.
* **Steps:**
  1. Create a new Typer CLI command `apply` in `cli/commands.py` that accepts a plan ID or path.
  2. Load the specified plan using the plan store utilities.
  3. Iterate over plan items and call `atomic_move` for each, updating status (`MOVED`, `SKIPPED`, `FAILED`) as appropriate.
  4. Maintain a rollback stack of successful moves; on failure, automatically revert all completed moves.
  5. Display a Rich progress bar and log each operation to the console and a log file.
  6. Support flags for dry-run, hash verification, and skip-identical logic.
  7. Return a summary table of results, including any failures or skipped items.
  8. Exit with appropriate code: 0 for success, 1 for error, 2 if manual intervention is required.
  9. Add tests for all expected, edge, and failure cases, including rollback and dry-run.
  10. Update documentation and CLI help to include the new command and usage examples.
* **Done when:** The `apply` command is fully functional, tested, documented, and passes all pre-commit and CI checks.

---

## 5 · Sprint 4 (MVP 0.5 "GUI Companion & Advanced Tagging" — Fully Expanded)

This sprint ships a local web GUI, music tag editing, and optional desktop bundle.

### 4.1 FastAPI Backend Layer

* **Goal:** Expose namegnome core actions over HTTP for GUI/automation.
* **Steps:**

  1. Add `api/__init__.py` with FastAPI `app` and health route.
  2. Endpoints: `POST /scan` (accept path, flags; return plan JSON), `POST /apply`, `POST /undo/{id}`.
  3. Pydantic response models reuse `RenamePlan`, `ApplyResult`.
  4. Enable CORS for `http://localhost:3000`.
  5. Unit tests using `httpx.AsyncClient(app=app,base_url="http://test")` for each route.
* **Done when:** `uvicorn namegnome.api:app` serves endpoints and tests pass.

### 4.2 Next.js Front‑End Scaffold

* **Goal:** Create React UI shell with Styled Components.
* **Steps:**

  1. Init project `apps/gui` using `create-next-app --typescript`.
  2. Configure ESLint + Prettier; add Styled Components babel plugin.
  3. Pages: `/` dashboard, `/scan`, `/plan/[id]`, `/settings`.
  4. Global theme file with color vars matching Rich table legend.
  5. Vercel dev server proxy to FastAPI port via next.config.
* **Done when:** `pnpm dev` renders placeholder pages with nav bar.

### 4.3 Shared Types via OpenAPI Generator

* **Goal:** Type‑safe API client in GUI.
* **Steps:**

  1. Generate OpenAPI JSON from FastAPI (`app.openapi()`