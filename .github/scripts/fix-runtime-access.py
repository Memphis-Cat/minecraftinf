from pathlib import Path


def replace(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text()
    if text.count(old) != 1:
        raise SystemExit(f"Expected source block exactly once in {path}")
    file.write_text(text.replace(old, new))


# Expose visible holder lookup through the public cubic contract rather than directly invoking
# ChunkMap's protected method from CubeColumnBridge.
path = "src/main/java/io/github/opencubicchunks/cubicchunks/server/level/CubicChunkMap.java"
replace(
    path,
    "import net.minecraft.server.level.ChunkGenerationTask;\n",
    "import javax.annotation.Nullable;\n\nimport net.minecraft.server.level.ChunkGenerationTask;\nimport net.minecraft.server.level.ChunkHolder;\n",
)
replace(
    path,
    "    ChunkGenerationTask cc_scheduleGenerationTask(ChunkStatus chunkStatus, CubePos cubePos);\n",
    "    ChunkGenerationTask cc_scheduleGenerationTask(ChunkStatus chunkStatus, CubePos cubePos);\n\n"
    "    @Nullable ChunkHolder cc_getVisibleChunkIfPresent(long position);\n",
)

path = "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinChunkMap.java"
replace(
    path,
    "    @Shadow protected abstract ChunkHolder getUpdatingChunkIfPresent(long aLong);\n",
    "    @Shadow protected abstract ChunkHolder getUpdatingChunkIfPresent(long aLong);\n\n"
    "    @Shadow protected abstract @Nullable ChunkHolder getVisibleChunkIfPresent(long position);\n",
)
replace(
    path,
    "    @Override public native void cc_setCloUnsaved(CloPos cloPos);\n",
    "    @Override public native void cc_setCloUnsaved(CloPos cloPos);\n\n"
    "    @Override public @Nullable ChunkHolder cc_getVisibleChunkIfPresent(long position) {\n"
    "        return this.getVisibleChunkIfPresent(position);\n"
    "    }\n",
)

path = "src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/status/CubeColumnBridge.java"
replace(
    path,
    "import io.github.opencubicchunks.cubicchunks.world.level.cube.CubeAccess;\n",
    "import io.github.opencubicchunks.cubicchunks.server.level.CubicChunkMap;\n"
    "import io.github.opencubicchunks.cubicchunks.world.level.cube.CubeAccess;\n",
)
replace(
    path,
    "                ChunkHolder holder = context.level().getChunkSource().chunkMap.getVisibleChunkIfPresent(ChunkPos.asLong(chunkX, chunkZ));\n",
    "                ChunkHolder holder = ((CubicChunkMap) context.level().getChunkSource().chunkMap)\n"
    "                        .cc_getVisibleChunkIfPresent(ChunkPos.asLong(chunkX, chunkZ));\n",
)

# DASM copies vanilla generation methods into CCChunkStatusTasks. Those methods access the source
# class's private LOGGER field, so the transformed target must own a matching redirected field.
path = "src/main/java/io/github/opencubicchunks/cubicchunks/world/level/chunk/status/CCChunkStatusTasks.java"
replace(
    path,
    "import java.util.concurrent.CompletableFuture;\n\nimport io.github.notstirred.dasm.api.annotations.Dasm;\n",
    "import java.util.concurrent.CompletableFuture;\n\nimport com.mojang.logging.LogUtils;\n"
    "import io.github.notstirred.dasm.api.annotations.Dasm;\n"
    "import io.github.notstirred.dasm.api.annotations.redirect.redirects.AddFieldToSets;\n",
)
replace(
    path,
    "import net.minecraft.world.level.storage.ValueInput;\n",
    "import net.minecraft.world.level.storage.ValueInput;\nimport org.slf4j.Logger;\n",
)
replace(
    path,
    "public final class CCChunkStatusTasks {\n    private CCChunkStatusTasks() {}\n",
    "public final class CCChunkStatusTasks {\n"
    "    @AddFieldToSets(containers = ChunkInCubicContextSet.ChunkStatusTasks_to_CCChunkStatusTasks_redirects.class, "
    "field = \"LOGGER:Lorg/slf4j/Logger;\")\n"
    "    private static final Logger LOGGER = LogUtils.getLogger();\n\n"
    "    private CCChunkStatusTasks() {}\n",
)

# The storage test uses mocked cubes. Supply the invariant real cubes always provide: a complete
# non-null section array. Production code must not add null-tolerant behavior for impossible cubes.
path = "src/test/java/io/github/opencubicchunks/cubicchunks/test/client/multiplayer/TestClientCubePacketUpdates.java"
replace(
    path,
    "import static org.mockito.Mockito.mock;\n",
    "import static org.mockito.Mockito.mock;\nimport static org.mockito.Mockito.mockingDetails;\n",
)
# Remove unused mockingDetails immediately after using a more precise helper implementation below.
replace(
    path,
    "import static org.mockito.Mockito.mockingDetails;\n",
    "",
)
replace(
    path,
    "import io.github.opencubicchunks.cc_core.api.CubePos;\n",
    "import java.util.Arrays;\n\n"
    "import io.github.opencubicchunks.cc_core.api.CubePos;\n"
    "import io.github.opencubicchunks.cc_core.api.CubicConstants;\n",
)
replace(
    path,
    "import net.minecraft.network.FriendlyByteBuf;\n",
    "import net.minecraft.network.FriendlyByteBuf;\nimport net.minecraft.world.level.chunk.LevelChunkSection;\n",
)
replace(
    path,
    "        when(cube.cc_getCubePos()).thenReturn(cubePos);\n",
    "        when(cube.cc_getCubePos()).thenReturn(cubePos);\n"
    "        when(cube.getSections()).thenReturn(nonEmptySections());\n",
)
replace(
    path,
    "        when(wrongCube.cc_getCubePos()).thenReturn(CubePos.of(0, 0, 0));\n",
    "        when(wrongCube.cc_getCubePos()).thenReturn(CubePos.of(0, 0, 0));\n"
    "        when(wrongCube.getSections()).thenReturn(nonEmptySections());\n",
)
replace(
    path,
    "    }\n}\n",
    "    }\n\n"
    "    private static LevelChunkSection[] nonEmptySections() {\n"
    "        LevelChunkSection[] sections = new LevelChunkSection[CubicConstants.SECTION_COUNT];\n"
    "        Arrays.setAll(sections, ignored -> {\n"
    "            LevelChunkSection section = mock(LevelChunkSection.class);\n"
    "            when(section.hasOnlyAir()).thenReturn(false);\n"
    "            return section;\n"
    "        });\n"
    "        return sections;\n"
    "    }\n"
    "}\n",
)
