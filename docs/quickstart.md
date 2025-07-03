# NameGnome Quickstart Guide

Welcome! This guide will help you get started with NameGnome, even if you have
never used the command line before. Follow these steps to organize your media
files quickly and safely.

---

## 0. TL;DR (60-second setup)

```bash
# 1. Install (isolated, recommended)
pipx install namegnome

# 2. Scan your TV folder (dry-run, nothing changes!)
namegnome scan ~/Media/TV --media-type tv --json

# 3. Review the plan ID printed at the end – when happy:
namegnome apply <plan-id>

# 4. Need to revert?
namegnome undo <plan-id>
```

---

## 1. What is NameGnome?

NameGnome is a **safety-first** command-line tool that organises and renames
TV, movie and music files so they play nicely with media servers such as **Plex**
or **Jellyfin**. Key guarantees:

* Scan is read-only – it never touches your files.
* Apply is transactional – any error triggers an automatic rollback.
* Undo restores the original state at any time.

---

## 2. Requirements

* **Python 3.12+**
* macOS, Linux or Windows
* Optional provider API keys (TMDB, TVDB…) – see `docs/providers.md`

---

## 3. Installation

### With pipx (recommended)
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath  # add to $PATH
pipx install namegnome
```

### With pip
```bash
pip install --upgrade namegnome
```

Verify:
```bash
namegnome --version && namegnome --help | head -n 5
```

---

## 4. First Scan (dry-run)

Run **scan** with at least one `--media-type`:
```bash
namegnome scan /path/to/TV --media-type tv --json
```
Flags worth knowing:

* `--media-type tv|movie|music` – required, repeatable.
* `--platform plex|jellyfin` – naming rules engine (default `plex`).
* `--anthology` – enable smart multi-episode splitting.
* `--no-rich` – plain output, useful in CI.

The command prints a coloured diff and saves a **plan file** locally. Its ID looks like `20250701_123456.json` and the file is stored under `~/.namegnome/plans/`.

---

## 5. Apply the Plan (rename files)

```bash
namegnome apply <plan-id>
```
You will see a progress bar with percentage, elapsed time and current filename.
Interrupt with Ctrl-C to trigger an automatic rollback.

---

## 6. Undo (rollback later)

```bash
namegnome undo <plan-id>
```
This reverses every move and deletes any empty directories created during apply.

---

## 7. Configuration (optional)

All settings can be supplied as:
1. CLI flag – highest precedence
2. Environment variable e.g. `NAMEGNOME_SCAN_VERIFY_HASH=1`
3. TOML file `${XDG_CONFIG_HOME:-~/.config}/namegnome/config.toml`

Run `namegnome config docs` to see the full table.

---

## 8. Getting Help

* `namegnome --help` and sub-command `--help` flags
* Documentation under `docs/`
* GitHub issues & discussions – we're friendly!

Happy organising 🧙‍♂️✨

If you get stuck, open an issue on GitHub or ask for help in the project
community! 