package io.github.opencubicchunks.cubicchunks.mixin.dasmsets;

import javax.annotation.Nullable;

import io.github.notstirred.dasm.api.annotations.redirect.redirects.ConstructorToFactoryRedirect;
import io.github.notstirred.dasm.api.annotations.redirect.redirects.FieldRedirect;
import io.github.notstirred.dasm.api.annotations.redirect.redirects.FieldToMethodRedirect;
import io.github.notstirred.dasm.api.annotations.redirect.redirects.MethodRedirect;
import io.github.notstirred.dasm.api.annotations.redirect.redirects.TypeRedirect;
import io.github.notstirred.dasm.api.annotations.redirect.sets.IntraOwnerContainer;
import io.github.notstirred.dasm.api.annotations.redirect.sets.RedirectSet;
import io.github.notstirred.dasm.api.annotations.selector.Ref;
import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.exception.DasmFailedToApply;
import io.github.opencubicchunks.cubicchunks.server.level.CloTrackingView;
import io.github.opencubicchunks.cubicchunks.world.level.chunklike.CloAccess;
import io.github.opencubicchunks.cubicchunks.world.level.chunklike.ImposterProtoClo;
import io.github.opencubicchunks.cubicchunks.world.level.chunklike.LevelClo;
import io.github.opencubicchunks.cubicchunks.world.level.chunklike.ProtoClo;
import net.minecraft.core.Registry;
import net.minecraft.server.level.ChunkGenerationTask;
import net.minecraft.server.level.ChunkHolder;
import net.minecraft.server.level.ChunkMap;
import net.minecraft.server.level.ChunkTaskDispatcher;
import net.minecraft.server.level.ChunkTaskPriorityQueue;
import net.minecraft.server.level.ChunkTrackingView;
import net.minecraft.server.level.GenerationChunkHolder;
import net.minecraft.server.level.ServerChunkCache;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.level.SimulationChunkTracker;
import net.minecraft.server.level.progress.LoggerChunkProgressListener;
import net.minecraft.server.level.progress.ProcessorChunkProgressListener;
import net.minecraft.server.level.progress.StoringChunkProgressListener;
import net.minecraft.server.network.PlayerChunkSender;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelHeightAccessor;
import net.minecraft.world.level.TicketStorage;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.ImposterProtoChunk;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.chunk.LevelChunkSection;
import net.minecraft.world.level.chunk.ProtoChunk;
import net.minecraft.world.level.chunk.UpgradeData;
import net.minecraft.world.level.chunk.status.ChunkStatus;
import net.minecraft.world.level.chunk.storage.ChunkStorage;
import net.minecraft.world.level.levelgen.blending.BlendingData;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.ticks.LevelChunkTicks;
import net.minecraft.world.ticks.ProtoChunkTicks;

/**
 * Redirects transforms that operate on the common chunk-or-cube abstraction.
 */
@RedirectSet
public interface ChunkToCloSet extends GlobalSet {
    @TypeRedirect(from = @Ref(ChunkPos.class), to = @Ref(CloPos.class))
    abstract class ChunkPos_to_CloPos_redirects {
        @FieldRedirect("INVALID_CHUNK_POS:J")
        static final long INVALID_CLO_POS = Long.MAX_VALUE;

        @FieldToMethodRedirect("x:I")
        native int getX();

        @FieldToMethodRedirect("z:I")
        native int getZ();

        @MethodRedirect("toLong()J")
        native long toLong();

        @ConstructorToFactoryRedirect("<init>(J)V")
        static native CloPos fromLong(long cloPos);

        @ConstructorToFactoryRedirect("<init>(II)V")
        static native CloPos chunk(int x, int z);

        @MethodRedirect("asLong(II)J")
        static native long chunkAsLong(int x, int z);
    }

    @TypeRedirect(from = @Ref(ChunkAccess.class), to = @Ref(CloAccess.class))
    interface ChunkAccess_to_CloAccess_redirects {
        @MethodRedirect("getPos()Lnet/minecraft/world/level/ChunkPos;")
        CloPos cc_getCloPos();

