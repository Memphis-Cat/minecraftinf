package io.github.opencubicchunks.cubicchunks.mixin.dasm;

import org.spongepowered.asm.mixin.Mixin;

/** Fabric DASM routing targets for CubicChunks-owned interfaces. */
@Mixin(
    targets = {
        "io.github.opencubicchunks.cubicchunks.client.renderer.chunk.CCSectionCopy",
        "io.github.opencubicchunks.cubicchunks.server.level.CloTrackingView"
    },
    remap = false
)
public interface MixinFabricDasmInterfaceTargets {
}
