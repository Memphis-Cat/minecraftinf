#!/usr/bin/env python3
"""Port CubicChunksCore's Minecraft header bridge to the 26.2 ChunkPos API."""

from pathlib import Path

root = Path("CubicChunksCore")
header = root / "src/main/java/io/github/opencubicchunks/cc_core/minecraft/MCChunkPos.java"
text = header.read_text(encoding="utf-8")
text = text.replace("    public native long toLong();\n\n    public native static long asLong(int x, int z);\n", "    public native long pack();\n")
if "public native long pack();" not in text:
    raise SystemExit("Failed to migrate the CubicChunksCore MCChunkPos header")
header.write_text(text, encoding="utf-8")

cube_pos = root / "src/main/java/io/github/opencubicchunks/cc_core/api/CubePos.java"
text = cube_pos.read_text(encoding="utf-8")
text = text.replace(
    "return MCChunkPos.asLong(Coords.cubeToSection(CubePos.extractX(cubePosIn), localX), Coords.cubeToSection(CubePos.extractZ(cubePosIn), localZ));",
    "return new MCChunkPos(Coords.cubeToSection(CubePos.extractX(cubePosIn), localX), Coords.cubeToSection(CubePos.extractZ(cubePosIn), localZ)).pack();",
)
if "MCChunkPos.asLong" in text:
    raise SystemExit("A removed ChunkPos.asLong call remains in CubePos")
cube_pos.write_text(text, encoding="utf-8")

clo_pos = root / "src/main/java/io/github/opencubicchunks/cc_core/world/level/CloPos.java"
text = clo_pos.read_text(encoding="utf-8")
text = text.replace("return MCChunkPos.asLong(x, z);", "return new MCChunkPos(x, z).pack();")
text = text.replace("return MCChunkPos.asLong(x, MCChunkPos.getZ(packed));", "return new MCChunkPos(x, MCChunkPos.getZ(packed)).pack();")
text = text.replace("return MCChunkPos.asLong(MCChunkPos.getX(packed), z);", "return new MCChunkPos(MCChunkPos.getX(packed), z).pack();")
if "MCChunkPos.asLong" in text:
    raise SystemExit("A removed ChunkPos.asLong call remains in CloPos")
clo_pos.write_text(text, encoding="utf-8")

# Keep the published Core tests aligned with the migrated header API.
for path in (root / "src/test/java").rglob("*.java"):
    source = path.read_text(encoding="utf-8")
    source = source.replace("MCChunkPos.asLong(x, z)", "new MCChunkPos(x, z).pack()")
    source = source.replace("MCChunkPos.asLong(root.getScale(), root.getScaledY())", "new MCChunkPos(root.getScale(), root.getScaledY()).pack()")
    source = source.replace("MCChunkPos.asLong(node.getScale(), node.getScaledY())", "new MCChunkPos(node.getScale(), node.getScaledY()).pack()")
    source = source.replace("MCChunkPos.asLong(child.getScale(), child.getScaledY())", "new MCChunkPos(child.getScale(), child.getScaledY()).pack()")
    path.write_text(source, encoding="utf-8")

remaining = []
for path in (root / "src").rglob("*.java"):
    source = path.read_text(encoding="utf-8")
    if "MCChunkPos.asLong" in source or ".toLong()" in source and "MCChunkPos" in source:
        remaining.append(str(path))
if remaining:
    raise SystemExit("Unmigrated Minecraft 26.2 ChunkPos calls remain in CubicChunksCore: " + ", ".join(remaining))

print("Migrated CubicChunksCore to ChunkPos.pack() for Minecraft 26.2")
