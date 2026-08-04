#!/usr/bin/env python3
"""Port Level#setBlock cube routing to Minecraft 26.2's inlined notifications."""

from pathlib import Path

path = Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/world/level/MixinLevel.java")
text = path.read_text(encoding="utf-8")

text = text.replace("import com.llamalad7.mixinextras.injector.v2.WrapWithCondition;\n", "")
text = text.replace("import io.github.notstirred.dasm.api.annotations.redirect.redirects.AddTransformToSets;\n", "")
text = text.replace("import net.minecraft.core.Direction;\n", "import net.minecraft.core.Direction;\nimport net.minecraft.server.level.FullChunkStatus;\n")
text = text.replace(
    "    // Uses LevelChunk to call setBlockState and markAndNotifyBlock, so we replace it with a LevelCube and call the Cubic variants of those functions.\n",
    "    // Routes LevelChunk-specific block mutation accesses through LevelCube in cubic dimensions.\n",
)

start_marker = "    @WrapWithCondition(method = \"setBlock(Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;II)Z\""
end_marker = "    // getBlockState\n"
if start_marker in text:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    replacement = '''    // Minecraft 26.2 inlines the old block-notification helper into setBlock.
    // The remaining LevelChunk-specific access after setBlockState is the
    // full-status gate used for server block update packets.
    @WrapOperation(method = "setBlock(Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;II)Z", at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/chunk/LevelChunk;getFullStatus()Lnet/minecraft/server/level/FullChunkStatus;"))
    private FullChunkStatus cc_replaceLevelChunkInGetFullStatus(
            LevelChunk levelChunk, Operation<FullChunkStatus> original, @Share("levelCube") LocalRef<LevelCube> levelCubeLocalRef
    ) {
        if (cc_isCubic) {
            return levelCubeLocalRef.get().getFullStatus();
        }
        return original.call(levelChunk);
    }

'''
    text = text[:start] + replacement + text[end:]
elif "cc_replaceLevelChunkInGetFullStatus" not in text:
    raise SystemExit("Unable to locate the obsolete Level block-notification mixin")

for forbidden in ("WrapWithCondition", "AddTransformToSets", "cc_markAndNotifyBlock"):
    if forbidden in text:
        raise SystemExit(f"Obsolete Minecraft Level API remains after migration: {forbidden}")

required = (
    "cc_replaceLevelChunkInGetFullStatus",
    "levelCubeLocalRef.get().getFullStatus()",
    "LevelChunk;getFullStatus()Lnet/minecraft/server/level/FullChunkStatus;",
)
for marker in required:
    if marker not in text:
        raise SystemExit(f"Missing Minecraft 26.2 Level routing: {marker}")

path.write_text(text, encoding="utf-8")
print("Migrated Level#setBlock cube routing to Minecraft 26.2")
