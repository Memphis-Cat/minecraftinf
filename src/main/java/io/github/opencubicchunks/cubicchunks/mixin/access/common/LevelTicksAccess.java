package io.github.opencubicchunks.cubicchunks.mixin.access.common;

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
    @Accessor("allContainers") Long2ObjectMap<LevelChunkTicks<T>> cc_getAllContainers();

    @Accessor("nextTickForContainer") Long2LongMap cc_getNextTickForContainer();

    @Accessor("alreadyRunThisTick") List<ScheduledTick<T>> cc_getAlreadyRunThisTick();

    @Accessor("toRunThisTick") Queue<ScheduledTick<T>> cc_getToRunThisTick();
}
