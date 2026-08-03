package io.github.opencubicchunks.cubicchunks.world.level.chunk.status;

import java.util.concurrent.CompletableFuture;

import com.mojang.logging.LogUtils;
import io.github.notstirred.dasm.api.annotations.Dasm;
import io.github.notstirred.dasm.api.annotations.redirect.redirects.AddFieldToSets;
import io.github.notstirred.dasm.api.annotations.redirect.redirects.AddTransformToSets;
import io.github.notstirred.dasm.api.annotations.selector.Ref;
import io.github.notstirred.dasm.api.annotations.transform.TransformFromMethod;
import io.github.opencubicchunks.cubicchunks.mixin.dasmsets.ChunkInCubicContextSet;
import io.github.opencubicchunks.cubicchunks.world.level.cube.status.CubeStatusTasks;
import net.minecraft.server.level.GenerationChunkHolder;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.StaticCache2D;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.status.ChunkStatusTasks;
import net.minecraft.world.level.chunk.status.ChunkStep;
import net.minecraft.world.level.chunk.status.WorldGenContext;
import net.minecraft.world.level.storage.ValueInput;
import org.slf4j.Logger;

/**
 * Equivalent of {@link ChunkStatusTasks} for chunks in cubic worlds.
 * <p>
 * Vanilla columns remain authoritative for terrain-generation metadata. Cubes project the
 * generated sections into sparse three-dimensional storage instead of maintaining a second
 * terrain generator.
 * </p>
 * <p>
 * See also {@link CubeStatusTasks} for the cube projection tasks.
 * </p>
 */
@Dasm(ChunkInCubicContextSet.class)
public final class CCChunkStatusTasks {
    @AddFieldToSets(containers = ChunkInCubicContextSet.ChunkStatusTasks_to_CCChunkStatusTasks_redirects.class, field = "LOGGER:Lorg/slf4j/Logger;")
    private static final Logger LOGGER = LogUtils.getLogger();

    private CCChunkStatusTasks() {}

    @AddTransformToSets(ChunkInCubicContextSet.ChunkStatusTasks_to_CCChunkStatusTasks_redirects.class)
    @TransformFromMethod(owner = @Ref(ChunkStatusTasks.class), value = "isLighted(Lnet/minecraft/world/level/chunk/ChunkAccess;)Z")
    private static native boolean isLighted(ChunkAccess chunk);

    @AddTransformToSets(ChunkInCubicContextSet.ChunkStatusTasks_to_CCChunkStatusTasks_redirects.class)
    @TransformFromMethod(owner = @Ref(ChunkStatusTasks.class), value = "passThrough(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static native CompletableFuture<ChunkAccess> passThrough(
            WorldGenContext worldGenContext, ChunkStep step, StaticCache2D<GenerationChunkHolder> cache, ChunkAccess chunk
    );

    @AddTransformToSets(ChunkInCubicContextSet.ChunkStatusTasks_to_CCChunkStatusTasks_redirects.class)
    @TransformFromMethod(owner = @Ref(ChunkStatusTasks.class), value = "generateStructureStarts(Lnet/minecraft/world/level/chunk/status/WorldGenContext;"
            + "Lnet/minecraft/world/level/chunk/status/ChunkStep;Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)"
            + "Ljava/util/concurrent/CompletableFuture;")
    public static native CompletableFuture<ChunkAccess> generateStructureStarts(
            WorldGenContext worldGenContext, ChunkStep step, StaticCache2D<GenerationChunkHolder> cache, ChunkAccess chunk
    );

    @AddTransformToSets(ChunkInCubicContextSet.ChunkStatusTasks_to_CCChunkStatusTasks_redirects.class)
    @TransformFromMethod(owner = @Ref(ChunkStatusTasks.class), value = "loadStructureStarts(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static native CompletableFuture<ChunkAccess> loadStructureStarts(
            WorldGenContext worldGenContext, ChunkStep step, StaticCache2D<GenerationChunkHolder> cache, ChunkAccess chunk
    );

    @AddTransformToSets(ChunkInCubicContextSet.ChunkStatusTasks_to_CCChunkStatusTasks_redirects.class)
    @TransformFromMethod(owner = @Ref(ChunkStatusTasks.class), value = "generateStructureReferences(Lnet/minecraft/world/level/chunk/status/WorldGenContext;"
            + "Lnet/minecraft/world/level/chunk/status/ChunkStep;Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)"
            + "Ljava/util/concurrent/CompletableFuture;")
    public static native CompletableFuture<ChunkAccess> generateStructureReferences(
            WorldGenContext worldGenContext, ChunkStep step, StaticCache2D<GenerationChunkHolder> cache, ChunkAccess chunk
    );

