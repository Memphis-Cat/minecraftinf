package io.github.opencubicchunks.cubicchunks.test.server.level;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;

import io.github.opencubicchunks.cc_core.api.CubicConstants;
import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.server.level.CloStatusUpdates;
import net.minecraft.server.level.FullChunkStatus;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.entity.ChunkStatusUpdateListener;
import org.junit.jupiter.api.Test;

public class TestCloStatusUpdates {
    @Test
    public void forwardsColumnsDirectly() {
        ChunkStatusUpdateListener listener = mock(ChunkStatusUpdateListener.class);
        CloStatusUpdates.adapt(listener).onChunkStatusChange(CloPos.chunk(-4, 9), FullChunkStatus.ENTITY_TICKING);
        verify(listener).onChunkStatusChange(new ChunkPos(-4, 9), FullChunkStatus.ENTITY_TICKING);
    }

    @Test
    public void forwardsEveryColumnCoveredByACube() {
        ChunkStatusUpdateListener listener = mock(ChunkStatusUpdateListener.class);
        int cubeX = -3;
        int cubeZ = 5;
        CloStatusUpdates.adapt(listener).onChunkStatusChange(CloPos.cube(cubeX, 12, cubeZ), FullChunkStatus.FULL);

        verify(listener, times(CubicConstants.CHUNK_COUNT)).onChunkStatusChange(org.mockito.ArgumentMatchers.any(),
                org.mockito.ArgumentMatchers.eq(FullChunkStatus.FULL));
        for (int localX = 0; localX < CubicConstants.DIAMETER_IN_SECTIONS; ++localX) {
            for (int localZ = 0; localZ < CubicConstants.DIAMETER_IN_SECTIONS; ++localZ) {
                verify(listener).onChunkStatusChange(new ChunkPos(Coords.cubeToSection(cubeX, localX), Coords.cubeToSection(cubeZ, localZ)),
                        FullChunkStatus.FULL);
            }
        }
    }
}
