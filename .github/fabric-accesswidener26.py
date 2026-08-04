#!/usr/bin/env python3
"""Remove access-widener entries for classes deleted in Minecraft 26.2."""

from pathlib import Path

path = Path("src/main/resources/cubicchunks.accesswidener")
lines = path.read_text(encoding="utf-8").splitlines()
removed_targets = (
    "net/minecraft/client/renderer/SectionOcclusionGraph$GraphEvents",
)
filtered = [line for line in lines if not any(target in line for target in removed_targets)]
path.write_text("\n".join(filtered) + "\n", encoding="utf-8")
for target in removed_targets:
    if target in path.read_text(encoding="utf-8"):
        raise SystemExit(f"Obsolete access-widener target remains: {target}")
print("Removed Minecraft 26.2-deleted GraphEvents access-widener entries")
