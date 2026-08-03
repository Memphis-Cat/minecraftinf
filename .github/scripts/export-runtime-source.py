from pathlib import Path
import json
import shutil
import subprocess
import tarfile

MARKER = "\n// CC_RUNTIME_EXPORT_BEGIN\n"
HELPER_PATH = Path(".github/scripts/export-runtime-source.py")
BUILD_FILE = Path("build.gradle")
OUTPUT = Path("build/reports/runtime-source-snapshot")
EXCLUDED_PATH = ":(exclude).github/scripts/export-runtime-source.py"


def git_output(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True)


# Remove the temporary Gradle task configuration before calculating the source
# diff so the exported patch contains only the actual runtime implementation.
build_text = BUILD_FILE.read_text()
if MARKER not in build_text:
    raise SystemExit("Runtime source export marker is missing from build.gradle")
BUILD_FILE.write_text(build_text.split(MARKER, 1)[0])
HELPER_PATH.unlink()

if OUTPUT.exists():
    shutil.rmtree(OUTPUT)
files_root = OUTPUT / "files"
files_root.mkdir(parents=True)

name_status = git_output("diff", "--name-status", "HEAD", "--", ".", EXCLUDED_PATH)
(OUTPUT / "name-status.txt").write_text(name_status)

entries = []
for line in name_status.splitlines():
    fields = line.split("\t")
    if len(fields) < 2:
        continue
    status = fields[0]
    paths = fields[1:]
    entries.append({"status": status, "paths": paths})
    if status.startswith("D"):
        continue
    source_path = Path(paths[-1])
    if not source_path.is_file():
        continue
    destination = files_root / source_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination)

(OUTPUT / "manifest.json").write_text(json.dumps(entries, indent=2) + "\n")
with (OUTPUT / "integration.patch").open("wb") as patch:
    subprocess.run(
        ["git", "diff", "--binary", "HEAD", "--", ".", EXCLUDED_PATH],
        stdout=patch,
        check=True,
    )
with tarfile.open(OUTPUT / "runtime-source-files.tar.gz", "w:gz") as archive:
    archive.add(files_root, arcname="files")
    archive.add(OUTPUT / "manifest.json", arcname="manifest.json")
    archive.add(OUTPUT / "name-status.txt", arcname="name-status.txt")
    archive.add(OUTPUT / "integration.patch", arcname="integration.patch")
