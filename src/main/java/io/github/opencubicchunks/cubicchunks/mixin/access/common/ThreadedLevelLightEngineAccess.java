package io.github.opencubicchunks.cubicchunks.mixin.access.common;

import net.minecraft.server.level.ThreadedLevelLightEngine;
import net.minecraft.world.level.ChunkPos;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

@Mixin(ThreadedLevelLightEngine.class)
public interface ThreadedLevelLightEngineAccess {
    @Invoker("updateChunkStatus") void cc_invokeUpdateChunkStatus(ChunkPos chunkPos);
}
