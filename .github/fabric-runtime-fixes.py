#!/usr/bin/env python3
"""Apply verified runtime correctness fixes that are independent of API renames."""

from pathlib import Path

path = Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/world/level/MixinLevel.java")
text = path.read_text(encoding="utf-8")

broken = """        if (cc_isCubic) {
            return ((CubeSource) chunkSource).cc_hasCube(Coords.blockToCube(blockPos.getX()), Coords.blockToCube(blockPos.getY()),
                    Coords.blockToCube(blockPos.getZ()));
        }
        return false;
"""
fixed = """        if (cc_isCubic) {
            return ((CubeSource) chunkSource).cc_hasCube(Coords.blockToCube(blockPos.getX()), Coords.blockToCube(blockPos.getY()),
                    Coords.blockToCube(blockPos.getZ()));
        }
        return original.call(chunkSource, x, z);
"""

if broken in text:
    text = text.replace(broken, fixed, 1)
elif fixed not in text:
    raise SystemExit("Could not locate the Level.isLoaded cubic wrapper")

path.write_text(text, encoding="utf-8")
print("Applied verified Fabric runtime correctness fixes")
