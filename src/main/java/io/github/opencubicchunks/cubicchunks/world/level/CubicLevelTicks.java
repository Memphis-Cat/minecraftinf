package io.github.opencubicchunks.cubicchunks.world.level;

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
 * <p>
 * Vanilla {@link LevelTicks} keys containers by X/Z chunk columns. That cannot represent two
 * independently loaded cubes with the same X/Z coordinates at different Y levels. This class
 * keeps the vanilla draining machinery, but keys every container and every scheduling update by
 * the full packed {@link CubePos}.
 * </p>
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
