package io.github.opencubicchunks.cubicchunks.test.client.multiplayer;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import io.github.opencubicchunks.cubicchunks.client.multiplayer.ClientCubeAvailability;
import io.github.opencubicchunks.cubicchunks.client.multiplayer.ClientCubeCache;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import net.minecraft.world.level.chunk.status.ChunkStatus;
import org.junit.jupiter.api.Test;

public class TestClientCubeAvailability {
    @Test
    public void reportsOnlyActuallyLoadedCubes() {
        ClientCubeCache cache = mock(ClientCubeCache.class);
        when(cache.cc_getCube(2, -3, 7, ChunkStatus.FULL, false)).thenReturn(mock(LevelCube.class));

        assertTrue(ClientCubeAvailability.hasCube(cache, 2, -3, 7));
        assertFalse(ClientCubeAvailability.hasCube(cache, 2, -3, 8));
    }
}
