#!/usr/bin/env python3
"""Inspect the official Minecraft distribution without relying on Loom."""

from __future__ import annotations

import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

VERSION = "26.2"
MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
OUTPUT = Path("fabric-minecraft-distribution.log")


def fetch_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=120) as response:
        return json.load(response)


def fetch_bytes(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=300) as response:
        return response.read()


def inspect_zip(label: str, data: bytes, out: list[str]) -> None:
    out.append(f"{label}: bytes={len(data)} sha256={hashlib.sha256(data).hexdigest()}")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = archive.namelist()
            classes = [name for name in names if name.endswith(".class")]
            jars = [name for name in names if name.endswith(".jar")]
            out.append(f"{label}: entries={len(names)} classes={len(classes)} nested_jars={len(jars)}")
            out.append(f"{label}: first_entries={names[:80]}")
            out.append(f"{label}: first_classes={classes[:80]}")
            out.append(f"{label}: nested_jars={jars[:80]}")
            for nested_name in jars[:20]:
                try:
                    nested = archive.read(nested_name)
                    with zipfile.ZipFile(io.BytesIO(nested)) as nested_archive:
                        nested_names = nested_archive.namelist()
                        nested_classes = [name for name in nested_names if name.endswith(".class")]
                        out.append(
                            f"{label}/{nested_name}: bytes={len(nested)} "
                            f"entries={len(nested_names)} classes={len(nested_classes)} "
                            f"first_classes={nested_classes[:30]}"
                        )
                except (KeyError, zipfile.BadZipFile) as exc:
                    out.append(f"{label}/{nested_name}: unable to inspect: {exc}")
    except zipfile.BadZipFile as exc:
        out.append(f"{label}: not a zip: {exc}")


def main() -> int:
    lines: list[str] = []
    manifest = fetch_json(MANIFEST_URL)
    entry = next((item for item in manifest["versions"] if item["id"] == VERSION), None)
    if entry is None:
        raise RuntimeError(f"Minecraft {VERSION} is absent from the official version manifest")

    lines.append(f"version_entry={json.dumps(entry, sort_keys=True)}")
    version_json = fetch_json(entry["url"])
    lines.append(f"version_json_keys={sorted(version_json)}")
    lines.append(f"mainClass={version_json.get('mainClass')}")
    lines.append(f"javaVersion={json.dumps(version_json.get('javaVersion'), sort_keys=True)}")
    lines.append(f"downloads={json.dumps(version_json.get('downloads'), sort_keys=True)}")

    libraries = version_json.get("libraries", [])
    lines.append(f"library_count={len(libraries)}")
    for library in libraries:
        name = str(library.get("name", ""))
        artifact = library.get("downloads", {}).get("artifact", {})
        path = str(artifact.get("path", ""))
        if "minecraft" in name.lower() or "minecraft" in path.lower() or name.startswith("net.minecraft"):
            lines.append(f"minecraft_library={json.dumps(library, sort_keys=True)}")

    for key, descriptor in sorted(version_json.get("downloads", {}).items()):
        url = descriptor.get("url")
        if not url:
            continue
        data = fetch_bytes(url)
        inspect_zip(f"download[{key}]", data, lines)

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUTPUT.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # diagnostics must preserve the actual failure
        print(f"Minecraft distribution inspection failed: {exc}", file=sys.stderr)
        raise
