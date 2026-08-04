package io.github.opencubicchunks.cubicchunks.world.level.cube.status;

import java.util.concurrent.CompletableFuture;

import com.mojang.logging.LogUtils;
import io.github.notstirred.dasm.api.annotations.Dasm;
import io.github.notstirred.dasm.api.annotations.redirect.redirects.AddFieldToSets;
import io.github.notstirred.dasm.api.annotations.redirect.redirects.AddMethodToSets;
import io.github.notstirred.dasm.api.annotations.redirect.redirects.AddTransformToSets;
import io.github.notstirred.dasm.api.annotations.selector.Ref;
import io.github.notstirred.dasm.api.annotations.transform.TransformFromMethod;
import io.github.opencubicchunks.cubicchunks.mixin.dasmsets.ChunkToCubeSet;
import io.github.opencubicchunks.cubicchunks.util.StaticCache3D;
import io.github.opencubicchunks.cubicchunks.world.level.chunk.status.CCChunkStatusTasks;
import io.github.opencubicchunks.cubicchunks.world.level.cube.CubeAccess;
import net.minecraft.server.level.GenerationChunkHolder;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.level.chunk.status.ChunkStatus;
import net.minecraft.world.level.chunk.status.ChunkStatusTasks;
import net.minecraft.world.level.chunk.status.WorldGenContext;
import net.minecraft.world.level.storage.ValueInput;
import org.slf4j.Logger;

/**
 * Equivalent of {@link ChunkStatusTasks} for sparse cube generation.
 * <p>
 * Each generation stage waits for the matching vanilla chunk-column stage and projects the
 * generated vertical sections into the cube. This preserves the configured vanilla generator,
 * biomes, carvers and features instead of maintaining test terrain.
 * </p>
 * <p>
 * See also {@link CCChunkStatusTasks} for the real column generation tasks used in cubic worlds.
 * </p>
 */
@Dasm(ChunkToCubeSet.class)
public final class CubeStatusTasks {
    private CubeStatusTasks() {}

    @AddFieldToSets(containers = ChunkToCubeSet.ChunkStatusTasks_to_CubeStatusTasks_redirects.class, field = "LOGGER:Lorg/slf4j/Logger;")
    private static final Logger LOGGER = LogUtils.getLogger();

    @AddTransformToSets(ChunkToCubeSet.ChunkStatusTasks_to_CubeStatusTasks_redirects.class)
    @TransformFromMethod(owner = @Ref(ChunkStatusTasks.class), value = "isLighted(Lnet/minecraft/world/level/chunk/ChunkAccess;)Z")
    private static native boolean isLighted(CubeAccess cube);

    @AddMethodToSets(containers = ChunkToCubeSet.ChunkStatusTasks_to_CubeStatusTasks_redirects.class, method = "passThrough(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static CompletableFuture<CubeAccess> passThrough(
            WorldGenContext worldGenContext, CubeStep step, StaticCache3D<GenerationChunkHolder> cache, CubeAccess cube
    ) {
        return CompletableFuture.completedFuture(cube);
    }

    @AddMethodToSets(containers = ChunkToCubeSet.ChunkStatusTasks_to_CubeStatusTasks_redirects.class, method = "generateStructureStarts(Lnet/minecraft/world/level/chunk/status/WorldGenContext;"
            + "Lnet/minecraft/world/level/chunk/status/ChunkStep;Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)"
            + "Ljava/util/concurrent/CompletableFuture;")
    public static CompletableFuture<CubeAccess> generateStructureStarts(
            WorldGenContext worldGenContext, CubeStep step, StaticCache3D<GenerationChunkHolder> cache, CubeAccess cube
    ) {
        return CubeColumnBridge.synchronize(worldGenContext, ChunkStatus.STRUCTURE_STARTS, cube);
    }

    @AddMethodToSets(containers = ChunkToCubeSet.ChunkStatusTasks_to_CubeStatusTasks_redirects.class, method = "loadStructureStarts(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static CompletableFuture<CubeAccess> loadStructureStarts(
            WorldGenContext worldGenContext, CubeStep step, StaticCache3D<GenerationChunkHolder> cache, CubeAccess cube
    ) {
        return CubeColumnBridge.synchronize(worldGenContext, ChunkStatus.STRUCTURE_STARTS, cube);
    }

    @AddMethodToSets(containers = ChunkToCubeSet.ChunkStatusTasks_to_CubeStatusTasks_redirects.class, method = "generateStructureReferences(Lnet/minecraft/world/level/chunk/status/WorldGenContext;"
            + "Lnet/minecraft/world/level/chunk/status/ChunkStep;Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)"
            + "Ljava/util/concurrent/CompletableFuture;")
    public static CompletableFuture<CubeAccess> generateStructureReferences(
            WorldGenContext worldGenContext, CubeStep step, StaticCache3D<GenerationChunkHolder> cache, CubeAccess cube
    ) {
        return CubeColumnBridge.synchronize(worldGenContext, ChunkStatus.STRUCTURE_REFERENCES, cube);
    }

