package io.github.opencubicchunks.cubicchunks.mixin.core.dasm;

import org.spongepowered.asm.mixin.Mixin;

/**
 * Empty Mixin targets that route CubicChunks-owned DASM classes through the
 * Mixin extension pipeline on Fabric. Vanilla targets already enter that
 * pipeline through their functional mixins; these classes do not.
 */
@Mixin(
    targets = {
        "io.github.opencubicchunks.cubicchunks.client.multiplayer.ClientCubeCache$Storage",
        "io.github.opencubicchunks.cubicchunks.server.level.CloTrackingView$Positioned",
        "io.github.opencubicchunks.cubicchunks.server.level.CubeLevel",
        "io.github.opencubicchunks.cubicchunks.world.level.chunk.status.CCChunkStatusTasks",
        "io.github.opencubicchunks.cubicchunks.world.level.cube.CubeAccess",
        "io.github.opencubicchunks.cubicchunks.world.level.cube.EmptyLevelCube",
        "io.github.opencubicchunks.cubicchunks.world.level.cube.ImposterProtoCube",
        "io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube",
        "io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube$BoundTickingBlockEntity",
        "io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube$RebindableTickingBlockEntityWrapper",
        "io.github.opencubicchunks.cubicchunks.world.level.cube.ProtoCube",
        "io.github.opencubicchunks.cubicchunks.world.level.cube.status.CubePyramid",
        "io.github.opencubicchunks.cubicchunks.world.level.cube.status.CubePyramid$Builder",
        "io.github.opencubicchunks.cubicchunks.world.level.cube.status.CubeStatusTasks",
        "io.github.opencubicchunks.cubicchunks.world.level.cube.status.CubeStep",
        "io.github.opencubicchunks.cubicchunks.world.level.cube.status.CubeStep$Builder"
    },
    remap = false
)
public abstract class MixinFabricDasmClassTargets {
}
