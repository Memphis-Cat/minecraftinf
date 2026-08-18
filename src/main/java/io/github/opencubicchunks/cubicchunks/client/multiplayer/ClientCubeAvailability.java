package io.github.opencubicchunks.cubicchunks.client.multiplayer;

import net.minecraft.world.level.chunk.status.ChunkStatus;

/** Client-side loaded-cube availability checks. */
public final class ClientCubeAvailability {
    private ClientCubeAvailability() {}

    public static boolean hasCube(ClientCubeCache cubeCache, int cubeX, int cubeY, int cubeZ) {
        return cubeCache.cc_getCube(cubeX, cubeY, cubeZ, ChunkStatus.FULL, false) != null;
    }
}
