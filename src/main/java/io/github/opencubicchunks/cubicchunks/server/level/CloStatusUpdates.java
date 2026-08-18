package io.github.opencubicchunks.cubicchunks.server.level;

import java.util.Objects;

import io.github.opencubicchunks.cc_core.api.CubicConstants;
import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.world.level.entity.CloStatusUpdateListener;
import net.minecraft.server.level.FullChunkStatus;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.entity.ChunkStatusUpdateListener;

/** Bridges three-dimensional cube status changes to vanilla column status listeners. */
public final class CloStatusUpdates {
    private CloStatusUpdates() {}

    public static CloStatusUpdateListener adapt(ChunkStatusUpdateListener listener) {
        Objects.requireNonNull(listener, "listener");
        return (cloPos, status) -> notify(listener, cloPos, status);
    }

    static void notify(ChunkStatusUpdateListener listener, CloPos cloPos, FullChunkStatus status) {
        if (cloPos.isChunk()) {
            listener.onChunkStatusChange(new ChunkPos(cloPos.getX(), cloPos.getZ()), status);
            return;
        }

        for (int localX = 0; localX < CubicConstants.DIAMETER_IN_SECTIONS; ++localX) {
            for (int localZ = 0; localZ < CubicConstants.DIAMETER_IN_SECTIONS; ++localZ) {
                int chunkX = Coords.cubeToSection(cloPos.getX(), localX);
                int chunkZ = Coords.cubeToSection(cloPos.getZ(), localZ);
                listener.onChunkStatusChange(new ChunkPos(chunkX, chunkZ), status);
            }
        }
    }
}
