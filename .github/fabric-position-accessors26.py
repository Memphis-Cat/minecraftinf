#!/usr/bin/env python3
"""Map Minecraft 26.2 ChunkPos record accessors to CubicChunksCore positions."""

from pathlib import Path

paths = (
    Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/dasmsets/ChunkToCloSet.java"),
    Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/dasmsets/ChunkToCubeSet.java"),
)

for path in paths:
    text = path.read_text(encoding="utf-8")
    for axis in ("x", "z"):
        getter = f"get{axis.upper()}"
        old = f'''        @FieldToMethodRedirect("{axis}:I")
        native int {getter}();
'''
        new = f'''        @FieldToMethodRedirect("{axis}:I")
        @MethodRedirect("{axis}()I")
        native int {getter}();
'''
        if old in text:
            text = text.replace(old, new, 1)
        elif f'@MethodRedirect("{axis}()I")' not in text:
            raise SystemExit(f"Unable to install {axis}() redirect in {path}")

    if '@MethodRedirect("x()I")' not in text or '@MethodRedirect("z()I")' not in text:
        raise SystemExit(f"Missing Minecraft 26.2 record accessor redirects in {path}")
    path.write_text(text, encoding="utf-8")

print("Mapped Minecraft 26.2 ChunkPos record accessors to Core positions")
