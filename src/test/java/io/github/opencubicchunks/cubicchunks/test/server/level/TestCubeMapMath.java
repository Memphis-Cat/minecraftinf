package io.github.opencubicchunks.cubicchunks.test.server.level;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.server.level.CubeMapMath;
import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;

public class TestCubeMapMath {
    @Test
    public void usesIndependentCubeAxes() {
        CloPos cubePos = CloPos.cube(1, 2, 3);
        Vec3 center = new Vec3(Coords.cubeToCenterBlock(1), Coords.cubeToCenterBlock(2), Coords.cubeToCenterBlock(3));

        assertEquals(0.0D, CubeMapMath.euclideanDistanceSquared(cubePos, center));
        assertEquals(169.0D, CubeMapMath.euclideanDistanceSquared(cubePos, center.add(3.0D, -4.0D, 12.0D)));
    }

    @Test
    public void rejectsChunkColumns() {
        assertThrows(IllegalArgumentException.class,
                () -> CubeMapMath.euclideanDistanceSquared(CloPos.chunk(1, 3), Vec3.ZERO));
    }
}
