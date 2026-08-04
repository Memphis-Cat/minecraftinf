#!/usr/bin/env python3
"""Port ChunkAccess constructor injection to Minecraft 26.2."""

from pathlib import Path

path = Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/world/level/chunk/MixinChunkAccess.java")
text = path.read_text(encoding="utf-8")
text = text.replace("import net.minecraft.core.Registry;\n", "")
if "import net.minecraft.world.level.chunk.PalettedContainerFactory;\n" not in text:
    anchor = "import net.minecraft.world.level.chunk.LevelChunkSection;\n"
    if anchor not in text:
        raise SystemExit("Unable to add PalettedContainerFactory import")
    text = text.replace(anchor, anchor + "import net.minecraft.world.level.chunk.PalettedContainerFactory;\n", 1)
text = text.replace(
    "LevelHeightAccessor levelHeightAccessor, Registry biomeRegistry, long inhabitedTime,",
    "LevelHeightAccessor levelHeightAccessor, PalettedContainerFactory containerFactory, long inhabitedTime,",
)
if "Registry biomeRegistry" in text or "import net.minecraft.core.Registry;" in text:
    raise SystemExit("Obsolete ChunkAccess biome registry constructor parameter remains")
if "PalettedContainerFactory containerFactory" not in text:
    raise SystemExit("Minecraft 26.2 ChunkAccess constructor parameter was not installed")
if text.count("import net.minecraft.world.level.chunk.PalettedContainerFactory;") != 1:
    raise SystemExit("Expected exactly one PalettedContainerFactory import")
path.write_text(text, encoding="utf-8")
print("Migrated ChunkAccess constructor injection to Minecraft 26.2")
