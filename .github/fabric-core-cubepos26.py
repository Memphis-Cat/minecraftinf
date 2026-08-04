#!/usr/bin/env python3
"""Add Minecraft 26.2 position validity APIs to the CubicChunksCore bridge."""

from pathlib import Path

cube_pos = Path("CubicChunksCore/src/main/java/io/github/opencubicchunks/cc_core/api/CubePos.java")
text = cube_pos.read_text(encoding="utf-8")

method = '''    /**
     * Minecraft 26.2 validates a position before constructing generation holders.
     * Cubes are valid only while all three packed coordinates remain inside the
     * public CubePos coordinate range.
     */
    @UsedFromASM
    public boolean isValid() {
        return this.isInsideInclusive(
                -MAX_COORDINATE_VALUE, -MAX_COORDINATE_VALUE, -MAX_COORDINATE_VALUE,
                MAX_COORDINATE_VALUE, MAX_COORDINATE_VALUE, MAX_COORDINATE_VALUE
        );
    }

'''

if "public boolean isValid()" not in text:
    anchor = "    @UsedFromASM\n    public long asLong() {\n"
    if anchor not in text:
        raise SystemExit("Unable to locate CubePos.asLong insertion point")
    text = text.replace(anchor, method + anchor, 1)

if "public boolean isValid()" not in text or "-MAX_COORDINATE_VALUE" not in text:
    raise SystemExit("Failed to install CubePos.isValid for Minecraft 26.2")

cube_pos.write_text(text, encoding="utf-8")
print("Added Minecraft 26.2 CubePos validity checking")
