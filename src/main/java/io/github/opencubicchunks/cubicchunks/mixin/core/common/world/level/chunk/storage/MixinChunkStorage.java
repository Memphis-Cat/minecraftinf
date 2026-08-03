package io.github.opencubicchunks.cubicchunks.mixin.core.common.world.level.chunk.storage;

import java.util.Optional;
import java.util.concurrent.CompletableFuture;

import io.github.notstirred.dasm.api.annotations.Dasm;
import io.github.notstirred.dasm.api.annotations.redirect.redirects.AddMethodToSets;
import io.github.notstirred.dasm.api.annotations.selector.Ref;
import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.api.CubicConstants;
import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.mixin.dasmsets.ChunkToCloSet;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.chunk.storage.ChunkStorage;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;

@Dasm(value = ChunkToCloSet.class, target = @Ref(ChunkStorage.class))
@Mixin(ChunkStorage.class)
public abstract class MixinChunkStorage {
    @Shadow public abstract boolean isOldChunkAround(ChunkPos pos, int radius);

    @Shadow public abstract CompletableFuture<Optional<CompoundTag>> read(ChunkPos pos);

    @Shadow public abstract CompletableFuture<Void> write(ChunkPos pos, CompoundTag chunkData);

    @AddMethodToSets(containers = ChunkToCloSet.ChunkStorage_redirects.class, method = "isOldChunkAround(Lnet/minecraft/world/level/ChunkPos;I)Z")
    public boolean cc_isOldChunkAround(CloPos pos, int radius) {
        if (pos.isChunk()) {
            return this.isOldChunkAround(pos.chunkPos(), radius);
        }

        // Cubes are generated from their complete square of vanilla columns. A cube is
        // therefore considered near old terrain when any backing column is near old
        // terrain; checking every column is conservative and prevents blending seams.
        CubePos cubePos = pos.cubePos();
        for (int localX = 0; localX < CubicConstants.DIAMETER_IN_SECTIONS; localX++) {
            for (int localZ = 0; localZ < CubicConstants.DIAMETER_IN_SECTIONS; localZ++) {
                ChunkPos columnPos = new ChunkPos(
                        Coords.cubeToSection(cubePos.getX(), localX),
                        Coords.cubeToSection(cubePos.getZ(), localZ)
                );
                if (this.isOldChunkAround(columnPos, radius)) {
                    return true;
                }
            }
        }
        return false;
    }

    @AddMethodToSets(containers = ChunkToCloSet.ChunkStorage_redirects.class, method = "read(Lnet/minecraft/world/level/ChunkPos;)Ljava/util/concurrent/CompletableFuture;")
    public CompletableFuture<Optional<CompoundTag>> cc_read(CloPos cloPos) {
        if (cloPos.isChunk()) {
            return this.read(cloPos.chunkPos());
        }

        // MixinChunkMap checks CubeStorage before the transformed vanilla load path.
        // Reaching this method for a cube means CubeStorage had no persisted cube, so
        // Optional.empty is the correct signal to create and generate a new cube.
        return CompletableFuture.completedFuture(Optional.empty());
    }

    @AddMethodToSets(containers = ChunkToCloSet.ChunkStorage_redirects.class, method = "write(Lnet/minecraft/world/level/ChunkPos;Ljava/util/function/Supplier;)Ljava/util/concurrent/CompletableFuture;")
    public void cc_write(CloPos cloPos, CompoundTag chunkData) {
        if (cloPos.isChunk()) {
            this.write(cloPos.chunkPos(), chunkData);
            return;
        }

        // Cube saves are versioned and atomic in CubeStorage and are intercepted by
        // MixinChunkMap.cc_save. Silently writing cube NBT into a 2D region would lose
        // the Y coordinate, so reaching this bridge is a fatal programming error.
        throw new IllegalStateException("Cube write bypassed CubeStorage for " + cloPos);
    }

    // chunkScanner remains the vanilla column scanner. Cube existence and payloads are
    // queried through CubeStorage rather than projected into two-dimensional region keys.
}
