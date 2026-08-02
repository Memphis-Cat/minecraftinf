package io.github.opencubicchunks.cubicchunks.test.server.level;

import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cubicchunks.server.level.CubicChunkMap;
import io.github.opencubicchunks.cubicchunks.server.level.EntityTracking;
import io.github.opencubicchunks.cubicchunks.world.entity.EntityCubePosGetter;
import net.minecraft.server.level.ServerPlayer;
import org.junit.jupiter.api.Test;

public class TestEntityTracking {
    @Test
    public void forwardsAllEntityCubeCoordinates() {
        CubicChunkMap chunkMap = mock(CubicChunkMap.class);
        ServerPlayer player = mock(ServerPlayer.class);
        EntityCubePosGetter entity = mock(EntityCubePosGetter.class);
        CubePos cubePos = CubePos.of(2, -4, 7);
        when(entity.cc_cubePosition()).thenReturn(cubePos);
        when(chunkMap.cc_isChunkTracked(player, 2, -4, 7)).thenReturn(true);

        assertTrue(EntityTracking.isTracked(chunkMap, player, entity));
        verify(chunkMap).cc_isChunkTracked(player, 2, -4, 7);
    }
}
