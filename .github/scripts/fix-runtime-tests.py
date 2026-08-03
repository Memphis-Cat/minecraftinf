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
path.write_text(text.replace(old, new))
