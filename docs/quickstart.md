# NameGnome Quickstart Guide

Welcome! This guide will help you get started with NameGnome, even if you have
never used the command line before. Follow these steps to organize your media
files quickly and safely.

---

## 1. What is NameGnome?

NameGnome is a tool that helps you organize and rename your TV shows, movies,
and music files so they work perfectly with media servers like Plex or Jellyfin.
It can:
- Scan your folders for media files
- Suggest new names and folders
- Help you fix tricky cases with AI (optional)
- Let you undo changes if needed

---

## 2. Prerequisites

- **Python 3.12 or higher**
- **pipx** (recommended for easy CLI installs)

To check if you have Python:
```sh
python3 --version
```
If you see a version like `Python 3.12.3`, you're good!

To install pipx (if you don't have it):
```sh
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

---

## 3. Install NameGnome

With pipx:
```sh
pipx install namegnome
```
Or with pip:
```sh
pip install namegnome
```

Check your install:
```sh
namegnome --help
```
You should see a list of commands.

---

## 4. Scan Your Media Folder

To preview how NameGnome would organize your files, you must specify at least one media type (tv, movie, or music):
```sh
namegnome scan /path/to/your/media --media-type tv
```
Replace `/path/to/your/media` with the folder where your files are. You can specify multiple types:
```sh
namegnome scan /path/to/your/media --media-type tv --media-type movie
```
**Note:** The --media-type option is required. NameGnome will not scan unless you specify at least one media type.

---

## 5. Preview and Apply Renames

- **Preview:** The scan will show a table of old and new names. No files are
  changed yet!
- **Apply:** To actually rename files, use:
  ```sh
  namegnome apply <plan-id>
  ```
  The `<plan-id>` is shown after a scan.

---

## 6. Undo Changes

If you want to undo a rename:
```sh
namegnome undo <plan-id>
```
This will restore your files to their original names.

---

## 7. Where to Get Help

- See the [LLM Features & Usage Guide](llm.md) for AI features
- See the [Provider Setup & API Keys](providers.md) doc for metadata/artwork
- See the [Known Issues & Troubleshooting](KNOWN_ISSUES.md) doc
- Or run:
  ```sh
  namegnome --help
  ```

If you get stuck, open an issue on GitHub or ask for help in the project
community! 