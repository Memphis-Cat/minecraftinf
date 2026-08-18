package io.github.opencubicchunks.cubicchunks.server.level;

import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cc_core.world.level.CloPos;
import net.minecraft.world.phys.Vec3;

/** Coordinate calculations shared by cubic {@code ChunkMap} paths. */
public final class CubeMapMath {
    private CubeMapMath() {}

    /** Returns the squared distance between a point and the center of a cube. */
    public static double euclideanDistanceSquared(CloPos cubePos, Vec3 point) {
        if (!cubePos.isCube()) {
            throw new IllegalArgumentException("Expected a cube position, got " + cubePos);
        }

        double cubeCenterX = Coords.cubeToCenterBlock(cubePos.getX());
        double cubeCenterY = Coords.cubeToCenterBlock(cubePos.getY());
        double cubeCenterZ = Coords.cubeToCenterBlock(cubePos.getZ());
        double dx = cubeCenterX - point.x();
        double dy = cubeCenterY - point.y();
        double dz = cubeCenterZ - point.z();
        return dx * dx + dy * dy + dz * dz;
    }
}
