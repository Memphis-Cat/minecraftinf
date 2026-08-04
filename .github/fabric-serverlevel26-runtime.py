#!/usr/bin/env python3
"""Port ServerLevel mixin shadows to Minecraft 26.2 class ownership."""

from pathlib import Path

path = Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinServerLevel.java")
text = path.read_text(encoding="utf-8")

# The general API finalizer is intentionally run twice as an idempotency check.
# It previously reinserted this three-line shadow block after this script removed
# the inherited clock method, duplicating the two valid shadows. Keep exactly one
# declaration of each valid ServerLevel member and no shadow for Level-owned time.
def keep_one(source: str, declaration: str) -> str:
    first = source.find(declaration)
    if first < 0:
        return source
    prefix_end = first + len(declaration)
    return source[:prefix_end] + source[prefix_end:].replace(declaration, "")

text = keep_one(text, "    @Shadow @Final protected RandomSource random;\n")
text = keep_one(text, "    @Shadow public abstract float getMoonBrightness(BlockPos pos);\n")
text = text.replace("    @Shadow public abstract long getOverworldClockTime();\n", "")
text = text.replace(
    "new DifficultyInstance(this.getDifficulty(), this.getOverworldClockTime(), inhabitedTime, moonBrightness)",
    "new DifficultyInstance(this.getDifficulty(), ((ServerLevel) (Object) this).getOverworldClockTime(), inhabitedTime, moonBrightness)",
)

if text.count("@Shadow @Final protected RandomSource random;") != 1:
    raise SystemExit("Expected exactly one ServerLevel random shadow")
if text.count("@Shadow public abstract float getMoonBrightness(BlockPos pos);") != 1:
    raise SystemExit("Expected exactly one positional moon-brightness shadow")
if "@Shadow public abstract long getOverworldClockTime" in text:
    raise SystemExit("Obsolete ServerLevel-owned clock shadow remains")
if "((ServerLevel) (Object) this).getOverworldClockTime()" not in text:
    raise SystemExit("Minecraft 26.2 inherited clock access was not installed")

path.write_text(text, encoding="utf-8")
print("Migrated and deduplicated ServerLevel members for Minecraft 26.2")
