package io.github.opencubicchunks.cubicchunks.mixin.core.common.server.level;

import java.util.List;
import java.util.concurrent.Executor;
import java.util.function.LongPredicate;

import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import io.github.notstirred.dasm.api.annotations.Dasm;
import io.github.notstirred.dasm.api.annotations.redirect.redirects.AddMethodToSets;
import io.github.notstirred.dasm.api.annotations.redirect.redirects.AddTransformToSets;
import io.github.notstirred.dasm.api.annotations.selector.Ref;
import io.github.notstirred.dasm.api.annotations.transform.TransformFromMethod;
import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.api.CubicConstants;
import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.mixin.core.common.world.level.MixinLevel;
import io.github.opencubicchunks.cubicchunks.mixin.dasmsets.ChunkToCloSet;
import io.github.opencubicchunks.cubicchunks.mixin.dasmsets.ChunkToCubeSet;
import io.github.opencubicchunks.cubicchunks.server.level.CubicServerLevel;
import io.github.opencubicchunks.cubicchunks.server.level.ServerCubeCache;
import io.github.opencubicchunks.cubicchunks.world.level.CubicLevelTicks;
import io.github.opencubicchunks.cubicchunks.world.level.chunklike.LevelClo;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import net.minecraft.core.BlockPos;
import net.minecraft.core.SectionPos;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerChunkCache;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.TicketType;
import net.minecraft.server.level.progress.ChunkProgressListener;
import net.minecraft.util.profiling.Profiler;
import net.minecraft.util.profiling.ProfilerFiller;
import net.minecraft.world.RandomSequences;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.chunk.LevelChunkSection;
import net.minecraft.world.level.dimension.LevelStem;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.storage.LevelStorageSource;
import net.minecraft.world.level.storage.ServerLevelData;
import net.minecraft.world.ticks.LevelTicks;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Dasm(value = ChunkToCloSet.class, target = @Ref(ServerLevel.class))
@Mixin(ServerLevel.class)
public abstract class MixinServerLevel extends MixinLevel implements CubicServerLevel {
    @Shadow @Final private ServerChunkCache chunkSource;

    @Inject(method = "<init>", at = @At("CTOR_HEAD"))
    private void cc_onInit(
            MinecraftServer server, Executor dispatcher, LevelStorageSource.LevelStorageAccess levelStorageAccess, ServerLevelData serverLevelData,
            ResourceKey dimension, LevelStem levelStem, ChunkProgressListener progressListener, boolean isDebug, long biomeZoomSeed,
            List customSpawners, boolean tickTime, RandomSequences randomSequences, CallbackInfo ci
    ) {
        // TODO conditionally mark as cubic based on dimension, config, level data, etc
    }

    @Redirect(method = "<init>", at = @At(value = "NEW", target = "net/minecraft/world/ticks/LevelTicks"))
    private <T> LevelTicks<T> cc_createLevelTicks(LongPredicate vanillaTickCheck) {
        if (!this.cc_isCubic) {
            return new LevelTicks<>(vanillaTickCheck);
        }
        return new CubicLevelTicks<>(packedCube -> this.chunkSource.isPositionTicking(packedCube));
    }

    @Override public ServerCubeCache cc_getCubeSource() {
        return ((ServerCubeCache) this.chunkSource);
    }

    @AddTransformToSets(ChunkToCloSet.ServerLevel_redirects.class)
    @TransformFromMethod("startTickingChunk(Lnet/minecraft/world/level/chunk/LevelChunk;)V")
    public native void cc_startTickingClo(LevelClo chunk);

    @AddTransformToSets(ChunkToCloSet.ServerLevel_redirects.class)
    @TransformFromMethod("unload(Lnet/minecraft/world/level/chunk/LevelChunk;)V")
    public native void cc_unloadClo(LevelClo clo);

    @WrapOperation(method = "setDefaultSpawnPos", at = @At(value = "INVOKE", target = "Lnet/minecraft/server/level/ServerChunkCache;removeTicketWithRadius(Lnet/minecraft/server/level/TicketType;"
            + "Lnet/minecraft/world/level/ChunkPos;I)V"))
    private void cc_onSetDefaultSpawnPos_removeTicketWithRadius(
            ServerChunkCache instance, TicketType ticket, ChunkPos chunkPos, int radius, Operation<Void> original, BlockPos pos
    ) {
        if (cc_isCubic) {
            ((ServerCubeCache) instance).cc_removeTicketWithRadius(ticket, CloPos.cube(pos), radius);
        } else {
            original.call(instance, ticket, chunkPos, radius);
        }
    }

