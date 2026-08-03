from pathlib import Path

# This fixture mirrors the vanilla generator futures used by cubic generation.
path = Path("src/test/java/io/github/opencubicchunks/cubicchunks/integrationtest/server/level/IntegrationTestServerCubeCache.java")
text = path.read_text()
old = '''        if (vanillaTest) {
            // These methods are currently only called when running vanilla tests
            when(noiseBasedChunkGeneratorMock.createBiomes(any(), any(), any(), any()))
                    .thenAnswer(i -> CompletableFuture.completedFuture(i.getArguments()[3]));
            when(noiseBasedChunkGeneratorMock.fillFromNoise(any(), any(), any(), any()))
                    .thenAnswer(i -> CompletableFuture.completedFuture(i.getArguments()[3]));
        }
'''
new = '''        when(noiseBasedChunkGeneratorMock.createBiomes(any(), any(), any(), any()))
                .thenAnswer(i -> CompletableFuture.completedFuture(i.getArguments()[3]));
        when(noiseBasedChunkGeneratorMock.fillFromNoise(any(), any(), any(), any()))
                .thenAnswer(i -> CompletableFuture.completedFuture(i.getArguments()[3]));
'''
if text.count(old) != 1:
    raise SystemExit("Expected the vanilla-only generator mock block exactly once")
text = text.replace(old, new)

# Heightmap generation asks the mocked LevelReader for the minimum Y once per
# sampled block. Leaving this to RETURNS_DEEP_STUBS performs expensive generic
# reflection on every call and makes the real ticket-radius test appear hung.
old = '''        when(serverLevelMock.getHeight()).thenReturn(384);
        when(serverLevelMock.getSectionsCount()).thenReturn(24);
'''
new = '''        when(serverLevelMock.getMinY()).thenReturn(-64);
        when(serverLevelMock.getHeight()).thenReturn(384);
        when(serverLevelMock.getSectionsCount()).thenReturn(24);
'''
if text.count(old) != 1:
    raise SystemExit("Expected the server-level height fixture exactly once")
path.write_text(text.replace(old, new))
