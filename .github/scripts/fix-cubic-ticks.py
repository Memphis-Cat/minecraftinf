from pathlib import Path


def replace(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text()
    if text.count(old) != 1:
        raise SystemExit(f"Expected source block exactly once in {path}")
    file.write_text(text.replace(old, new))


Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/access/common/LevelTicksAccess.java").write_text('''package io.github.opencubicchunks.cubicchunks.mixin.access.common;

import java.util.List;
import java.util.Queue;

import it.unimi.dsi.fastutil.longs.Long2LongMap;
import it.unimi.dsi.fastutil.longs.Long2ObjectMap;
import net.minecraft.world.ticks.LevelChunkTicks;
import net.minecraft.world.ticks.LevelTicks;
import net.minecraft.world.ticks.ScheduledTick;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

@Mixin(LevelTicks.class)
public interface LevelTicksAccess<T> {
    @Accessor("allContainers")
    Long2ObjectMap<LevelChunkTicks<T>> cc_getAllContainers();

    @Accessor("nextTickForContainer")
    Long2LongMap cc_getNextTickForContainer();

    @Accessor("alreadyRunThisTick")
    List<ScheduledTick<T>> cc_getAlreadyRunThisTick();

    @Accessor("toRunThisTick")
    Queue<ScheduledTick<T>> cc_getToRunThisTick();
}
''')

Path("src/main/java/io/github/opencubicchunks/cubicchunks/world/level/CubicLevelTicks.java").write_text('''package io.github.opencubicchunks.cubicchunks.world.level;

import java.util.ArrayList;
import java.util.List;
import java.util.LongSummaryStatistics;
import java.util.function.LongPredicate;
import java.util.function.Predicate;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cubicchunks.mixin.access.common.LevelTicksAccess;
import it.unimi.dsi.fastutil.longs.Long2ObjectMap;
import net.minecraft.Util;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Vec3i;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.ticks.LevelChunkTicks;
import net.minecraft.world.ticks.LevelTicks;
import net.minecraft.world.ticks.ScheduledTick;

/**
 * Three-dimensional scheduled-tick storage for cubic levels.
 *
 * <p>Vanilla {@link LevelTicks} keys containers by X/Z chunk columns. That cannot represent two
 * independently loaded cubes with the same X/Z coordinates at different Y levels. This class
 * keeps the vanilla draining machinery, but keys every container and every scheduling update by
 * the full packed {@link CubePos}.</p>
 */
public final class CubicLevelTicks<T> extends LevelTicks<T> {
    public CubicLevelTicks(LongPredicate tickCheck) {
        super(tickCheck);
    }

    public void addContainer(CubePos cubePos, LevelChunkTicks<T> ticks) {
        long packed = cubePos.asLong();
        LevelChunkTicks<T> previous = this.access().cc_getAllContainers().put(packed, ticks);
        if (previous != null && previous != ticks) {
            previous.setOnTickAdded(null);
        }

        ScheduledTick<T> first = ticks.peek();
        if (first != null) {
            this.access().cc_getNextTickForContainer().put(packed, first.triggerTick());
        } else {
            this.access().cc_getNextTickForContainer().remove(packed);
        }

        ticks.setOnTickAdded((container, addedTick) -> {
            if (addedTick.equals(container.peek())) {
                this.access().cc_getNextTickForContainer().put(CubePos.asLong(addedTick.pos()), addedTick.triggerTick());
            }
        });
    }

    /**
     * Vanilla columns are generation backing data in a cubic level. Runtime block/fluid ticks are
     * migrated into cubes and must not be registered a second time as column containers.
     */
    @Override public void addContainer(ChunkPos chunkPos, LevelChunkTicks<T> ticks) {}

    public void removeContainer(CubePos cubePos) {
        long packed = cubePos.asLong();
        LevelChunkTicks<T> ticks = this.access().cc_getAllContainers().remove(packed);
        this.access().cc_getNextTickForContainer().remove(packed);
        if (ticks != null) {
            ticks.setOnTickAdded(null);
        }
    }

    @Override public void removeContainer(ChunkPos chunkPos) {}

    @Override public void schedule(ScheduledTick<T> scheduledTick) {
        long packed = CubePos.asLong(scheduledTick.pos());
        LevelChunkTicks<T> ticks = this.access().cc_getAllContainers().get(packed);
        if (ticks == null) {
            Util.logAndPauseIfInIde("Trying to schedule tick in not loaded cube at " + scheduledTick.pos());
            return;
        }
        ticks.schedule(scheduledTick);
    }

    @Override public boolean hasScheduledTick(BlockPos blockPos, T type) {
        LevelChunkTicks<T> ticks = this.access().cc_getAllContainers().get(CubePos.asLong(blockPos));
        return ticks != null && ticks.hasScheduledTick(blockPos, type);
    }

    @Override public void clearArea(BoundingBox boundingBox) {
        Predicate<ScheduledTick<T>> inside = tick -> boundingBox.isInside(tick.pos());
        this.forContainersInArea(boundingBox, (packed, container) -> {
            ScheduledTick<T> previousFirst = container.peek();
            container.removeIf(inside);
            ScheduledTick<T> currentFirst = container.peek();
            if (currentFirst != previousFirst) {
                if (currentFirst == null) {
                    this.access().cc_getNextTickForContainer().remove(packed);
                } else {
                    this.access().cc_getNextTickForContainer().put(packed, currentFirst.triggerTick());
                }
            }
        });
        this.access().cc_getAlreadyRunThisTick().removeIf(inside);
        this.access().cc_getToRunThisTick().removeIf(inside);
    }

    @Override public void copyArea(BoundingBox boundingBox, Vec3i offset) {
        this.copyAreaFrom(this, boundingBox, offset);
    }

    @Override public void copyAreaFrom(LevelTicks<T> source, BoundingBox boundingBox, Vec3i offset) {
        Predicate<ScheduledTick<T>> inside = tick -> boundingBox.isInside(tick.pos());
        List<ScheduledTick<T>> copied = new ArrayList<>();
        LevelTicksAccess<T> sourceAccess = access(source);
        sourceAccess.cc_getAlreadyRunThisTick().stream().filter(inside).forEach(copied::add);
        sourceAccess.cc_getToRunThisTick().stream().filter(inside).forEach(copied::add);
        sourceAccess.cc_getAllContainers().values().forEach(container -> container.getAll().filter(inside).forEach(copied::add));
        if (copied.isEmpty()) {
            return;
        }

        LongSummaryStatistics statistics = copied.stream().mapToLong(ScheduledTick::subTickOrder).summaryStatistics();
        long minimumSubTickOrder = statistics.getMin();
        long maximumSubTickOrder = statistics.getMax();
        copied.forEach(tick -> this.schedule(new ScheduledTick<>(tick.type(), tick.pos().offset(offset), tick.triggerTick(), tick.priority(),
                tick.subTickOrder() - minimumSubTickOrder + maximumSubTickOrder + 1L)));
    }

    private void forContainersInArea(BoundingBox boundingBox, ContainerConsumer<T> consumer) {
        int minCubeX = Coords.blockToCube(boundingBox.minX());
        int minCubeY = Coords.blockToCube(boundingBox.minY());
        int minCubeZ = Coords.blockToCube(boundingBox.minZ());
        int maxCubeX = Coords.blockToCube(boundingBox.maxX());
        int maxCubeY = Coords.blockToCube(boundingBox.maxY());
        int maxCubeZ = Coords.blockToCube(boundingBox.maxZ());
        Long2ObjectMap<LevelChunkTicks<T>> containers = this.access().cc_getAllContainers();

        for (int cubeX = minCubeX; cubeX <= maxCubeX; ++cubeX) {
            for (int cubeY = minCubeY; cubeY <= maxCubeY; ++cubeY) {
                for (int cubeZ = minCubeZ; cubeZ <= maxCubeZ; ++cubeZ) {
                    long packed = CubePos.asLong(cubeX, cubeY, cubeZ);
                    LevelChunkTicks<T> container = containers.get(packed);
                    if (container != null) {
                        consumer.accept(packed, container);
                    }
                }
            }
        }
    }

    @SuppressWarnings("unchecked")
    private LevelTicksAccess<T> access() {
        return (LevelTicksAccess<T>) (Object) this;
    }

    @SuppressWarnings("unchecked")
    private static <T> LevelTicksAccess<T> access(LevelTicks<T> ticks) {
        return (LevelTicksAccess<T>) (Object) ticks;
    }

    @FunctionalInterface
    private interface ContainerConsumer<T> {
        void accept(long packed, LevelChunkTicks<T> container);
    }
}
''')

server_level = "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinServerLevel.java"
replace(
    server_level,
    "import java.util.concurrent.Executor;\n",
    "import java.util.concurrent.Executor;\nimport java.util.function.LongPredicate;\n",
)
replace(
    server_level,
    "import io.github.opencubicchunks.cubicchunks.world.level.chunklike.LevelClo;\n",
    "import io.github.opencubicchunks.cubicchunks.world.level.CubicLevelTicks;\n"
    "import io.github.opencubicchunks.cubicchunks.world.level.chunklike.LevelClo;\n",
)
replace(
    server_level,
    "import net.minecraft.world.level.storage.ServerLevelData;\n",
    "import net.minecraft.world.level.storage.ServerLevelData;\nimport net.minecraft.world.ticks.LevelTicks;\n",
)
replace(
    server_level,
    "import org.spongepowered.asm.mixin.injection.Inject;\n",
    "import org.spongepowered.asm.mixin.injection.Inject;\nimport org.spongepowered.asm.mixin.injection.Redirect;\n",
)
replace(
    server_level,
    """    @Override public ServerCubeCache cc_getCubeSource() {
        return ((ServerCubeCache) this.chunkSource);
    }
""",
    """    @Redirect(method = "<init>", at = @At(value = "NEW", target = "net/minecraft/world/ticks/LevelTicks"))
    private <T> LevelTicks<T> cc_createLevelTicks(LongPredicate vanillaTickCheck) {
        if (!this.cc_isCubic) {
            return new LevelTicks<>(vanillaTickCheck);
        }
        return new CubicLevelTicks<>(packedCube -> this.chunkSource.isPositionTicking(packedCube));
    }

    @Override public ServerCubeCache cc_getCubeSource() {
        return ((ServerCubeCache) this.chunkSource);
    }
""",
)

level_cube = "src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/LevelCube.java"
replace(
    level_cube,
    "import io.github.opencubicchunks.cubicchunks.mixin.dasmsets.ChunkToCubeSet;\n",
    "import io.github.opencubicchunks.cubicchunks.mixin.dasmsets.ChunkToCubeSet;\n"
    "import io.github.opencubicchunks.cubicchunks.world.level.CubicLevelTicks;\n",
)
replace(
    level_cube,
    """    @TransformFromMethod(value = "registerTickContainerInLevel(Lnet/minecraft/server/level/ServerLevel;)V", owner = @Ref(LevelChunk.class))
    public native void registerTickContainerInLevel(ServerLevel level);

    @TransformFromMethod(value = "unregisterTickContainerFromLevel(Lnet/minecraft/server/level/ServerLevel;)V", owner = @Ref(LevelChunk.class))
    public native void unregisterTickContainerFromLevel(ServerLevel level);
""",
    """    public void registerTickContainerInLevel(ServerLevel level) {
        cubicTicks(level.getBlockTicks(), "block").addContainer(this.cubePos, this.blockTicks);
        cubicTicks(level.getFluidTicks(), "fluid").addContainer(this.cubePos, this.fluidTicks);
    }

    public void unregisterTickContainerFromLevel(ServerLevel level) {
        cubicTicks(level.getBlockTicks(), "block").removeContainer(this.cubePos);
        cubicTicks(level.getFluidTicks(), "fluid").removeContainer(this.cubePos);
    }

    @SuppressWarnings("unchecked")
    private static <T> CubicLevelTicks<T> cubicTicks(LevelTicks<T> ticks, String type) {
        if (!(ticks instanceof CubicLevelTicks<?> cubicTicks)) {
            throw new IllegalStateException("Cubic level uses non-cubic " + type + " tick storage: " + ticks.getClass().getName());
        }
        return (CubicLevelTicks<T>) cubicTicks;
    }
""",
)
replace(
    level_cube,
    "import net.minecraft.world.ticks.LevelChunkTicks;\n",
    "import net.minecraft.world.ticks.LevelChunkTicks;\nimport net.minecraft.world.ticks.LevelTicks;\n",
)

bridge = "src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/status/CubeColumnBridge.java"
replace(
    bridge,
    "import net.minecraft.world.level.biome.Biome;\n",
    "import net.minecraft.world.level.biome.Biome;\n"
    "import net.minecraft.world.level.block.Block;\n",
)
replace(
    bridge,
    "import net.minecraft.world.level.chunk.status.WorldGenContext;\n",
    "import net.minecraft.world.level.chunk.status.WorldGenContext;\n"
    "import net.minecraft.world.level.material.Fluid;\n"
    "import net.minecraft.world.ticks.SavedTick;\n"
    "import net.minecraft.world.ticks.SerializableTickContainer;\n"
    "import net.minecraft.world.ticks.TickContainerAccess;\n",
)
replace(
    bridge,
    """        if (requiredStatus.isOrAfter(ChunkStatus.FEATURES)) {
            copyPostProcessing(cube, columns);
            copyBlockEntities(context, cube, columns);
        }
""",
    """        if (requiredStatus.isOrAfter(ChunkStatus.FEATURES)) {
            copyPostProcessing(cube, columns);
            copyBlockEntities(context, cube, columns);
            copyScheduledTicks(context, cube, columns);
        }
""",
)
replace(
    bridge,
    """    private static void copyBlockEntities(WorldGenContext context, CubeAccess cube, ChunkAccess[] columns) {
""",
    """    private static void copyScheduledTicks(WorldGenContext context, CubeAccess cube, ChunkAccess[] columns) {
        long gameTime = context.level().getGameTime();
        long blockSubTickOrder = 0L;
        long fluidSubTickOrder = 0L;
        for (ChunkAccess column : columns) {
            blockSubTickOrder = copyScheduledTicks(gameTime, cube.cc_getCubePos(), cube.getBlockTicks(), column.getBlockTicks(), blockSubTickOrder);
            fluidSubTickOrder = copyScheduledTicks(gameTime, cube.cc_getCubePos(), cube.getFluidTicks(), column.getFluidTicks(), fluidSubTickOrder);
        }
    }

    @SuppressWarnings("unchecked")
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

    private static void copyBlockEntities(WorldGenContext context, CubeAccess cube, ChunkAccess[] columns) {
""",
)
# Remove imports added only for generic type inference if Spotless/Checkstyle identifies them as unused.
replace(bridge, "import net.minecraft.world.level.block.Block;\n", "")
replace(bridge, "import net.minecraft.world.level.material.Fluid;\n", "")

Path("src/test/java/io/github/opencubicchunks/cubicchunks/test/world/level/TestCubicLevelTicks.java").parent.mkdir(parents=True, exist_ok=True)
Path("src/test/java/io/github/opencubicchunks/cubicchunks/test/world/level/TestCubicLevelTicks.java").write_text('''package io.github.opencubicchunks.cubicchunks.test.world.level;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cubicchunks.world.level.CubicLevelTicks;
import net.minecraft.core.BlockPos;
import net.minecraft.world.ticks.LevelChunkTicks;
import net.minecraft.world.ticks.ScheduledTick;
import net.minecraft.world.ticks.TickPriority;
import org.junit.jupiter.api.Test;

public class TestCubicLevelTicks {
    @Test
    public void keepsStackedCubeContainersIndependent() {
        CubicLevelTicks<String> ticks = new CubicLevelTicks<>(ignored -> true);
        CubePos lower = CubePos.of(2, -4, 7);
        CubePos upper = CubePos.of(2, 9, 7);
        BlockPos lowerPos = new BlockPos(lower.minCubeX() + 1, lower.minCubeY() + 2, lower.minCubeZ() + 3);
        BlockPos upperPos = new BlockPos(upper.minCubeX() + 1, upper.minCubeY() + 2, upper.minCubeZ() + 3);

        ticks.addContainer(lower, new LevelChunkTicks<>());
        ticks.addContainer(upper, new LevelChunkTicks<>());
        ticks.schedule(new ScheduledTick<>("lower", lowerPos, 10L, TickPriority.NORMAL, 0L));
        ticks.schedule(new ScheduledTick<>("upper", upperPos, 11L, TickPriority.NORMAL, 1L));

        assertTrue(ticks.hasScheduledTick(lowerPos, "lower"));
        assertTrue(ticks.hasScheduledTick(upperPos, "upper"));
        ticks.removeContainer(lower);
        assertFalse(ticks.hasScheduledTick(lowerPos, "lower"));
        assertTrue(ticks.hasScheduledTick(upperPos, "upper"));
    }
}
''')

# Avoid nested Mockito stubbing: construct the section array before opening when(...).thenReturn(...).
test_packets = "src/test/java/io/github/opencubicchunks/cubicchunks/test/client/multiplayer/TestClientCubePacketUpdates.java"
replace(
    test_packets,
    """        when(cube.cc_getCubePos()).thenReturn(cubePos);
        when(cube.getSections()).thenReturn(nonEmptySections());
""",
    """        LevelChunkSection[] cubeSections = nonEmptySections();
        when(cube.cc_getCubePos()).thenReturn(cubePos);
        when(cube.getSections()).thenReturn(cubeSections);
""",
)
replace(
    test_packets,
    """        when(wrongCube.cc_getCubePos()).thenReturn(CubePos.of(0, 0, 0));
        when(wrongCube.getSections()).thenReturn(nonEmptySections());
""",
    """        LevelChunkSection[] wrongCubeSections = nonEmptySections();
        when(wrongCube.cc_getCubePos()).thenReturn(CubePos.of(0, 0, 0));
        when(wrongCube.getSections()).thenReturn(wrongCubeSections);
""",
)
