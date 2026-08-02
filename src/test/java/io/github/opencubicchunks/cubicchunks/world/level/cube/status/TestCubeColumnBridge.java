package io.github.opencubicchunks.cubicchunks.world.level.cube.status;

import static org.junit.jupiter.api.Assertions.assertEquals;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.utils.Coords;
import org.junit.jupiter.api.Test;

public class TestCubeColumnBridge {
    @Test
    public void mapsEachAxisIndependently() {
        CubePos cubePos = CubePos.of(7, -11, 13);

        assertEquals(Coords.cubeToSection(-11, 0), CubeColumnBridge.sourceSectionY(cubePos, 0));
        assertEquals(Coords.cubeToSection(-11, 1), CubeColumnBridge.sourceSectionY(cubePos, 1));
        assertEquals(Coords.sectionToIndex(0, 1, 1), CubeColumnBridge.targetSectionIndex(0, 1, 1));
        assertEquals(Coords.sectionToIndex(1, 0, 0), CubeColumnBridge.targetSectionIndex(1, 0, 0));
        assertEquals(Coords.columnToColumnIndex(0, 1), CubeColumnBridge.columnIndex(0, 1));
        assertEquals(Coords.columnToColumnIndex(1, 0), CubeColumnBridge.columnIndex(1, 0));
    }
}
