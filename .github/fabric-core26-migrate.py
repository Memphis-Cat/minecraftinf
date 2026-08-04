#!/usr/bin/env python3
"""Port CubicChunksCore's Minecraft header bridge and tests to Minecraft 26.2."""

from pathlib import Path

root = Path("CubicChunksCore")
header = root / "src/main/java/io/github/opencubicchunks/cc_core/minecraft/MCChunkPos.java"
header.write_text(
    """package io.github.opencubicchunks.cc_core.minecraft;

import io.github.opencubicchunks.javaheaders.api.Header;

/** Minecraft 26.2 ChunkPos header used by JavaHeaders. */
@Header
public class MCChunkPos {
    public MCChunkPos(int x, int z) {
        throw new IllegalStateException("Per-version doesn't overwrite method");
    }

    public native int x();
    public native int z();
    public native long pack();

    public native static MCChunkPos unpack(long packedPos);
    public native static long pack(int x, int z);
    public native static int getX(long chunkAsLong);
    public native static int getZ(long chunkAsLong);
}
""",
    encoding="utf-8",
)

# Apply API substitutions throughout Core rather than relying on direct record
# field access, which is private in Minecraft 26.2 bytecode.
for path in (root / "src").rglob("*.java"):
    source = path.read_text(encoding="utf-8")
    source = source.replace("MCChunkPos.asLong(", "MCChunkPos.pack(")
    source = source.replace("MCChunkPos#toLong", "MCChunkPos#pack")
    source = source.replace("columnPos.x", "columnPos.x()")
    source = source.replace("columnPos.z", "columnPos.z()")
    source = source.replace("position.x", "position.x()")
    source = source.replace("position.z", "position.z()")
    source = source.replace("new MCChunkPos(chunkLong)", "MCChunkPos.unpack(chunkLong)")
    source = source.replace("import static org.hamcrest.junit.MatcherAssert.assertThat;", "import static org.hamcrest.MatcherAssert.assertThat;")
    path.write_text(source, encoding="utf-8")

# Preserve the instance packing paths introduced by the earlier migration while
# also accepting the exact 26.2 static pack API.
cube_pos = root / "src/main/java/io/github/opencubicchunks/cc_core/api/CubePos.java"
text = cube_pos.read_text(encoding="utf-8")
text = text.replace(
    "return new MCChunkPos(Coords.cubeToSection(CubePos.extractX(cubePosIn), localX), Coords.cubeToSection(CubePos.extractZ(cubePosIn), localZ)).pack();",
    "return MCChunkPos.pack(Coords.cubeToSection(CubePos.extractX(cubePosIn), localX), Coords.cubeToSection(CubePos.extractZ(cubePosIn), localZ));",
)
cube_pos.write_text(text, encoding="utf-8")

clo_pos = root / "src/main/java/io/github/opencubicchunks/cc_core/world/level/CloPos.java"
text = clo_pos.read_text(encoding="utf-8")
text = text.replace("return new MCChunkPos(x, z).pack();", "return MCChunkPos.pack(x, z);")
text = text.replace("return new MCChunkPos(x, MCChunkPos.getZ(packed)).pack();", "return MCChunkPos.pack(x, MCChunkPos.getZ(packed));")
text = text.replace("return new MCChunkPos(MCChunkPos.getX(packed), z).pack();", "return MCChunkPos.pack(MCChunkPos.getX(packed), z);")
clo_pos.write_text(text, encoding="utf-8")

# Keep test expectations on the public 26.2 API.
for path in (root / "src/test/java").rglob("*.java"):
    source = path.read_text(encoding="utf-8")
    source = source.replace("new MCChunkPos(x, z).pack()", "MCChunkPos.pack(x, z)")
    source = source.replace("new MCChunkPos(root.getScale(), root.getScaledY()).pack()", "MCChunkPos.pack(root.getScale(), root.getScaledY())")
    source = source.replace("new MCChunkPos(node.getScale(), node.getScaledY()).pack()", "MCChunkPos.pack(node.getScale(), node.getScaledY())")
    source = source.replace("new MCChunkPos(child.getScale(), child.getScaledY()).pack()", "MCChunkPos.pack(child.getScale(), child.getScaledY())")
    path.write_text(source, encoding="utf-8")

remaining = []
for path in (root / "src").rglob("*.java"):
    source = path.read_text(encoding="utf-8")
    forbidden = (
        "MCChunkPos.asLong",
        "MCChunkPos#toLong",
        "columnPos.x;",
        "columnPos.z;",
        "position.x)",
        "position.z)",
        "new MCChunkPos(chunkLong)",
        "org.hamcrest.junit.MatcherAssert",
    )
    if any(marker in source for marker in forbidden):
        remaining.append(str(path))
if remaining:
    raise SystemExit("Unmigrated Minecraft 26.2 Core API calls remain: " + ", ".join(remaining))

print("Migrated CubicChunksCore to the Minecraft 26.2 ChunkPos record API")