    @AddTransformToSets(ChunkInCubicContextSet.ChunkStatusTasks_to_CCChunkStatusTasks_redirects.class)
    @TransformFromMethod(owner = @Ref(ChunkStatusTasks.class), value = "generateBiomes(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static native CompletableFuture<ChunkAccess> generateBiomes(
            WorldGenContext worldGenContext, ChunkStep step, StaticCache2D<GenerationChunkHolder> cache, ChunkAccess chunk
    );

    @AddTransformToSets(ChunkInCubicContextSet.ChunkStatusTasks_to_CCChunkStatusTasks_redirects.class)
    @TransformFromMethod(owner = @Ref(ChunkStatusTasks.class), value = "generateNoise(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static native CompletableFuture<ChunkAccess> generateNoise(
            WorldGenContext worldGenContext, ChunkStep step, StaticCache2D<GenerationChunkHolder> cache, ChunkAccess chunk
    );

    @AddTransformToSets(ChunkInCubicContextSet.ChunkStatusTasks_to_CCChunkStatusTasks_redirects.class)
    @TransformFromMethod(owner = @Ref(ChunkStatusTasks.class), value = "generateSurface(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static native CompletableFuture<ChunkAccess> generateSurface(
            WorldGenContext worldGenContext, ChunkStep step, StaticCache2D<GenerationChunkHolder> cache, ChunkAccess chunk
    );

    @AddTransformToSets(ChunkInCubicContextSet.ChunkStatusTasks_to_CCChunkStatusTasks_redirects.class)
    @TransformFromMethod(owner = @Ref(ChunkStatusTasks.class), value = "generateCarvers(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static native CompletableFuture<ChunkAccess> generateCarvers(
            WorldGenContext worldGenContext, ChunkStep step, StaticCache2D<GenerationChunkHolder> cache, ChunkAccess chunk
    );

    @AddTransformToSets(ChunkInCubicContextSet.ChunkStatusTasks_to_CCChunkStatusTasks_redirects.class)
    @TransformFromMethod(owner = @Ref(ChunkStatusTasks.class), value = "generateFeatures(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static native CompletableFuture<ChunkAccess> generateFeatures(
            WorldGenContext worldGenContext, ChunkStep step, StaticCache2D<GenerationChunkHolder> cache, ChunkAccess chunk
    );

    @AddTransformToSets(ChunkInCubicContextSet.ChunkStatusTasks_to_CCChunkStatusTasks_redirects.class)
    @TransformFromMethod(owner = @Ref(ChunkStatusTasks.class), value = "initializeLight(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static native CompletableFuture<ChunkAccess> initializeLight(
            WorldGenContext worldGenContext, ChunkStep step, StaticCache2D<GenerationChunkHolder> cache, ChunkAccess chunk
    );

    @AddTransformToSets(ChunkInCubicContextSet.ChunkStatusTasks_to_CCChunkStatusTasks_redirects.class)
    @TransformFromMethod(owner = @Ref(ChunkStatusTasks.class), value = "light(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static native CompletableFuture<ChunkAccess> light(
            WorldGenContext worldGenContext, ChunkStep step, StaticCache2D<GenerationChunkHolder> cache, ChunkAccess chunk
    );

    @AddTransformToSets(ChunkInCubicContextSet.ChunkStatusTasks_to_CCChunkStatusTasks_redirects.class)
    @TransformFromMethod(owner = @Ref(ChunkStatusTasks.class), value = "generateSpawn(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static native CompletableFuture<ChunkAccess> generateSpawn(
            WorldGenContext worldGenContext, ChunkStep step, StaticCache2D<GenerationChunkHolder> cache, ChunkAccess chunk
    );

    @AddTransformToSets(ChunkInCubicContextSet.ChunkStatusTasks_to_CCChunkStatusTasks_redirects.class)
    @TransformFromMethod(owner = @Ref(ChunkStatusTasks.class), value = "full(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static native CompletableFuture<ChunkAccess> full(
            WorldGenContext worldGenContext, ChunkStep step, StaticCache2D<GenerationChunkHolder> cache, ChunkAccess chunk
    );

    @AddTransformToSets(ChunkInCubicContextSet.ChunkStatusTasks_to_CCChunkStatusTasks_redirects.class)
    @TransformFromMethod(owner = @Ref(ChunkStatusTasks.class), value = "postLoadProtoChunk(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/level/storage/ValueInput$ValueInputList;)V")
    private static native void postLoadProtoChunk(ServerLevel level, ValueInput.ValueInputList entityTags);
}
