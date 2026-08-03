from pathlib import Path


def replace(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text()
    if text.count(old) != 1:
        raise SystemExit(f"Expected source block exactly once in {path}")
    file.write_text(text.replace(old, new))


path = "src/test/java/io/github/opencubicchunks/cubicchunks/integrationtest/server/level/IntegrationTestServerCubeCache.java"
replace(
    path,
    "import io.github.opencubicchunks.cubicchunks.testutils.CloseableReference;\n",
    "import io.github.opencubicchunks.cubicchunks.testutils.CloseableReference;\n"
    "import io.github.opencubicchunks.cubicchunks.world.level.CubicLevelTicks;\n",
)
replace(
    path,
    """        when(serverLevelMock.getHeight()).thenReturn(384);
        when(serverLevelMock.getSectionsCount()).thenReturn(24);
""",
    """        when(serverLevelMock.getHeight()).thenReturn(384);
        when(serverLevelMock.getSectionsCount()).thenReturn(24);
        if (!vanillaTest) {
            when(serverLevelMock.getBlockTicks()).thenReturn(new CubicLevelTicks<>(ignored -> true));
            when(serverLevelMock.getFluidTicks()).thenReturn(new CubicLevelTicks<>(ignored -> true));
        }
""",
)
