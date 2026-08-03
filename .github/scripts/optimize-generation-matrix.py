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
