from pathlib import Path
import shutil

SRC_DIR = Path("/Volumes/LaCie/TV Shows/WCO/Paw Patrol")
DEST_DIR = Path(
    "/Users/douglasmackrell/Development/namegnome/tests/mocks/tv/Paw Patrol"
)
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"}


def get_files(directory: Path):
    """Return a set of file names (not paths) contained directly in *directory*."""
    return {item.name for item in directory.iterdir() if item.is_file()}


def main():
    if not SRC_DIR.exists():
        print(f"Source directory does not exist: {SRC_DIR}")
        return
    if not DEST_DIR.exists():
        DEST_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created destination directory: {DEST_DIR}")

    src_files = get_files(SRC_DIR)
    dest_files = get_files(DEST_DIR)

    # Only consider video files
    src_video_files = {f for f in src_files if Path(f).suffix.lower() in VIDEO_EXTS}
    missing_files = src_video_files - dest_files

    print(f"Found {len(src_video_files)} video files in source.")
    print(f"{len(dest_files)} files already in destination.")
    print(f"{len(missing_files)} files to copy.")

    for fname in sorted(missing_files):
        src_path = SRC_DIR / fname
        dest_path = DEST_DIR / fname
        print(f"Copying: {fname}")
        shutil.copy2(src_path, dest_path)

    print("Sync complete.")


if __name__ == "__main__":
    main()
