package io.github.opencubicchunks.cubicchunks.test.server.network;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.util.ArrayList;
import java.util.List;

import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.server.network.CloSendOrder;
import io.github.opencubicchunks.cubicchunks.world.level.chunklike.LevelClo;
import org.junit.jupiter.api.Test;

public class TestCloSendOrder {
    @Test
    public void sendsColumnsBeforeCubesWhilePreservingVanillaOrder() {
        long nearCube = CloPos.cubeAsLong(0, 0, 0);
        long farChunk = CloPos.chunkAsLong(10, 10);
        long nearChunk = CloPos.chunkAsLong(0, 0);
        long farCube = CloPos.cubeAsLong(10, 10, 10);
        List<Long> positions = new ArrayList<>(List.of(nearCube, farChunk, farCube, nearChunk));
        positions.sort(CloSendOrder.encodedPositions(position -> position == nearChunk || position == nearCube ? 0 : 10));
        assertEquals(List.of(nearChunk, farChunk, nearCube, farCube), positions);
    }

    @Test
    public void ordersLoadedClosTheSameWay() {
        LevelClo cube = mock(LevelClo.class);
        LevelClo chunk = mock(LevelClo.class);
        when(cube.cc_getCloPos()).thenReturn(CloPos.cube(0, -2, 0));
        when(chunk.cc_getCloPos()).thenReturn(CloPos.chunk(8, 8));
        List<LevelClo> clos = new ArrayList<>(List.of(cube, chunk));
        clos.sort(CloSendOrder.loadedClos(ignored -> 0));
        assertEquals(List.of(chunk, cube), clos);
    }
}