    @WrapOperation(method = "setDefaultSpawnPos", at = @At(value = "INVOKE", target = "Lnet/minecraft/server/level/ServerChunkCache;addTicketWithRadius(Lnet/minecraft/server/level/TicketType;"
            + "Lnet/minecraft/world/level/ChunkPos;I)V"))
    private void cc_onSetDefaultSpawnPos_addicketWithRadius(
            ServerChunkCache instance, TicketType ticket, ChunkPos chunkPos, int radius, Operation<Void> original, BlockPos pos
    ) {
        if (cc_isCubic) {
            ((ServerCubeCache) instance).cc_addTicketWithRadius(ticket, CloPos.cube(pos), radius);
        } else {
            original.call(instance, ticket, chunkPos, radius);
        }
    }

    @AddMethodToSets(containers = ChunkToCloSet.ServerLevel_redirects.class, method = "tickChunk(Lnet/minecraft/world/level/chunk/LevelChunk;I)V")
    public void cc_tickClo(LevelClo levelClo, int randomTickSpeed) {
        if (levelClo instanceof LevelCube levelCube) {
            cc_tickCube(levelCube, randomTickSpeed);
        } else {
            // Columns remain authoritative for precipitation and weather. Cubes own random block/fluid ticks.
            ((ServerLevel) (Object) this).tickChunk((LevelChunk) levelClo, 0);
        }
    }

    @AddMethodToSets(containers = ChunkToCubeSet.ServerLevel_redirects.class, method = "tickChunk(Lnet/minecraft/world/level/chunk/LevelChunk;I)V")
    public void cc_tickCube(LevelCube levelCube, int randomTickSpeed) {
        if (randomTickSpeed <= 0) {
            return;
        }

        ServerLevel serverLevel = (ServerLevel) (Object) this;
        CubePos cubePos = levelCube.cc_getCubePos();
        LevelChunkSection[] sections = levelCube.getSections();
        ProfilerFiller profiler = Profiler.get();
        profiler.push("tickBlocks");
        try {
            for (int localSectionY = 0; localSectionY < CubicConstants.DIAMETER_IN_SECTIONS; localSectionY++) {
                for (int localSectionZ = 0; localSectionZ < CubicConstants.DIAMETER_IN_SECTIONS; localSectionZ++) {
                    for (int localSectionX = 0; localSectionX < CubicConstants.DIAMETER_IN_SECTIONS; localSectionX++) {
                        int sectionIndex = Coords.sectionToIndex(localSectionX, localSectionY, localSectionZ);
                        LevelChunkSection section = sections[sectionIndex];
                        if (!section.isRandomlyTicking()) {
                            continue;
                        }

                        int minBlockX = SectionPos.sectionToBlockCoord(Coords.cubeToSection(cubePos.getX(), localSectionX));
                        int minBlockY = SectionPos.sectionToBlockCoord(Coords.cubeToSection(cubePos.getY(), localSectionY));
                        int minBlockZ = SectionPos.sectionToBlockCoord(Coords.cubeToSection(cubePos.getZ(), localSectionZ));
                        for (int tickIndex = 0; tickIndex < randomTickSpeed; tickIndex++) {
                            BlockPos blockPos = serverLevel.getBlockRandomPos(minBlockX, minBlockY, minBlockZ, SectionPos.SECTION_MASK);
                            profiler.push("randomTick");
                            try {
                                BlockState blockState = section.getBlockState(blockPos.getX() - minBlockX, blockPos.getY() - minBlockY,
                                        blockPos.getZ() - minBlockZ);
                                if (blockState.isRandomlyTicking()) {
                                    blockState.randomTick(serverLevel, blockPos, serverLevel.random);
                                }

                                FluidState fluidState = blockState.getFluidState();
                                if (fluidState.isRandomlyTicking()) {
                                    fluidState.randomTick(serverLevel, blockPos, serverLevel.random);
                                }
                            } finally {
                                profiler.pop();
                            }
                        }
                    }
                }
            }
        } finally {
            profiler.pop();
        }
    }

    // TODO (P2) waitForChunkAndEntities

    // TODO: comments below don't account for 1.20.4->1.21.5 changes; will need to check for other methods that need CC changes

    // TODO: phase 3 - isNaturalSpawningAllowed

    // TODO: phase 3 - invalidateCapabilites, neoforge api

    // TODO: phase 4 - setCubeForced - new function

    // TODO: saveDebugReport - mixins, debug only, low priority, if we really really really really need it

    // TODO: phase 2 - isPositionEntityTicking - mixin

}
