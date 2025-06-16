import os
import shutil

SRC_DIR = "/Volumes/LaCie/TV Shows/WCO/Paw Patrol"
DEST_DIR = "/Users/douglasmackrell/Development/namegnome/tests/mocks/tv/Paw Patrol"
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"}

def get_files(directory):
    return {f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))}

def main():
    if not os.path.exists(SRC_DIR):
        print(f"Source directory does not exist: {SRC_DIR}")
        return
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
        print(f"Created destination directory: {DEST_DIR}")

    src_files = get_files(SRC_DIR)
    dest_files = get_files(DEST_DIR)

    # Only consider video files
    src_video_files = {f for f in src_files if os.path.splitext(f)[1].lower() in VIDEO_EXTS}
    missing_files = src_video_files - dest_files

    print(f"Found {len(src_video_files)} video files in source.")
    print(f"{len(dest_files)} files already in destination.")
    print(f"{len(missing_files)} files to copy.")

    for fname in sorted(missing_files):
        src_path = os.path.join(SRC_DIR, fname)
        dest_path = os.path.join(DEST_DIR, fname)
        print(f"Copying: {fname}")
        shutil.copy2(src_path, dest_path)

    print("Sync complete.")

if __name__ == "__main__":
    main()