#!/usr/bin/env python3
"""Port remaining Minecraft 26.2 startup-sensitive mixin hooks."""
from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding='utf-8')


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding='utf-8')

# MinecraftServer.setInitialSpawn now uses ChunkPos.containing(BlockPos) and has a LevelLoadListener argument.
path = 'src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/MixinMinecraftServer.java'
text = read(path)
if 'import net.minecraft.server.level.progress.LevelLoadListener;\n' not in text:
    text = text.replace('import net.minecraft.server.level.ServerLevel;\n', 'import net.minecraft.server.level.ServerLevel;\nimport net.minecraft.server.level.progress.LevelLoadListener;\n', 1)
old = '''    // setInitialSpawn
    // We replace the ChunkPos spawn position with a CubePos spawn position and reuse it later to get the world position.
    @Inject(method = "setInitialSpawn", at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/ChunkPos;<init>(Lnet/minecraft/core/BlockPos;)V"))
    private static void cc_replaceChunkPosInSetInitialSpawn(
            ServerLevel serverLevel, ServerLevelData serverLevelData, boolean generateBonusChest, boolean debug, CallbackInfo ci,
            @Share("cubePos") LocalRef<CubePos> cubePosLocalRef
    ) {
        if (((CanBeCubic) serverLevel).cc_isCubic()) {
            CubePos cubePos = new CubePos(serverLevel.getChunkSource().randomState().sampler().findSpawnPosition());
            cubePosLocalRef.set(cubePos);
        }
    }
'''
new = '''    // setInitialSpawn
    // Capture the full 3D spawn sample before vanilla projects it to a ChunkPos.
    @WrapOperation(method = "setInitialSpawn", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/world/level/ChunkPos;containing(Lnet/minecraft/core/BlockPos;)Lnet/minecraft/world/level/ChunkPos;"))
    private static ChunkPos cc_captureCubePosInSetInitialSpawn(
            BlockPos spawnPosition, Operation<ChunkPos> original, ServerLevel serverLevel, ServerLevelData serverLevelData,
            boolean generateBonusChest, boolean debug, LevelLoadListener levelLoadListener,
            @Share("cubePos") LocalRef<CubePos> cubePosLocalRef
    ) {
        if (((CanBeCubic) serverLevel).cc_isCubic()) {
            cubePosLocalRef.set(new CubePos(spawnPosition));
        }
        return original.call(spawnPosition);
    }
'''
if old in text:
    text = text.replace(old, new, 1)
elif 'cc_captureCubePosInSetInitialSpawn' not in text:
    raise SystemExit('Unable to migrate MinecraftServer initial-spawn capture')
write(path, text)

# Minecraft 26.2 replaced the static prepareLevels target formula with ChunkLoadCounter,
# which observes the actual newly activated holders. Cubes and their backing columns are
# therefore counted directly; the old Mth.square replacement must not remain.
path = 'src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/MixinMinecraftServer.java'
text = read(path)
method_name = 'cc_onPrepareLevels_computeTickingGeneratedCount'
name_index = text.find(method_name)
if name_index >= 0:
    method_start = text.rfind('    @WrapOperation', 0, name_index)
    body_start = text.find('{', name_index)
    if method_start < 0 or body_start < 0:
        raise SystemExit('Unable to locate obsolete prepareLevels hook boundaries')
    depth = 0
    method_end = -1
    for index in range(body_start, len(text)):
        if text[index] == '{':
            depth += 1
        elif text[index] == '}':
            depth -= 1
            if depth == 0:
                method_end = index + 1
                break
    if method_end < 0:
        raise SystemExit('Unable to locate obsolete prepareLevels hook end')
    while method_end < len(text) and text[method_end] == '\n':
        method_end += 1
    text = text[:method_start] + text[method_end:]
text = text.replace('import io.github.opencubicchunks.cc_core.api.CubicConstants;\n', '')
text = text.replace('import io.github.opencubicchunks.cc_core.utils.Coords;\n', '')
text = text.replace('import net.minecraft.world.level.GameRules;\n', '')
text = text.replace('    @Shadow public abstract ServerLevel overworld();\n\n', '')
text = text.replace('    @Shadow public abstract GameRules getGameRules();\n\n', '')
if 'cc_onPrepareLevels_computeTickingGeneratedCount' in text:
    raise SystemExit('Obsolete prepareLevels static-count hook remains')
write(path, text)

# Replace the fragile injection into a DASM-generated method with a concrete mixin helper.
path = 'src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinChunkMap.java'
text = read(path)
text = text.replace('import org.spongepowered.asm.mixin.Overwrite;\n', '')
shadow = '''    @Shadow abstract CompletableFuture<ChunkResult<List<ChunkAccess>>> getChunkRangeFuture(
            ChunkHolder centerChunk, int range, IntFunction<ChunkStatus> distanceToStatus
    );

'''
if shadow not in text:
    text = text.replace('    @Shadow public abstract ReportedException debugFuturesAndCreateReportedException(IllegalStateException exception, String details);\n\n',
                        '    @Shadow public abstract ReportedException debugFuturesAndCreateReportedException(IllegalStateException exception, String details);\n\n' + shadow, 1)
