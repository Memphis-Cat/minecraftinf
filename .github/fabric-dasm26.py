#!/usr/bin/env python3
"""Port shared DASM redirect sets to Minecraft 26.2 ChunkPos packing names."""

from pathlib import Path

files = (
    Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/dasmsets/ChunkToCubeSet.java"),
    Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/dasmsets/ChunkToCloSet.java"),
)

for path in files:
    text = path.read_text(encoding="utf-8")
    text = text.replace('@MethodRedirect("toLong()J")', '@MethodRedirect("pack()J")')
    text = text.replace('@MethodRedirect("asLong(II)J")', '@MethodRedirect("pack(II)J")')
    if '@MethodRedirect("toLong()J")' in text or '@MethodRedirect("asLong(II)J")' in text:
        raise SystemExit(f"Obsolete ChunkPos DASM packing redirect remains in {path}")
    path.write_text(text, encoding="utf-8")

cube = files[0].read_text(encoding="utf-8")
clo = files[1].read_text(encoding="utf-8")
if '@MethodRedirect("pack()J")' not in cube:
    raise SystemExit("Missing Minecraft 26.2 instance ChunkPos.pack redirect")
if '@MethodRedirect("pack(II)J")' not in cube or '@MethodRedirect("pack(II)J")' not in clo:
    raise SystemExit("Missing Minecraft 26.2 static ChunkPos.pack redirect")

print("Migrated shared DASM ChunkPos packing redirects to Minecraft 26.2")
