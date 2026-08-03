from pathlib import Path


def replace(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text()
    if text.count(old) != 1:
        raise SystemExit(f"Expected source block exactly once in {path}")
    file.write_text(text.replace(old, new))


path = "src/test/java/io/github/opencubicchunks/cubicchunks/integrationtest/server/level/IntegrationTestServerCubeCache.java"
replace(path, "import java.util.stream.Stream;\n", "")
replace(path, "import org.junit.jupiter.params.ParameterizedTest;\n", "")
replace(path, "import org.junit.jupiter.params.provider.MethodSource;\n", "")
replace(
    path,
    """    private Stream<ChunkStatus> chunkStatuses() {
        return ChunkStatus.getStatusList().stream();
    }

""",
    "",
)
replace(
    path,
    """    @ParameterizedTest
    @MethodSource("chunkStatuses")
    public void getChunkVanilla(ChunkStatus status) throws Exception {
        singleGetChunkVanilla(status);
    }
""",
    """    @Test
    public void getChunkVanilla() throws Exception {
        try (var serverChunkCacheRef = createServerChunkCache(true)) {
            var serverChunkCache = serverChunkCacheRef.value();
            for (ChunkStatus status : ChunkStatus.getStatusList()) {
                var chunkAccess = serverChunkCache.getChunk(0, 0, status, true);
                assertNotNull(chunkAccess);
                assertTrue(chunkAccess.getPersistedStatus().isOrAfter(status));
                if (status.isOrAfter(ChunkStatus.FULL)) {
                    assertInstanceOf(LevelChunk.class, chunkAccess);
                } else {
                    assertInstanceOf(ProtoChunk.class, chunkAccess);
                }
            }
        }
    }
""",
)
replace(
    path,
    """    @ParameterizedTest
    @MethodSource("chunkStatuses")
    public void getChunk(ChunkStatus status) throws Exception {
        singleGetChunk(status);
    }
""",
    """    @Test
    public void getChunk() throws Exception {
        try (var serverChunkCacheRef = createServerChunkCache(false)) {
            var serverChunkCache = serverChunkCacheRef.value();
            for (ChunkStatus status : ChunkStatus.getStatusList()) {
                var chunkAccess = serverChunkCache.getChunk(0, 0, status, true);
                assertNotNull(chunkAccess);
                assertTrue(chunkAccess.getPersistedStatus().isOrAfter(status));
                if (status.isOrAfter(ChunkStatus.FULL)) {
                    assertInstanceOf(LevelChunk.class, chunkAccess);
                } else {
                    assertInstanceOf(ProtoChunk.class, chunkAccess);
                }
            }
        }
    }
""",
)
replace(
    path,
    """    @ParameterizedTest
    @MethodSource("chunkStatuses")
    public void getCube(ChunkStatus status) throws Exception {
        singleGetCube(status);
    }
""",
    """    @Test
    public void getCube() throws Exception {
        try (var serverChunkCacheRef = createServerChunkCache(false)) {
            var serverCubeCache = (ServerCubeCache) serverChunkCacheRef.value();
            for (ChunkStatus status : ChunkStatus.getStatusList()) {
                var cubeAccess = serverCubeCache.cc_getCube(0, 0, 0, status, true);
                assertNotNull(cubeAccess);
                assertTrue(cubeAccess.getPersistedStatus().isOrAfter(status));
                if (status.isOrAfter(ChunkStatus.FULL)) {
                    assertInstanceOf(LevelCube.class, cubeAccess);
                } else {
                    assertInstanceOf(ProtoCube.class, cubeAccess);
                }
            }
        }
    }
""",
)

# Keep generated runtime code compliant with the repository's strict Checkstyle rules.
level_cube = "src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/LevelCube.java"
replace(
    level_cube,
    """public class LevelCube extends CubeAccess implements LevelClo {
    // Fields matching LevelChunk
    static final Logger LOGGER = LogUtils.getLogger();
""",
    """public class LevelCube extends CubeAccess implements LevelClo {
    private static final int PACKED_Y_SHIFT = 4;
    private static final int PACKED_Z_SHIFT = 8;
    private static final int POST_PROCESSING_UPDATE_FLAGS = 276;

    // Fields matching LevelChunk
    static final Logger LOGGER = LogUtils.getLogger();
""",
)
replace(
    level_cube,
    """                int localY = packedPosition >> 4 & SectionPos.SECTION_MASK;
                int localZ = packedPosition >> 8 & SectionPos.SECTION_MASK;
""",
    """                int localY = packedPosition >> PACKED_Y_SHIFT & SectionPos.SECTION_MASK;
                int localZ = packedPosition >> PACKED_Z_SHIFT & SectionPos.SECTION_MASK;
""",
)
replace(
    level_cube,
    "serverLevel.setBlock(blockPos, updatedState, 276);",
    "serverLevel.setBlock(blockPos, updatedState, POST_PROCESSING_UPDATE_FLAGS);",
)

bridge = "src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/status/CubeColumnBridge.java"
replace(
    bridge,
    """    @SuppressWarnings("unchecked")
    private static <T> long copyScheduledTicks(
            long gameTime, CubePos cubePos, TickContainerAccess<T> target, TickContainerAccess<T> source, long subTickOrder
    ) {
        if (!(source instanceof SerializableTickContainer<?> rawSerializable)) {
            return subTickOrder;
        }
        SerializableTickContainer<T> serializable = (SerializableTickContainer<T>) rawSerializable;
        for (SavedTick<T> tick : serializable.pack(gameTime)) {
            BlockPos position = tick.pos();
            if (position.getX() < cubePos.minCubeX() || position.getX() > cubePos.maxCubeX()
                    || position.getY() < cubePos.minCubeY() || position.getY() > cubePos.maxCubeY()
                    || position.getZ() < cubePos.minCubeZ() || position.getZ() > cubePos.maxCubeZ()) {
                continue;
            }
            target.schedule(tick.unpack(gameTime, subTickOrder++));
        }
        return subTickOrder;
    }
""",
    """    @SuppressWarnings("unchecked")
    private static <T> long copyScheduledTicks(
            long gameTime, CubePos cubePos, TickContainerAccess<T> target, TickContainerAccess<T> source, long subTickOrder
    ) {
        if (!(source instanceof SerializableTickContainer<?> rawSerializable)) {
            return subTickOrder;
        }
        long nextSubTickOrder = subTickOrder;
        SerializableTickContainer<T> serializable = (SerializableTickContainer<T>) rawSerializable;
        for (SavedTick<T> tick : serializable.pack(gameTime)) {
            BlockPos position = tick.pos();
            if (position.getX() < cubePos.minCubeX() || position.getX() > cubePos.maxCubeX()
                    || position.getY() < cubePos.minCubeY() || position.getY() > cubePos.maxCubeY()
                    || position.getZ() < cubePos.minCubeZ() || position.getZ() > cubePos.maxCubeZ()) {
                continue;
            }
            target.schedule(tick.unpack(gameTime, nextSubTickOrder++));
        }
        return nextSubTickOrder;
    }
""",
)
