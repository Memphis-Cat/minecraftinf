package io.github.opencubicchunks.cubicchunks.test.world.level.cube;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cubicchunks.testutils.BaseTest;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import io.github.opencubicchunks.cubicchunks.world.storage.CubeStorage;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.testframework.junit.EphemeralTestServerProvider;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.api.io.TempDir;
import org.mockito.Answers;

public class TestCubeStorage extends BaseTest {
    @ExtendWith(EphemeralTestServerProvider.class)
    @Test
    public void sectionPaletteSurvivesSaveAndLoad(MinecraftServer server, @TempDir Path temporaryDirectory) throws IOException {
        ServerLevel level = createLevel(server);
        CubePos cubePos = CubePos.of(0, 0, 0);
        LevelCube original = new LevelCube(level, cubePos);
        original.getSections()[0].setBlockState(3, 4, 5, Blocks.DIAMOND_BLOCK.defaultBlockState());
        original.setLightCorrect(true);

        CubeStorage storage = new CubeStorage(temporaryDirectory);
        storage.save(original);

        var loadedProto = storage.load(level, cubePos).orElseThrow();
        assertInstanceOf(LevelCube.class, loadedProto.cc_getWrappedClo());
        LevelCube loaded = (LevelCube) loadedProto.cc_getWrappedClo();

        assertEquals(Blocks.DIAMOND_BLOCK.defaultBlockState(), loaded.getSections()[0].getBlockState(3, 4, 5));
        assertTrue(loaded.isLightCorrect());
    }

    @ExtendWith(EphemeralTestServerProvider.class)
    @Test
    public void dirtyAwareSaveReturnsFalseAfterTheCubeIsClean(MinecraftServer server, @TempDir Path temporaryDirectory) throws IOException {
        LevelCube cube = new LevelCube(createLevel(server), CubePos.of(4, -2, 7));
        cube.markUnsaved();
        CubeStorage storage = new CubeStorage(temporaryDirectory);

        assertTrue(storage.saveIfUnsaved(cube));
        assertFalse(storage.saveIfUnsaved(cube));
    }

    @ExtendWith(EphemeralTestServerProvider.class)
    @Test
    public void failedDirtyAwareSaveMarksTheCubeUnsavedAgain(MinecraftServer server, @TempDir Path temporaryDirectory) throws IOException {
        Path blockedRoot = temporaryDirectory.resolve("blocked-root");
        Files.writeString(blockedRoot, "not a directory");
        LevelCube cube = new LevelCube(createLevel(server), CubePos.of(-3, 5, 9));
        cube.markUnsaved();

        CubeStorage storage = new CubeStorage(blockedRoot);
        assertThrows(IOException.class, () -> storage.saveIfUnsaved(cube));
        assertTrue(cube.isUnsaved());
    }

    private static ServerLevel createLevel(MinecraftServer server) {
        ServerLevel level = mock(ServerLevel.class, Answers.RETURNS_DEEP_STUBS);
        when(level.registryAccess()).thenReturn(server.registryAccess());
        return level;
    }
}