start = text.find('    // region [cc_getChunkRangeFuture dasm + mixin]')
end = text.find('    // endregion', start)
if start < 0 or end < 0:
    raise SystemExit('Unable to locate cc_getChunkRangeFuture region')
end += len('    // endregion')
body = '''    // region [cc_getChunkRangeFuture dasm + mixin]
    @AddTransformToSets(ChunkToCloSet.ChunkMap_redirects.class)
    @TransformFromMethod("getChunkRangeFuture(Lnet/minecraft/server/level/ChunkHolder;ILjava/util/function/IntFunction;)Ljava/util/concurrent/CompletableFuture;")
    private CompletableFuture<ChunkResult<List<CloAccess>>> cc_getChunkRangeFuture(
            ChunkHolder cloHolder, int radius, IntFunction<ChunkStatus> statusByRadius
    ) {
        CloPos pos = ((CloHolder) cloHolder).cc_getCloPos();
        if (!pos.isCube()) {
            return (CompletableFuture<ChunkResult<List<CloAccess>>>) (CompletableFuture<?>)
                    this.getChunkRangeFuture(cloHolder, radius, statusByRadius);
        }

        int cubeDiameter = radius * 2 + 1;
        int chunkDiameter = cubeDiameter * CubicConstants.DIAMETER_IN_SECTIONS;
        int futureCount = cubeDiameter * cubeDiameter * cubeDiameter + chunkDiameter * chunkDiameter;
        List<CompletableFuture<ChunkResult<CloAccess>>> futures = new ArrayList<>(futureCount);
        int middleCubeIndex = -1;
        for (int dz = -radius; dz <= radius; dz++) {
            for (int dx = -radius; dx <= radius; dx++) {
                int chunkDistance = Math.max(Math.abs(dz), Math.abs(dx));
                for (int sectionZ = 0; sectionZ < CubicConstants.DIAMETER_IN_SECTIONS; sectionZ++) {
                    for (int sectionX = 0; sectionX < CubicConstants.DIAMETER_IN_SECTIONS; sectionX++) {
                        ChunkHolder holder = this.getUpdatingChunkIfPresent(
                                CloPos.chunkAsLong(Coords.cubeToSection(pos.getX() + dx, sectionX),
                                        Coords.cubeToSection(pos.getZ() + dz, sectionZ)));
                        if (holder == null) {
                            return UNLOADED_CHUNK_LIST_FUTURE;
                        }
                        ChunkStatus expectedStatus = statusByRadius.apply(chunkDistance);
                        futures.add((CompletableFuture<ChunkResult<CloAccess>>) (CompletableFuture<?>)
                                holder.scheduleChunkGenerationTask(expectedStatus, (ChunkMap) (Object) this));
                    }
                }
                for (int dy = -radius; dy <= radius; dy++) {
                    if (dx == 0 && dy == 0 && dz == 0) {
                        middleCubeIndex = futures.size();
                    }
                    ChunkHolder holder = this.getUpdatingChunkIfPresent(
                            CloPos.cubeAsLong(pos.getX() + dx, pos.getY() + dy, pos.getZ() + dz));
                    if (holder == null) {
                        return UNLOADED_CHUNK_LIST_FUTURE;
                    }
                    ChunkStatus expectedStatus = statusByRadius.apply(Math.max(chunkDistance, Math.abs(dy)));
                    futures.add((CompletableFuture<ChunkResult<CloAccess>>) (CompletableFuture<?>)
                            holder.scheduleChunkGenerationTask(expectedStatus, (ChunkMap) (Object) this));
                }
            }
        }

        Collections.swap(futures, middleCubeIndex, futures.size() / 2);
        return Util.sequence(futures).thenApply(resultList -> {
            List<CloAccess> outputList = new ArrayList<>(resultList.size());
            for (ChunkResult<CloAccess> chunkResult : resultList) {
                if (chunkResult == null) {
                    throw this.debugFuturesAndCreateReportedException(
                            new IllegalStateException("At least one of the chunk futures were null"), "n/a");
                }
                CloAccess cloAccess = chunkResult.orElse(null);
                if (cloAccess == null) {
                    return UNLOADED_CHUNK_LIST_RESULT;
                }
                outputList.add(cloAccess);
            }
            return ChunkResult.of(outputList);
        });
    }
    // endregion'''
text = text[:start] + body + text[end:]
write(path, text)
print('Ported Minecraft 26.2 startup-sensitive mixin hooks')
