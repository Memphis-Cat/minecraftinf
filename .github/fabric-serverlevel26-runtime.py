#!/usr/bin/env python3
"""Port ServerLevel mixin shadows to Minecraft 26.2 class ownership."""

from pathlib import Path

path = Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinServerLevel.java")
text = path.read_text(encoding="utf-8")
text = text.replace("    @Shadow public abstract long getOverworldClockTime();\n", "")
text = text.replace(
    "new DifficultyInstance(this.getDifficulty(), this.getOverworldClockTime(), inhabitedTime, moonBrightness)",
    "new DifficultyInstance(this.getDifficulty(), ((ServerLevel) (Object) this).getOverworldClockTime(), inhabitedTime, moonBrightness)",
)
if "@Shadow public abstract long getOverworldClockTime" in text:
    raise SystemExit("Obsolete ServerLevel-owned clock shadow remains")
if "((ServerLevel) (Object) this).getOverworldClockTime()" not in text:
    raise SystemExit("Minecraft 26.2 inherited clock access was not installed")
path.write_text(text, encoding="utf-8")
print("Migrated ServerLevel clock access to Minecraft 26.2 class ownership")
