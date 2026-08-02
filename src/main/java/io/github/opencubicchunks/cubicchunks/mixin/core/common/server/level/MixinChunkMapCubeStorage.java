package io.github.opencubicchunks.cubicchunks.mixin.core.common.server.level;

import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.function.Supplier;

import com.mojang.datafixers.DataFixer;
import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.CanBeCubic;
import io.github.opencubicchunks.cubicchunks.CubicChunks;
import io.github.opencubicchunks.cubicchunks.world.level.chunklike.CloAccess;
import io.github.opencubicchunks.cubicchunks.world.level.chunklike.ImposterProtoClo;
import io.github.opencubicchunks.cubicchunks.world.level.cube.ImposterProtoCube;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import io.github.opencubicchunks.cubicchunks.world.storage.CubeStorage;
import net.minecraft.server.level.ChunkMap;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.progress.ChunkProgressListener;
import net.minecraft.util.thread.BlockableEventLoop;
import net.minecraft.world.level.TicketStorage;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.chunk.LightChunkGetter;
import net.minecraft.world.level.entity.ChunkStatusUpdateListener;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplateManager;
import net.minecraft.world.level.storage.LevelStorageSource;
import org.jetbrains.annotations.Nullable;
import org.spongepowered.asm.mixin.Dynamic;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Adds the Phase 1 full-cube section persistence path to {@link ChunkMap}. */
@Mixin(value = ChunkMap.class, priority = 900)
public abstract class MixinChunkMapCubeStorage {
    @Shadow @Final private ServerLevel level;

    @Unique
    private CubeStorage cc_cubeStorage;

    @Inject(method = "<init>", at = @At("RETURN"))
    private void cc_initializeCubeStorage(
            ServerLevel level, LevelStorageSource.LevelStorageAccess levelStorageAccess, DataFixer fixerUpper,
            StructureTemplateManager structureManager, Executor dispatcher, BlockableEventLoop mainThreadExecutor, LightChunkGetter lightChunk,
            ChunkGenerator generator, ChunkProgressListener progressListener, ChunkStatusUpdateListener chunkStatusListener,
            Supplier overworldDataStorage, TicketStorage ticketStorage, int serverViewDistance, boolean sync, CallbackInfo ci
    ) {
        if (((CanBeCubic) level).cc_isCubic()) {
            cc_cubeStorage = new CubeStorage(levelStorageAccess.getDimensionPath(level.dimension()).resolve("cubicchunks").resolve("cubes"));
        }
    }

    @Dynamic @Inject(method = "cc_save", at = @At("HEAD"), cancellable = true, require = 0)
    private void cc_saveCube(CloAccess cloAccess, CallbackInfoReturnable<Boolean> cir) {
        LevelCube cube = cc_asLevelCube(cloAccess);
        if (cube == null) {
            return;
        }

        try {
            cc_cubeStorage.save(cube);
            cube.tryMarkSaved();
            cir.setReturnValue(true);
        } catch (Exception exception) {
            CubicChunks.LOGGER.error("Failed to save cube {}", cube.cc_getCubePos(), exception);
            cir.setReturnValue(false);
        }
    }

    @Dynamic @Inject(method = "cc_scheduleChunkLoad(Lio/github/opencubicchunks/cc_core/world/level/CloPos;)Ljava/util/concurrent/CompletableFuture;", at = @At("HEAD"), cancellable = true, require = 0)
    private void cc_loadCube(CloPos cloPos, CallbackInfoReturnable<CompletableFuture<CloAccess>> cir) {
        if (!cloPos.isCube()) {
            return;
        }

        try {
            Optional<ImposterProtoCube> storedCube = cc_cubeStorage.load(level, cloPos.cubePos());
            storedCube.ifPresent(cube -> cir.setReturnValue(CompletableFuture.completedFuture(cube)));
        } catch (Exception exception) {
            CubicChunks.LOGGER.error("Failed to load cube {}", cloPos, exception);
        }
    }

    @Unique
    private static @Nullable LevelCube cc_asLevelCube(CloAccess cloAccess) {
        if (cloAccess instanceof LevelCube levelCube) {
            return levelCube;
        }
        if (cloAccess instanceof ImposterProtoClo imposter && imposter.cc_getWrappedClo() instanceof LevelCube levelCube) {
            return levelCube;
        }
        return null;
    }
}
