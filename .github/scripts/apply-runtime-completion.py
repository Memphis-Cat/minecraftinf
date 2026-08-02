from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one source block in {path}, found {count}")
    file.write_text(text.replace(old, new))


# ChunkMap: notify vanilla column listeners for chunks and every column covered by a cube.
replace_once(
    "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinChunkMap.java",
    "import io.github.opencubicchunks.cubicchunks.server.level.CloTrackingView;\n",
    "import io.github.opencubicchunks.cubicchunks.server.level.CloStatusUpdates;\n"
    "import io.github.opencubicchunks.cubicchunks.server.level.CloTrackingView;\n",
)
replace_once(
    "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinChunkMap.java",
    """            // TODO P2 (entities): actually pass in a cloStatusListener - since ChunkStatusUpdateListener is passed as a parameter, not sure what the
            // best approach is without making our own constructor
            cc_cloStatusListener = (cloPos, fullChunkStatus) -> {};
""",
    """            cc_cloStatusListener = CloStatusUpdates.adapt(chunkStatusListener);
""",
)
replace_once(
    "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinChunkMap.java",
    """    @AddTransformToSets(ChunkToCloSet.ChunkMap_redirects.class)
    @TransformFromMethod("setChunkUnsaved(Lnet/minecraft/world/level/ChunkPos;)V")
    private native void cc_setCloUnsaved(CloPos cloPos);
""",
    """    @AddTransformToSets(ChunkToCloSet.ChunkMap_redirects.class)
    @TransformFromMethod("setChunkUnsaved(Lnet/minecraft/world/level/ChunkPos;)V")
    @Override public native void cc_setCloUnsaved(CloPos cloPos);
""",
)

Path("src/main/java/io/github/opencubicchunks/cubicchunks/server/level/CloStatusUpdates.java").write_text('''package io.github.opencubicchunks.cubicchunks.server.level;

import java.util.Objects;

import io.github.opencubicchunks.cc_core.api.CubicConstants;
import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.world.level.entity.CloStatusUpdateListener;
import net.minecraft.server.level.FullChunkStatus;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.entity.ChunkStatusUpdateListener;

/** Bridges three-dimensional cube status changes to vanilla column status listeners. */
public final class CloStatusUpdates {
    private CloStatusUpdates() {}

    public static CloStatusUpdateListener adapt(ChunkStatusUpdateListener listener) {
        Objects.requireNonNull(listener, "listener");
        return (cloPos, status) -> notify(listener, cloPos, status);
    }

    static void notify(ChunkStatusUpdateListener listener, CloPos cloPos, FullChunkStatus status) {
        if (cloPos.isChunk()) {
            listener.onChunkStatusChange(new ChunkPos(cloPos.getX(), cloPos.getZ()), status);
            return;
        }

        for (int localX = 0; localX < CubicConstants.DIAMETER_IN_SECTIONS; ++localX) {
            for (int localZ = 0; localZ < CubicConstants.DIAMETER_IN_SECTIONS; ++localZ) {
                int chunkX = Coords.cubeToSection(cloPos.getX(), localX);
                int chunkZ = Coords.cubeToSection(cloPos.getZ(), localZ);
                listener.onChunkStatusChange(new ChunkPos(chunkX, chunkZ), status);
            }
        }
    }
}
''')

