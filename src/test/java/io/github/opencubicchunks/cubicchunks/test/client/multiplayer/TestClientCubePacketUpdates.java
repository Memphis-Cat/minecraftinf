package io.github.opencubicchunks.cubicchunks.test.client.multiplayer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cubicchunks.client.multiplayer.ClientCubeCache;
import io.github.opencubicchunks.cubicchunks.client.multiplayer.ClientCubePacketUpdates;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.network.FriendlyByteBuf;
import org.junit.jupiter.api.Test;

public class TestClientCubePacketUpdates {
    @Test
    public void replacesBiomesForTheMatchingLoadedCube() {
        ClientCubeCache.Storage storage = new ClientCubeCache.Storage(2, mock(ClientLevel.class));
        LevelCube cube = mock(LevelCube.class);
        FriendlyByteBuf buffer = mock(FriendlyByteBuf.class);
        CubePos cubePos = CubePos.of(1, -1, 2);
        when(cube.cc_getCubePos()).thenReturn(cubePos);
        storage.replace(storage.getIndex(cubePos.getX(), cubePos.getY(), cubePos.getZ()), cube);

        assertEquals(ClientCubePacketUpdates.Result.UPDATED,
                ClientCubePacketUpdates.replaceBiomes(storage, cubePos.getX(), cubePos.getY(), cubePos.getZ(), buffer));
        verify(cube).replaceBiomes(buffer);
    }

    @Test
    public void ignoresMissingAndOutOfRangeCubes() {
        ClientCubeCache.Storage storage = new ClientCubeCache.Storage(1, mock(ClientLevel.class));
        FriendlyByteBuf buffer = mock(FriendlyByteBuf.class);
        LevelCube wrongCube = mock(LevelCube.class);
        when(wrongCube.cc_getCubePos())
                .thenReturn(CubePos.of(0, 0, 0));
        storage.replace(storage.getIndex(1, 0, 0), wrongCube);

        assertEquals(ClientCubePacketUpdates.Result.MISSING, ClientCubePacketUpdates.replaceBiomes(storage, 1, 0, 0, buffer));
        assertEquals(ClientCubePacketUpdates.Result.OUT_OF_RANGE, ClientCubePacketUpdates.replaceBiomes(storage, 2, 0, 0, buffer));
        verify(wrongCube, never()).replaceBiomes(buffer);
    }
}
