package io.github.opencubicchunks.cubicchunks.mixin.core.common.world.level.cube.status;

import io.github.opencubicchunks.cubicchunks.world.level.cube.status.CubeStep;
import org.spongepowered.asm.mixin.Mixin;

/**
 * Reserved mixin target for cube-step integration.
 *
 * <p>CubeStep is implemented directly on Fabric 26.2 and deliberately omits
 * vanilla chunk JFR profiling, matching the former redirect that returned
 * {@code null}. No bytecode injection is required.</p>
 */
@Mixin(CubeStep.class)
public class MixinCubeStep {
}