Path("src/test/java/io/github/opencubicchunks/cubicchunks/test/server/level/TestCloStatusUpdates.java").write_text('''package io.github.opencubicchunks.cubicchunks.test.server.level;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;

import io.github.opencubicchunks.cc_core.api.CubicConstants;
import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.server.level.CloStatusUpdates;
import net.minecraft.server.level.FullChunkStatus;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.entity.ChunkStatusUpdateListener;
import org.junit.jupiter.api.Test;

public class TestCloStatusUpdates {
    @Test
    public void forwardsColumnsDirectly() {
        ChunkStatusUpdateListener listener = mock(ChunkStatusUpdateListener.class);
        CloStatusUpdates.adapt(listener).onChunkStatusChange(CloPos.chunk(-4, 9), FullChunkStatus.ENTITY_TICKING);
        verify(listener).onChunkStatusChange(new ChunkPos(-4, 9), FullChunkStatus.ENTITY_TICKING);
    }

    @Test
    public void forwardsEveryColumnCoveredByACube() {
        ChunkStatusUpdateListener listener = mock(ChunkStatusUpdateListener.class);
        int cubeX = -3;
        int cubeZ = 5;
        CloStatusUpdates.adapt(listener).onChunkStatusChange(CloPos.cube(cubeX, 12, cubeZ), FullChunkStatus.FULL);

        verify(listener, times(CubicConstants.CHUNK_COUNT)).onChunkStatusChange(org.mockito.ArgumentMatchers.any(),
                org.mockito.ArgumentMatchers.eq(FullChunkStatus.FULL));
        for (int localX = 0; localX < CubicConstants.DIAMETER_IN_SECTIONS; ++localX) {
            for (int localZ = 0; localZ < CubicConstants.DIAMETER_IN_SECTIONS; ++localZ) {
                verify(listener).onChunkStatusChange(
                        new ChunkPos(Coords.cubeToSection(cubeX, localX), Coords.cubeToSection(cubeZ, localZ)), FullChunkStatus.FULL);
            }
        }
    }
}
''')

# Full cubes must route dirty notifications into ChunkMap's eager-save set.
Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/world/level/cube/status/MixinCubeStatusTasks.java").write_text('''package io.github.opencubicchunks.cubicchunks.mixin.core.common.world.level.cube.status;

import com.llamalad7.mixinextras.sugar.Local;
import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.server.level.CubicChunkMap;
import io.github.opencubicchunks.cubicchunks.util.StaticCache3D;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import io.github.opencubicchunks.cubicchunks.world.level.cube.status.CubeStatusTasks;
import net.minecraft.world.level.chunk.status.WorldGenContext;
import org.spongepowered.asm.mixin.Dynamic;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

@Mixin(CubeStatusTasks.class)
public class MixinCubeStatusTasks {
    @Dynamic @Redirect(method = "full", at = @At(value = "INVOKE", target = "Lio/github/opencubicchunks/cubicchunks/util/StaticCache3D;get(II)Ljava/lang/Object;"))
    private static Object onFullCube_cacheGet(StaticCache3D<?> instance, int x, int z, @Local(ordinal = 0) CubePos cubePos) {
        return instance.get(x, cubePos.getY(), z);
    }