        @MethodRedirect("getPersistedStatus()Lnet/minecraft/world/level/chunk/status/ChunkStatus;")
        ChunkStatus getPersistedStatus();
    }

    @TypeRedirect(from = @Ref(LevelChunk.class), to = @Ref(LevelClo.class))
    interface LevelChunk_to_LevelClo_redirects extends ChunkAccess_to_CloAccess_redirects {
        @ConstructorToFactoryRedirect("<init>(Lnet/minecraft/world/level/Level;Lnet/minecraft/world/level/ChunkPos;)V")
        static LevelClo create(Level level, ChunkPos pos) {
            throw new DasmFailedToApply();
        }

        @ConstructorToFactoryRedirect("<init>(Lnet/minecraft/world/level/Level;Lnet/minecraft/world/level/ChunkPos;Lnet/minecraft/world/level/chunk/UpgradeData;"
                + "Lnet/minecraft/world/ticks/LevelChunkTicks;Lnet/minecraft/world/ticks/LevelChunkTicks;"
                + "J[Lnet/minecraft/world/level/chunk/LevelChunkSection;Lnet/minecraft/world/level/chunk/LevelChunk$PostLoadProcessor;"
                + "Lnet/minecraft/world/level/levelgen/blending/BlendingData;)V")
        static LevelClo create(
                Level level, CloPos pos, UpgradeData data, LevelChunkTicks<Block> blockTicks, LevelChunkTicks<Fluid> fluidTicks, long inhabitedTime,
                @Nullable LevelChunkSection[] sections, @Nullable LevelClo.PostLoadProcessor postLoad, @Nullable BlendingData blendingData
        ) {
            throw new DasmFailedToApply();
        }

        @ConstructorToFactoryRedirect("<init>(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/level/chunk/ProtoChunk;"
                + "Lnet/minecraft/world/level/chunk/LevelChunk$PostLoadProcessor;)V")
        static LevelClo create(ServerLevel level, ProtoClo clo, @Nullable LevelClo.PostLoadProcessor postLoad) {
            throw new DasmFailedToApply();
        }
    }

    @TypeRedirect(from = @Ref(LevelChunk.PostLoadProcessor.class), to = @Ref(LevelClo.PostLoadProcessor.class))
    interface LevelChunk$PostLoadProcessor_to_LevelClo$PostLoadProcessor_redirects {}

    @TypeRedirect(from = @Ref(ProtoChunk.class), to = @Ref(ProtoClo.class))
    interface ProtoChunk_to_ProtoClo_redirects extends ChunkAccess_to_CloAccess_redirects {
        @ConstructorToFactoryRedirect("<init>(Lnet/minecraft/world/level/ChunkPos;Lnet/minecraft/world/level/chunk/UpgradeData;"
                + "Lnet/minecraft/world/level/LevelHeightAccessor;Lnet/minecraft/core/Registry;"
                + "Lnet/minecraft/world/level/levelgen/blending/BlendingData;)V")
        static ProtoClo create(
                CloPos cloPos, UpgradeData upgradeData, LevelHeightAccessor levelHeightAccessor, Registry<Biome> biomeRegistry,
                @Nullable BlendingData blendingData
        ) {
            throw new DasmFailedToApply();
        }

        @ConstructorToFactoryRedirect("<init>(Lnet/minecraft/world/level/ChunkPos;Lnet/minecraft/world/level/chunk/UpgradeData;"
                + "[Lnet/minecraft/world/level/chunk/LevelChunkSection;Lnet/minecraft/world/ticks/ProtoChunkTicks;"
                + "Lnet/minecraft/world/ticks/ProtoChunkTicks;Lnet/minecraft/world/level/LevelHeightAccessor;Lnet/minecraft/core/Registry;"
                + "Lnet/minecraft/world/level/levelgen/blending/BlendingData;)V")
        static ProtoClo create(
                CloPos cloPos, UpgradeData upgradeData, @Nullable LevelChunkSection[] sections, ProtoChunkTicks<Block> blockTicks,
                ProtoChunkTicks<Fluid> liquidTicks, LevelHeightAccessor levelHeightAccessor, Registry<Biome> biomeRegistry,
                @Nullable BlendingData blendingData
        ) {
            throw new DasmFailedToApply();
        }
    }

