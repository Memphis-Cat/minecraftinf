#!/usr/bin/env python3
"""Implement cube-aware ChunkMap loading without injecting into a DASM-native method."""

from pathlib import Path

path = Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinChunkMap.java")
text = path.read_text(encoding="utf-8")

invalid_shadow = '''    @Shadow private abstract CompletableFuture<ChunkAccess> scheduleChunkLoad(ChunkPos pos);\n\n'''
valid_shadow = '''    @Shadow private CompletableFuture<ChunkAccess> scheduleChunkLoad(ChunkPos pos) {\n        throw new AssertionError();\n    }\n\n'''
if invalid_shadow in text:
    text = text.replace(invalid_shadow, valid_shadow, 1)
elif valid_shadow not in text:
    anchor = '''    @Shadow abstract CompletableFuture<ChunkResult<List<ChunkAccess>>> getChunkRangeFuture(\n            ChunkHolder centerChunk, int range, IntFunction<ChunkStatus> distanceToStatus\n    );\n\n'''
    if anchor not in text:
        raise SystemExit("Unable to locate ChunkMap scheduleChunkLoad shadow insertion point")
    text = text.replace(anchor, anchor + valid_shadow, 1)

start = text.find("    // region [cc_scheduleChunkLoad dasm + mixin]")
end = text.find("    // endregion", start)
if start < 0 or end < 0:
    raise SystemExit("Unable to locate cc_scheduleChunkLoad region")
end += len("    // endregion")

replacement = '''    // region [cc_scheduleChunkLoad dasm + mixin]
    @AddTransformToSets(ChunkToCloSet.ChunkMap_redirects.class)
    @TransformFromMethod("scheduleChunkLoad(Lnet/minecraft/world/level/ChunkPos;)Ljava/util/concurrent/CompletableFuture;")
    private CompletableFuture<CloAccess> cc_scheduleChunkLoad(CloPos cloPos) {
        if (!cloPos.isCube()) {
            return (CompletableFuture<CloAccess>) (CompletableFuture<?>) this.scheduleChunkLoad(cloPos.chunkPos());
        }

        try {
            Optional<CloAccess> storedCube = this.cc_cubeStorage.load(this.level, cloPos.cubePos());
            if (storedCube.isPresent()) {
                return CompletableFuture.completedFuture(storedCube.get());
            }
        } catch (Exception exception) {
            CubicChunks.LOGGER.error("Failed to load cube {}", cloPos, exception);
        }

        return CompletableFuture.completedFuture(this.cc_createEmptyChunk(cloPos));
    }

    @AddMethodToSets(containers = ChunkToCubeSet.ChunkMap_redirects.class, method = "scheduleChunkLoad(Lnet/minecraft/world/level/ChunkPos;)Ljava/util/concurrent/CompletableFuture;")
    private CompletableFuture<CloAccess> cc_scheduleChunkLoad(CubePos cubePos) {
        return this.cc_scheduleChunkLoad(CloPos.cube(cubePos));
    }
    // endregion'''

text = text[:start] + replacement + text[end:]

# The concrete method delegates vanilla columns to vanilla scheduleChunkLoad and
# cube data to CubeStorage, so the old transformed PoiManager redirect is gone.
text = text.replace("import net.minecraft.world.entity.ai.village.poi.PoiManager;\n", "")
text = text.replace("    @Shadow @Final private PoiManager poiManager;\n", "")

for obsolete in (
    "cc_loadStoredCube",
    "cc_onScheduleChunkLoad_poiManagerPreFetch",
    '@Dynamic @Inject(method = "cc_scheduleChunkLoad',
    '@Dynamic @Redirect(method = "cc_scheduleChunkLoad',
    "private native CompletableFuture<CloAccess> cc_scheduleChunkLoad(CloPos",
    "@Shadow private abstract CompletableFuture<ChunkAccess> scheduleChunkLoad",
):
    if obsolete in text:
        raise SystemExit(f"Obsolete cc_scheduleChunkLoad implementation remains: {obsolete}")

path.write_text(text, encoding="utf-8")
print("Implemented concrete Minecraft 26.2 cube loading")
