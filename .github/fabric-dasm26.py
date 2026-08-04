#!/usr/bin/env python3
"""Port DASM and transformed-call signatures to Minecraft 26.2."""

from pathlib import Path

redirect_files = (
    Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/dasmsets/ChunkToCubeSet.java"),
    Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/dasmsets/ChunkToCloSet.java"),
)

for path in redirect_files:
    text = path.read_text(encoding="utf-8")
    text = text.replace('@MethodRedirect("toLong()J")', '@MethodRedirect("pack()J")')
    text = text.replace('@MethodRedirect("asLong(II)J")', '@MethodRedirect("pack(II)J")')
    if '@MethodRedirect("toLong()J")' in text or '@MethodRedirect("asLong(II)J")' in text:
        raise SystemExit(f"Obsolete ChunkPos DASM packing redirect remains in {path}")
    path.write_text(text, encoding="utf-8")

cube = redirect_files[0].read_text(encoding="utf-8")
clo = redirect_files[1].read_text(encoding="utf-8")
if '@MethodRedirect("pack()J")' not in cube:
    raise SystemExit("Missing Minecraft 26.2 instance ChunkPos.pack redirect")
if '@MethodRedirect("pack(II)J")' not in cube or '@MethodRedirect("pack(II)J")' not in clo:
    raise SystemExit("Missing Minecraft 26.2 static ChunkPos.pack redirect")

# DistanceManager's player-ticket methods still exist, but their ChunkPos key call
# was renamed from toLong() to pack(). Keep the cubic SectionPos routing intact.
distance_manager = Path(
    "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinDistanceManager.java"
)
text = distance_manager.read_text(encoding="utf-8")
text = text.replace(
    'target = "Lnet/minecraft/world/level/ChunkPos;toLong()J"',
    'target = "Lnet/minecraft/world/level/ChunkPos;pack()J"',
)
if 'ChunkPos;toLong()J' in text:
    raise SystemExit("Obsolete DistanceManager ChunkPos.toLong injection remains")
if text.count('ChunkPos;pack()J') < 2:
    raise SystemExit("Missing Minecraft 26.2 DistanceManager ChunkPos.pack injections")
distance_manager.write_text(text, encoding="utf-8")

# shouldForceNaturalSpawning was a NeoForge-only hook and was removed from
# Minecraft 26.2 TicketStorage. CubicTicketStorage has no such API and there are
# no Fabric callers, so do not ask DASM to clone a nonexistent source method.
ticket_storage = Path(
    "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/world/level/MixinTicketStorage.java"
)
text = ticket_storage.read_text(encoding="utf-8")
method_name = "cc_shouldForceNaturalSpawning"
name_index = text.find(method_name)
if name_index >= 0:
    annotation_start = text.rfind("    // TODO move to neoforge-specific mixin", 0, name_index)
    if annotation_start < 0:
        annotation_start = text.rfind("    @AddTransformToSets", 0, name_index)
    semicolon = text.find(";", name_index)
    if annotation_start < 0 or semicolon < 0:
        raise SystemExit("Unable to locate obsolete TicketStorage natural-spawn transform")
    method_end = semicolon + 1
    while method_end < len(text) and text[method_end] == "\n":
        method_end += 1
    text = text[:annotation_start] + text[method_end:]
if method_name in text or "shouldForceNaturalSpawning" in text:
    raise SystemExit("Obsolete TicketStorage natural-spawn transform remains")
ticket_storage.write_text(text, encoding="utf-8")

print("Migrated Minecraft 26.2 DASM redirects and ticket hooks")
