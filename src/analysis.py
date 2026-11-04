import concurrent.futures
import glob
import os
import subprocess
import sys
import zipfile
from pathlib import Path


def reassemble_data_zip():
    """Reassemble data.zip from chunks if it doesn't exist."""
    if os.path.exists("data.zip"):
        return

    chunks = sorted(glob.glob("data.zip.*"))
    if not chunks:
        print("No data.zip chunks found.")
        return

    # Check if the chunks are git-lfs pointers instead of actual data
    with open(chunks[0], "rb") as f:
        header = f.read(25)
        if header.startswith(b"version https://git-lfs"):
            print("Error: data.zip chunks are git-lfs pointers, not the actual files.")
            print("Please run 'git lfs pull' to download the real data before proceeding.")
            sys.exit(1)

    print("Reassembling data.zip from chunks...")
    with open("data.zip", "wb") as output:
        for chunk in chunks:
            with open(chunk, "rb") as f:
                output.write(f.read())
    print("data.zip reassembled.")


def generate_data_directory():
    data_zip = Path("data.zip")
    data_dir = Path("data")

    if data_zip.exists() and not data_dir.exists():
        print("Extracting data.zip...")
        with zipfile.ZipFile(data_zip, "r") as zf:
            zf.extractall(".")
        print("Extraction complete.")


def cleanup_data_directory():
    data_dir = Path("data")
    if data_dir.exists():
        print("Cleaning up data directory...")
        import shutil
        shutil.rmtree(data_dir)
        print("Cleanup complete.")

    # delete data.zip as well
    data_zip = Path("data.zip")
    if data_zip.exists():
        data_zip.unlink()
        print("data.zip deleted.")


def run_analysis():
    data_dir = Path("data")
    if not data_dir.exists():
        print("Error: data directory not found.")
        print("Please run 'make setup' or 'uv run main.py setup' first.")
        sys.exit(1)

    analysis_dir = Path("research/analysis")
    scripts = sorted(analysis_dir.glob("*.py"))
    print(f"Running {len(scripts)} analysis scripts...")

    def run_script(script):
        result = subprocess.run(
            [sys.executable, str(script)], capture_output=True, text=True
        )
        return script.name, result

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(run_script, s): s for s in scripts}
        for future in concurrent.futures.as_completed(futures):
            name, result = future.result()
            if result.returncode != 0:
                print(f"[FAIL] {name}\n{result.stderr}")
            else:
                print(f"[OK] {name}")

    print(f"\nAll {len(scripts)} analysis scripts complete.")


def run_single_analysis(script_name: str):
    data_dir = Path("data")
    if not data_dir.exists():
        print("Error: data directory not found.")
        print("Please run 'make setup' or 'uv run main.py setup' first.")
        sys.exit(1)

    if not script_name.endswith(".py"):
        script_name = f"{script_name}.py"

    script = Path("research/analysis") / script_name
    if not script.exists():
        print(f"Script not found: {script}")
        sys.exit(1)

    print(f"Running {script_name}...")
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[FAIL] {script_name}\n{result.stderr}")
    else:
        print(f"[OK] {script_name}")
        if result.stdout:
            print(result.stdout)