    @Dynamic @Redirect(method = "dasm$redirect$lambda$full$2", at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/chunk/status/WorldGenContext;unsavedListener()Lio/github/opencubicchunks/cubicchunks/world/level/cube/LevelCube$UnsavedListener;"))
    private static LevelCube.UnsavedListener onFullCube_worldGenContext_unsavedListener(WorldGenContext instance) {
        CubicChunkMap chunkMap = (CubicChunkMap) instance.level().getChunkSource().chunkMap;
        return cubePos -> chunkMap.cc_setCloUnsaved(CloPos.cube(cubePos));
    }
}
''')

# Post-processing and block/fluid tick containers use the real vanilla-derived implementations.
level_cube = "src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/LevelCube.java"
replace_once(
    level_cube,
    "import net.minecraft.world.level.block.EntityBlock;\n",
    "import net.minecraft.world.level.block.EntityBlock;\nimport net.minecraft.world.level.block.LiquidBlock;\n",
)
replace_once(
    level_cube,
    """    // TODO P2 or P3 figure this out later - stub method for now
    public void postProcessGeneration(ServerLevel serverLevel) {
        for (int i = 0; i < this.postProcessing.length; ++i) {
            if (this.postProcessing[i] != null) {
                this.postProcessing[i].clear();
            }
        }

        for (BlockPos blockpos1 : ImmutableList.copyOf(this.pendingBlockEntities.keySet())) {
            this.getBlockEntity(blockpos1);
        }

        this.pendingBlockEntities.clear();
    }
""",
    """    public void postProcessGeneration(ServerLevel serverLevel) {
        for (int sectionIndex = 0; sectionIndex < this.postProcessing.length; ++sectionIndex) {
            if (this.postProcessing[sectionIndex] == null) {
                continue;
            }

            int sectionX = Coords.cubeToSection(this.cubePos.getX(), Coords.indexToX(sectionIndex));
            int sectionY = Coords.cubeToSection(this.cubePos.getY(), Coords.indexToY(sectionIndex));
            int sectionZ = Coords.cubeToSection(this.cubePos.getZ(), Coords.indexToZ(sectionIndex));
            for (short packedPosition : this.postProcessing[sectionIndex]) {
                int localX = packedPosition & SectionPos.SECTION_MASK;
                int localY = packedPosition >> 4 & SectionPos.SECTION_MASK;
                int localZ = packedPosition >> 8 & SectionPos.SECTION_MASK;
                BlockPos blockPos = new BlockPos(
                        SectionPos.sectionToBlockCoord(sectionX, localX),
                        SectionPos.sectionToBlockCoord(sectionY, localY),
                        SectionPos.sectionToBlockCoord(sectionZ, localZ));
                BlockState blockState = this.getBlockState(blockPos);
                FluidState fluidState = blockState.getFluidState();
                if (!fluidState.isEmpty()) {
                    fluidState.tick(serverLevel, blockPos, blockState);
                }
                if (!(blockState.getBlock() instanceof LiquidBlock)) {
                    BlockState updatedState = Block.updateFromNeighbourShapes(blockState, serverLevel, blockPos);
                    if (updatedState != blockState) {
                        serverLevel.setBlock(blockPos, updatedState, 276);
                    }
                }
            }
            this.postProcessing[sectionIndex].clear();
        }

        for (BlockPos blockPos : ImmutableList.copyOf(this.pendingBlockEntities.keySet())) {
            this.getBlockEntity(blockPos);
        }
        this.pendingBlockEntities.clear();
    }
""",
)
replace_once(
    level_cube,
    """    // TODO (P2 or P3) ticks are disabled for now; stub methods as placeholders
//    @TransformFromMethod(value = @MethodSig("registerTickContainerInLevel(Lnet/minecraft/server/level/ServerLevel;)V"), owner = @Ref(LevelChunk
//    .class))
//    public native void registerTickContainerInLevel(ServerLevel level);
    public void registerTickContainerInLevel(ServerLevel level) {}

    // @TransformFromMethod(value = @MethodSig("unregisterTickContainerFromLevel(Lnet/minecraft/server/level/ServerLevel;)V"), owner = @Ref
    // (LevelChunk.class))
//    public native void unregisterTickContainerFromLevel(ServerLevel level);
    public void unregisterTickContainerFromLevel(ServerLevel level) {}
""",
    """    @TransformFromMethod(value = "registerTickContainerInLevel(Lnet/minecraft/server/level/ServerLevel;)V", owner = @Ref(LevelChunk.class))
    public native void registerTickContainerInLevel(ServerLevel level);

    @TransformFromMethod(value = "unregisterTickContainerFromLevel(Lnet/minecraft/server/level/ServerLevel;)V", owner = @Ref(LevelChunk.class))
    public native void unregisterTickContainerFromLevel(ServerLevel level);
""",
)

# The generation task already schedules intersecting vanilla columns one status ahead. Read those completed holders directly;
# re-requesting chunk futures from inside cube generation deadlocks the same scheduler.
bridge = Path("src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/status/CubeColumnBridge.java")
bridge_text = bridge.read_text()
bridge_text = bridge_text.replace("import java.util.ArrayList;\nimport java.util.List;\n", "")
bridge_text = bridge_text.replace("import net.minecraft.server.level.ChunkResult;\n", "import net.minecraft.server.level.ChunkHolder;\n")
bridge_text = bridge_text.replace("import net.minecraft.world.level.biome.Biome;\n", "import net.minecraft.world.level.ChunkPos;\nimport net.minecraft.world.level.biome.Biome;\n")
method_start = bridge_text.index("    public static CompletableFuture<CubeAccess> synchronize")
method_end = bridge_text.index("    static int sourceSectionY", method_start)
bridge_method = '''    public static CompletableFuture<CubeAccess> synchronize(WorldGenContext context, ChunkStatus requiredStatus, CubeAccess cube) {
        CubePos cubePos = cube.cc_getCubePos();
        ChunkAccess[] columns = new ChunkAccess[CubicConstants.CHUNK_COUNT];
        for (int localX = 0; localX < CubicConstants.DIAMETER_IN_SECTIONS; ++localX) {
            for (int localZ = 0; localZ < CubicConstants.DIAMETER_IN_SECTIONS; ++localZ) {
                int chunkX = Coords.cubeToSection(cubePos.getX(), localX);
                int chunkZ = Coords.cubeToSection(cubePos.getZ(), localZ);
                ChunkHolder holder = context.level().getChunkSource().chunkMap.getVisibleChunkIfPresent(ChunkPos.asLong(chunkX, chunkZ));
                ChunkAccess column = holder == null ? null : holder.getChunkIfPresentUnchecked(requiredStatus);
                if (column == null) {
                    throw new IllegalStateException("Scheduled vanilla column " + new ChunkPos(chunkX, chunkZ) + " was unavailable at "
                            + requiredStatus + " while projecting cube " + cubePos);
                }
                columns[columnIndex(localX, localZ)] = column;
            }
        }

        copySections(context, cube, columns);
        if (requiredStatus.isOrAfter(ChunkStatus.FEATURES)) {
            copyPostProcessing(cube, columns);
            copyBlockEntities(context, cube, columns);
        }
        if (requiredStatus.isOrAfter(ChunkStatus.LIGHT)) {
            boolean lightCorrect = true;
            for (ChunkAccess column : columns) {
                lightCorrect &= column.isLightCorrect();
            }
            cube.setLightCorrect(lightCorrect);
        }
        cube.markUnsaved();
        return CompletableFuture.completedFuture(cube);
    }

'''
bridge.write_text(bridge_text[:method_start] + bridge_method + bridge_text[method_end:])

# Stable send ordering keeps columns ahead of cubes while preserving vanilla's distance order.
Path("src/main/java/io/github/opencubicchunks/cubicchunks/server/network/CloSendOrder.java").parent.mkdir(parents=True, exist_ok=True)
Path("src/main/java/io/github/opencubicchunks/cubicchunks/server/network/CloSendOrder.java").write_text('''package io.github.opencubicchunks.cubicchunks.server.network;

import java.util.Comparator;
import java.util.function.ToIntFunction;

import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.world.level.chunklike.LevelClo;

/** Stable send ordering that keeps vanilla columns ahead of dependent cubes. */
public final class CloSendOrder {
    private CloSendOrder() {}

