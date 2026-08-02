package io.github.opencubicchunks.cubicchunks.server.level;

import javax.annotation.Nullable;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.world.level.cube.CubeAccess;
import io.github.opencubicchunks.cubicchunks.world.level.cube.ImposterProtoCube;
import net.minecraft.world.level.chunk.status.ChunkStatus;

public interface GenerationCloHolder {
    CloPos cc_getCloPos();

    @Nullable CubePos cc_getCubePos();

    void cc_replaceProtoCube(ImposterProtoCube cube);

    @Nullable CubeAccess cc_getCubeIfPresentUnchecked(ChunkStatus status);
}
