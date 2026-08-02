package io.github.opencubicchunks.cubicchunks.server.level;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cubicchunks.world.entity.EntityCubePosGetter;
import net.minecraft.server.level.ServerPlayer;

/** Shared cubic entity-tracking decisions. */
public final class EntityTracking {
    private EntityTracking() {}

    public static boolean isTracked(CubicChunkMap chunkMap, ServerPlayer player, EntityCubePosGetter entity) {
        CubePos cubePos = entity.cc_cubePosition();
        return chunkMap.cc_isChunkTracked(player, cubePos.getX(), cubePos.getY(), cubePos.getZ());
    }
}