    @TypeRedirect(from = @Ref(ImposterProtoChunk.class), to = @Ref(ImposterProtoClo.class))
    interface ImposterProtoChunk_to_ImposterProtoClo_redirects {
        @ConstructorToFactoryRedirect("<init>(Lnet/minecraft/world/level/chunk/LevelChunk;Z)V")
        static ImposterProtoClo create(LevelClo wrapped, boolean allowWrites) {
            throw new DasmFailedToApply();
        }

        @MethodRedirect("getWrapped()Lnet/minecraft/world/level/chunk/LevelChunk;")
        LevelClo cc_getWrappedClo();
    }

    @TypeRedirect(from = @Ref(ChunkTrackingView.class), to = @Ref(CloTrackingView.class))
    interface ChunkTrackingView_to_CloTrackingView_redirects {}

    @TypeRedirect(from = @Ref(ChunkTrackingView.Positioned.class), to = @Ref(CloTrackingView.Positioned.class))
    abstract class ChunkTrackingView$Positioned_to_CloTrackingView$Positioned_redirects implements ChunkTrackingView_to_CloTrackingView_redirects {}

    @IntraOwnerContainer(@Ref(ChunkHolder.class))
    class ChunkHolder_redirects extends GenerationChunkHolder_redirects {}

    @IntraOwnerContainer(@Ref(ProcessorChunkProgressListener.class))
    class ProcessorChunkProgressListener_redirects {}

    @IntraOwnerContainer(@Ref(ChunkGenerationTask.class))
    class ChunkGenerationTask_redirects {}

    @IntraOwnerContainer(@Ref(GenerationChunkHolder.class))
    class GenerationChunkHolder_redirects {}

    @IntraOwnerContainer(@Ref(ChunkStorage.class))
    class ChunkStorage_redirects {}

    @IntraOwnerContainer(@Ref(ChunkMap.class))
    class ChunkMap_redirects extends ChunkStorage_redirects {}

    @IntraOwnerContainer(@Ref(ChunkMap.TrackedEntity.class))
    class ChunkMap$TrackedEntity_redirects {}

    @IntraOwnerContainer(@Ref(ServerChunkCache.class))
    class ServerChunkCache_redirects {}

    @IntraOwnerContainer(@Ref(ServerLevel.class))
    class ServerLevel_redirects {}

    @IntraOwnerContainer(@Ref(Entity.class))
    class Entity_redirects {}

    @IntraOwnerContainer(@Ref(ServerPlayer.class))
    class ServerPlayer_redirects extends Entity_redirects {}

    @IntraOwnerContainer(@Ref(PlayerChunkSender.class))
    class PlayerChunkSender_redirects {}

    @IntraOwnerContainer(@Ref(ChunkTaskDispatcher.class))
    class ChunkTaskDispatcher_redirects {}

    @IntraOwnerContainer(@Ref(ChunkTaskPriorityQueue.class))
    class ChunkTaskPriorityQueue_redirects {}

    @IntraOwnerContainer(@Ref(SimulationChunkTracker.class))
    class SimulationChunkTracker_redirects {}

    @IntraOwnerContainer(@Ref(LoggerChunkProgressListener.class))
    class LoggerChunkProgressListener_redirects {}

    @IntraOwnerContainer(@Ref(StoringChunkProgressListener.class))
    class StoringChunkProgressListener_redirects {}

    @IntraOwnerContainer(@Ref(TicketStorage.class))
    class TicketStorage_redirects {}
}
