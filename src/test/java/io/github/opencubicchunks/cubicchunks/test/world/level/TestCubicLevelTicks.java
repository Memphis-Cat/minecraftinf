package io.github.opencubicchunks.cubicchunks.test.world.level;

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
