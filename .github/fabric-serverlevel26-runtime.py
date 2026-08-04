#!/usr/bin/env python3
"""Port ServerLevel mixin members to Minecraft 26.2 class ownership."""

from pathlib import Path

path = Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinServerLevel.java")
text = path.read_text(encoding="utf-8")

# The API finalizer runs twice. It still inserts the former ServerLevel shadow
# block, so normalize it after every pass. In 26.2 random and overworld clock are
# inherited from Level; only positional moon brightness is declared by ServerLevel.
def keep_one(source: str, declaration: str) -> str:
    first = source.find(declaration)
    if first < 0:
        return source
    prefix_end = first + len(declaration)
    return source[:prefix_end] + source[prefix_end:].replace(declaration, "")

text = text.replace("    @Shadow @Final protected RandomSource random;\n", "")
text = keep_one(text, "    @Shadow public abstract float getMoonBrightness(BlockPos pos);\n")
text = text.replace("    @Shadow public abstract long getOverworldClockTime();\n", "")
text = text.replace("blockState.randomTick(serverLevel, blockPos, this.random);", "blockState.randomTick(serverLevel, blockPos, serverLevel.getRandom());")
text = text.replace("fluidState.randomTick(serverLevel, blockPos, this.random);", "fluidState.randomTick(serverLevel, blockPos, serverLevel.getRandom());")
text = text.replace(
    "new DifficultyInstance(this.getDifficulty(), this.getOverworldClockTime(), inhabitedTime, moonBrightness)",
    "new DifficultyInstance(this.getDifficulty(), ((ServerLevel) (Object) this).getOverworldClockTime(), inhabitedTime, moonBrightness)",
)

# Keep the now-unused RandomSource import. The legacy finalizer still checks that
# import before trying to insert the old shadow block, and retaining it makes the
# deliberately repeated migration pass stable without affecting compiled code.
if "import net.minecraft.util.RandomSource;\n" not in text:
    anchor = "import net.minecraft.util.profiling.Profiler;\n"
    if anchor not in text:
        raise SystemExit("Unable to retain the RandomSource finalizer sentinel")
    text = text.replace(anchor, "import net.minecraft.util.RandomSource;\n" + anchor, 1)

if "@Shadow @Final protected RandomSource random" in text:
    raise SystemExit("Obsolete ServerLevel-owned random shadow remains")
if text.count("@Shadow public abstract float getMoonBrightness(BlockPos pos);") != 1:
    raise SystemExit("Expected exactly one positional moon-brightness shadow")
if "@Shadow public abstract long getOverworldClockTime" in text:
    raise SystemExit("Obsolete ServerLevel-owned clock shadow remains")
if "serverLevel.getRandom()" not in text:
    raise SystemExit("Minecraft 26.2 inherited random access was not installed")
if "((ServerLevel) (Object) this).getOverworldClockTime()" not in text:
    raise SystemExit("Minecraft 26.2 inherited clock access was not installed")

path.write_text(text, encoding="utf-8")
print("Migrated ServerLevel members to Minecraft 26.2 ownership")
