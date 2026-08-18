package io.github.opencubicchunks.cubicchunks.server.network;

import java.util.Comparator;
import java.util.function.ToIntFunction;

import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.world.level.chunklike.LevelClo;

/** Stable send ordering that keeps vanilla columns ahead of dependent cubes. */
public final class CloSendOrder {
    private CloSendOrder() {}

    public static Comparator<Long> encodedPositions(ToIntFunction<Long> vanillaOrder) {
        return Comparator.comparingInt((Long packed) -> CloPos.isChunk(packed) ? 0 : 1).thenComparingInt(vanillaOrder)
                .thenComparingLong(Long::longValue);
    }

    public static Comparator<LevelClo> loadedClos(ToIntFunction<LevelClo> vanillaOrder) {
        return Comparator.comparingInt((LevelClo clo) -> clo.cc_getCloPos().isChunk() ? 0 : 1).thenComparingInt(vanillaOrder)
                .thenComparingLong(clo -> clo.cc_getCloPos().toLong());
    }
}