    @AddMethodToSets(containers = ChunkToCubeSet.ChunkStatusTasks_to_CubeStatusTasks_redirects.class, method = "generateBiomes(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static CompletableFuture<CubeAccess> generateBiomes(
            WorldGenContext worldGenContext, CubeStep step, StaticCache3D<GenerationChunkHolder> cache, CubeAccess cube
    ) {
        return CubeColumnBridge.synchronize(worldGenContext, ChunkStatus.BIOMES, cube);
    }

    @AddMethodToSets(containers = ChunkToCubeSet.ChunkStatusTasks_to_CubeStatusTasks_redirects.class, method = "generateNoise(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static CompletableFuture<CubeAccess> generateNoise(
            WorldGenContext worldGenContext, CubeStep step, StaticCache3D<GenerationChunkHolder> cache, CubeAccess cube
    ) {
        return CubeColumnBridge.synchronize(worldGenContext, ChunkStatus.NOISE, cube);
    }

    @AddMethodToSets(containers = ChunkToCubeSet.ChunkStatusTasks_to_CubeStatusTasks_redirects.class, method = "generateSurface(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static CompletableFuture<CubeAccess> generateSurface(
            WorldGenContext worldGenContext, CubeStep step, StaticCache3D<GenerationChunkHolder> cache, CubeAccess cube
    ) {
        return CubeColumnBridge.synchronize(worldGenContext, ChunkStatus.SURFACE, cube);
    }

    @AddMethodToSets(containers = ChunkToCubeSet.ChunkStatusTasks_to_CubeStatusTasks_redirects.class, method = "generateCarvers(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static CompletableFuture<CubeAccess> generateCarvers(
            WorldGenContext worldGenContext, CubeStep step, StaticCache3D<GenerationChunkHolder> cache, CubeAccess cube
    ) {
        return CubeColumnBridge.synchronize(worldGenContext, ChunkStatus.CARVERS, cube);
    }

    @AddMethodToSets(containers = ChunkToCubeSet.ChunkStatusTasks_to_CubeStatusTasks_redirects.class, method = "generateFeatures(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static CompletableFuture<CubeAccess> generateFeatures(
            WorldGenContext worldGenContext, CubeStep step, StaticCache3D<GenerationChunkHolder> cache, CubeAccess cube
    ) {
        return CubeColumnBridge.synchronize(worldGenContext, ChunkStatus.FEATURES, cube);
    }

    @AddMethodToSets(containers = ChunkToCubeSet.ChunkStatusTasks_to_CubeStatusTasks_redirects.class, method = "initializeLight(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static CompletableFuture<CubeAccess> initializeLight(
            WorldGenContext worldGenContext, CubeStep step, StaticCache3D<GenerationChunkHolder> cache, CubeAccess cube
    ) {
        return CubeColumnBridge.synchronize(worldGenContext, ChunkStatus.INITIALIZE_LIGHT, cube);
    }

    @AddMethodToSets(containers = ChunkToCubeSet.ChunkStatusTasks_to_CubeStatusTasks_redirects.class, method = "light(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static CompletableFuture<CubeAccess> light(
            WorldGenContext worldGenContext, CubeStep step, StaticCache3D<GenerationChunkHolder> cache, CubeAccess cube
    ) {
        return CubeColumnBridge.synchronize(worldGenContext, ChunkStatus.LIGHT, cube);
    }

    @AddMethodToSets(containers = ChunkToCubeSet.ChunkStatusTasks_to_CubeStatusTasks_redirects.class, method = "generateSpawn(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static CompletableFuture<CubeAccess> generateSpawn(
            WorldGenContext worldGenContext, CubeStep step, StaticCache3D<GenerationChunkHolder> cache, CubeAccess cube
    ) {
        return CubeColumnBridge.synchronize(worldGenContext, ChunkStatus.SPAWN, cube);
    }

    @AddTransformToSets(ChunkToCubeSet.ChunkStatusTasks_to_CubeStatusTasks_redirects.class)
    @TransformFromMethod(owner = @Ref(ChunkStatusTasks.class), value = "full(Lnet/minecraft/world/level/chunk/status/WorldGenContext;Lnet/minecraft/world/level/chunk/status/ChunkStep;"
            + "Lnet/minecraft/util/StaticCache2D;Lnet/minecraft/world/level/chunk/ChunkAccess;)Ljava/util/concurrent/CompletableFuture;")
    public static native CompletableFuture<CubeAccess> full(
            WorldGenContext worldGenContext, CubeStep step, StaticCache3D<GenerationChunkHolder> cache, CubeAccess cube
    );

    private static void postLoadProtoCube(ServerLevel level, ValueInput.ValueInputList entityTags) {
        if (!entityTags.isEmpty()) {
            level.addWorldGenChunkEntities(EntityType.loadEntitiesRecursive(entityTags, level, EntitySpawnReason.LOAD));
        }
    }
}