    public static Comparator<Long> encodedPositions(ToIntFunction<Long> vanillaOrder) {
        return Comparator.comparingInt((Long packed) -> CloPos.isChunk(packed) ? 0 : 1)
                .thenComparingInt(vanillaOrder)
                .thenComparingLong(Long::longValue);
    }

    public static Comparator<LevelClo> loadedClos(ToIntFunction<LevelClo> vanillaOrder) {
        return Comparator.comparingInt((LevelClo clo) -> clo.cc_getCloPos().isChunk() ? 0 : 1)
                .thenComparingInt(vanillaOrder)
                .thenComparingLong(clo -> clo.cc_getCloPos().toLong());
    }
}
''')

sender = "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/network/MixinPlayerChunkSender.java"
replace_once(sender, "import io.github.opencubicchunks.cubicchunks.network.CCClientboundLevelChunkPacket;\n", "")
replace_once(
    sender,
    "import io.github.opencubicchunks.cubicchunks.network.CCClientboundLevelCubeWithLightPacket;\n",
    "import io.github.opencubicchunks.cubicchunks.network.CCClientboundLevelCubeWithLightPacket;\n"
    "import io.github.opencubicchunks.cubicchunks.server.network.CloSendOrder;\n",
)
replace_once(
    sender,
    "import net.minecraft.network.protocol.game.ClientboundChunkBatchStartPacket;\n",
    "import net.minecraft.network.protocol.game.ClientboundChunkBatchStartPacket;\n"
    "import net.minecraft.network.protocol.game.ClientboundLevelChunkWithLightPacket;\n",
)
replace_once(
    sender,
    "PacketDistributor.sendToPlayer(packetListener.player, new CCClientboundLevelChunkPacket(chunk.getPos()));",
    "packetListener.send(new ClientboundLevelChunkWithLightPacket(chunk, level.getLightEngine(), null, null));",
)
replace_once(
    sender,
    """    // FIXME these should probably have some kind of reasonable sort order - at the very least, chunks before cubes
    @Dynamic @Redirect(method = "cc_collectChunksToSend", at = @At(ordinal = 0, value = "INVOKE", target = "Ljava/util/Comparator;comparingInt(Ljava/util/function/ToIntFunction;)Ljava/util/Comparator;"))
    private Comparator<Long> cc_onCollectChunksToSend_comparator1(ToIntFunction<Long> keyExtractor) {
        return (a, b) -> 0;
    }

    @Dynamic @Redirect(method = "cc_collectChunksToSend", at = @At(ordinal = 1, value = "INVOKE", target = "Ljava/util/Comparator;comparingInt(Ljava/util/function/ToIntFunction;)Ljava/util/Comparator;"))
    private Comparator<LevelClo> cc_onCollectChunksToSend_comparator2(ToIntFunction<LevelClo> keyExtractor) {
        return (a, b) -> 0;
    }
""",
    """    @Dynamic @Redirect(method = "cc_collectChunksToSend", at = @At(ordinal = 0, value = "INVOKE", target = "Ljava/util/Comparator;comparingInt(Ljava/util/function/ToIntFunction;)Ljava/util/Comparator;"))
    private Comparator<Long> cc_onCollectChunksToSend_comparator1(ToIntFunction<Long> keyExtractor) {
        return CloSendOrder.encodedPositions(keyExtractor);
    }

    @Dynamic @Redirect(method = "cc_collectChunksToSend", at = @At(ordinal = 1, value = "INVOKE", target = "Ljava/util/Comparator;comparingInt(Ljava/util/function/ToIntFunction;)Ljava/util/Comparator;"))
    private Comparator<LevelClo> cc_onCollectChunksToSend_comparator2(ToIntFunction<LevelClo> keyExtractor) {
        return CloSendOrder.loadedClos(keyExtractor);
    }
""",
)

Path("src/test/java/io/github/opencubicchunks/cubicchunks/test/server/network").mkdir(parents=True, exist_ok=True)
Path("src/test/java/io/github/opencubicchunks/cubicchunks/test/server/network/TestCloSendOrder.java").write_text('''package io.github.opencubicchunks.cubicchunks.test.server.network;

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
''')

# Send real vanilla column packets and remove the fake position-only column payload.
replace_once(
    "src/main/java/io/github/opencubicchunks/cubicchunks/network/CCNetworkHandler.java",
    """        registrar.playToClient(CCClientboundLevelChunkPacket.TYPE, CCClientboundLevelChunkPacket.STREAM_CODEC,
                new CCClientboundLevelChunkPacket.Handler());
""",
    "",
)
Path("src/main/java/io/github/opencubicchunks/cubicchunks/network/CCClientboundLevelChunkPacket.java").unlink()
Path("src/test/java/io/github/opencubicchunks/cubicchunks/test/network/TestCCClientboundLevelChunkPacket.java").unlink()

# Remove all temporary application machinery and restore normal read-only CI in the committed tree.
Path(".github/runtime-completion.patch").unlink(missing_ok=True)
Path(".github/scripts/apply-runtime-completion.py").unlink()
Path(".github/workflows/phase1-ci.yml").write_text('''name: CubicChunks3 Phase 1 CI

on:
  push:
    branches:
      - agent/**
  pull_request:
    branches:
      - dev

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    steps:
      - name: Check out repository and submodules
        uses: actions/checkout@v4
        with:
          submodules: recursive
          fetch-depth: 0
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '21'
          cache: gradle
      - uses: gradle/actions/wrapper-validation@v4
      - run: chmod +x gradlew
      - name: Run unit tests
        run: ./gradlew test --stacktrace --no-daemon
      - name: Run full checks
        run: ./gradlew check --stacktrace --no-daemon
      - name: Inspect Minecraft completion APIs
        if: always()
        run: bash .github/scripts/inspect-minecraft-storage.sh
      - name: Upload Minecraft completion API inspection
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: phase1-minecraft-storage-api
          path: build/minecraft-storage-inspection/
          if-no-files-found: ignore
          retention-days: 7
      - name: Upload reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: phase1-reports
          path: |
            build/reports/
            build/test-results/
            CubicChunksCore/build/reports/
            CubicChunksCore/build/test-results/
          if-no-files-found: ignore

  server-smoke:
    needs: validate
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive
          fetch-depth: 0
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '21'
          cache: gradle
      - run: chmod +x gradlew
      - name: Configure smoke-test server
        run: |
          mkdir -p run
          printf 'eula=true\\n' > run/eula.txt
          cat > run/server.properties <<'PROPERTIES'
          online-mode=false
          view-distance=2
          simulation-distance=2
          max-tick-time=-1
          level-name=phase1-smoke-world
          motd=CubicChunks3 Phase 1 Smoke Test
          PROPERTIES
      - name: Start dedicated server and wait for readiness
        run: |
          set -euo pipefail
          : > server-smoke.log
          setsid ./gradlew runServer --stacktrace --no-daemon >server-smoke.log 2>&1 &
          process_group=$!
          cleanup() {
            kill -INT -- "-$process_group" >/dev/null 2>&1 || true
            sleep 5
            kill -TERM -- "-$process_group" >/dev/null 2>&1 || true
            wait "$process_group" >/dev/null 2>&1 || true
          }
          trap cleanup EXIT
          for _ in $(seq 1 360); do
            if grep -Eq 'Done \\([0-9.]+s\\)!|For help, type "help"' server-smoke.log; then
              exit 0
            fi
            if ! kill -0 "$process_group" >/dev/null 2>&1; then
              cat server-smoke.log
              exit 1
            fi
            sleep 1
          done
          cat server-smoke.log
          exit 1
      - name: Upload dedicated-server logs
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: phase1-server-smoke-logs
          path: |
            server-smoke.log
            run/logs/
            run/crash-reports/
          if-no-files-found: ignore

  persistence-smoke:
    needs: server-smoke
    runs-on: ubuntu-latest
    timeout-minutes: 25
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive
          fetch-depth: 0
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '21'
          cache: gradle
      - name: Run cubic save and reload test
        run: bash .github/scripts/server-persistence-smoke.sh
      - name: Upload persistence logs and world metadata
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: phase1-persistence-smoke-logs
          path: |
            server-persistence-first.log
            server-persistence-second.log
            save-flush-rcon.log
            save-flush-processes.txt
            save-flush-thread-*.txt
            run/logs/
            run/crash-reports/
            run/phase1-persistence-world/level.dat
            run/phase1-persistence-world/level.dat_old
            run/phase1-persistence-world/cubicchunks/**
          if-no-files-found: ignore
''')
