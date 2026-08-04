#!/usr/bin/env python3
"""Implement LevelCube block and fluid reads directly for Minecraft 26.2."""

from pathlib import Path

path = Path("src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/LevelCube.java")
text = path.read_text(encoding="utf-8")

if "import net.minecraft.world.level.block.Blocks;\n" not in text:
    anchor = "import net.minecraft.world.level.block.Block;\n"
    if anchor not in text:
        raise SystemExit("Unable to add the Blocks import to LevelCube")
    text = text.replace(anchor, anchor + "import net.minecraft.world.level.block.Blocks;\n", 1)
if "import net.minecraft.world.level.material.Fluids;\n" not in text:
    anchor = "import net.minecraft.world.level.material.FluidState;\n"
    if anchor not in text:
        raise SystemExit("Unable to add the Fluids import to LevelCube")
    text = text.replace(anchor, anchor + "import net.minecraft.world.level.material.Fluids;\n", 1)

old = '''    // dasm + mixin
    @TransformFromMethod(value = "getBlockState(Lnet/minecraft/core/BlockPos;)Lnet/minecraft/world/level/block/state/BlockState;", owner = @Ref(LevelChunk.class))
    @Override public native @NotNull BlockState getBlockState(BlockPos pos);

    @TransformFromMethod(value = "getFluidState(Lnet/minecraft/core/BlockPos;)Lnet/minecraft/world/level/material/FluidState;", owner = @Ref(LevelChunk.class))
    @Override public native @NotNull FluidState getFluidState(BlockPos pos);

    // dasm + mixin
    @TransformFromMethod(value = "getFluidState(III)Lnet/minecraft/world/level/material/FluidState;", owner = @Ref(LevelChunk.class))
    @Override public native FluidState getFluidState(int x, int y, int z);
'''

new = '''    @Override public @NotNull BlockState getBlockState(BlockPos pos) {
        int sectionIndex = Coords.blockToIndex(pos);
        LevelChunkSection section = this.sections[sectionIndex];
        if (section.hasOnlyAir()) {
            return Blocks.AIR.defaultBlockState();
        }
        return section.getBlockState(pos.getX() & SectionPos.SECTION_MASK, pos.getY() & SectionPos.SECTION_MASK,
                pos.getZ() & SectionPos.SECTION_MASK);
    }

    @Override public @NotNull FluidState getFluidState(BlockPos pos) {
        return this.getFluidState(pos.getX(), pos.getY(), pos.getZ());
    }

    public FluidState getFluidState(int x, int y, int z) {
        LevelChunkSection section = this.sections[Coords.blockToIndex(x, y, z)];
        if (section.hasOnlyAir()) {
            return Fluids.EMPTY.defaultFluidState();
        }
        return section.getFluidState(x & SectionPos.SECTION_MASK, y & SectionPos.SECTION_MASK, z & SectionPos.SECTION_MASK);
    }
'''

if old in text:
    text = text.replace(old, new, 1)
elif "LevelChunkSection section = this.sections[Coords.blockToIndex(x, y, z)]" not in text:
    raise SystemExit("Unable to replace the transformed LevelCube state readers")

for marker in (
    '@TransformFromMethod(value = "getBlockState(',
    '@TransformFromMethod(value = "getFluidState(',
    'native @NotNull BlockState getBlockState',
    'native FluidState getFluidState',
):
    if marker in text:
        raise SystemExit(f"Obsolete transformed LevelCube reader remains: {marker}")
if text.count("import net.minecraft.world.level.block.Blocks;") != 1:
    raise SystemExit("Expected exactly one Blocks import")
if text.count("import net.minecraft.world.level.material.Fluids;") != 1:
    raise SystemExit("Expected exactly one Fluids import")

path.write_text(text, encoding="utf-8")

obsolete = Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/world/level/cube/MixinLevelCube.java")
if obsolete.exists():
    obsolete.unlink()

print("Implemented Minecraft 26.2 LevelCube block and fluid readers directly")
