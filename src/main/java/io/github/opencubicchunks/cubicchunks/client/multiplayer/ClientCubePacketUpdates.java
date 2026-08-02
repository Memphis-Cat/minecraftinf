package io.github.opencubicchunks.cubicchunks.client.multiplayer;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import net.minecraft.network.FriendlyByteBuf;

/** Applies packet updates to cubes already present in the client cube cache. */
public final class ClientCubePacketUpdates {
    private ClientCubePacketUpdates() {}

    public static Result replaceBiomes(ClientCubeCache.Storage storage, int x, int y, int z, FriendlyByteBuf buffer) {
        if (!storage.inRange(x, y, z)) {
            return Result.OUT_OF_RANGE;
        }

        LevelCube cube = storage.chunks.get(storage.getIndex(x, y, z));
        if (!isCubeAt(cube, x, y, z)) {
            return Result.MISSING;
        }

        cube.replaceBiomes(buffer);
        return Result.UPDATED;
    }

    private static boolean isCubeAt(LevelCube cube, int x, int y, int z) {
        if (cube == null) {
            return false;
        }
        CubePos cubePos = cube.cc_getCubePos();
        return cubePos.getX() == x && cubePos.getY() == y && cubePos.getZ() == z;
    }

    public enum Result {
        UPDATED, OUT_OF_RANGE, MISSING
    }
}
