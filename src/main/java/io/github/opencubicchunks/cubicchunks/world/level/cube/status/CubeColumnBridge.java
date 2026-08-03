package io.github.opencubicchunks.cubicchunks.world.level.cube.status;

import java.util.concurrent.CompletableFuture;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.api.CubicConstants;
import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cubicchunks.server.level.CubicChunkMap;
import io.github.opencubicchunks.cubicchunks.world.level.cube.CubeAccess;
import it.unimi.dsi.fastutil.shorts.ShortArrayList;
import it.unimi.dsi.fastutil.shorts.ShortList;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.level.ChunkHolder;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.LevelChunkSection;
import net.minecraft.world.level.chunk.status.ChunkStatus;
import net.minecraft.world.level.chunk.status.WorldGenContext;
import net.minecraft.world.ticks.SavedTick;
import net.minecraft.world.ticks.SerializableTickContainer;
import net.minecraft.world.ticks.TickContainerAccess;

/**
 * Projects vanilla-generated chunk columns into one sparse cube.
 * <p>
 * Vanilla columns remain authoritative for structures and column heightmaps. The cube owns
 * the actual three-dimensional block sections, block entities and post-processing records for
 * its vertical interval.
 * </p>
 */
public final class CubeColumnBridge {
    private CubeColumnBridge() {}

    public static CompletableFuture<CubeAccess> synchronize(WorldGenContext context, ChunkStatus requiredStatus, CubeAccess cube) {
        CubePos cubePos = cube.cc_getCubePos();
        ChunkAccess[] columns = new ChunkAccess[CubicConstants.CHUNK_COUNT];
        for (int localX = 0; localX < CubicConstants.DIAMETER_IN_SECTIONS; ++localX) {
            for (int localZ = 0; localZ < CubicConstants.DIAMETER_IN_SECTIONS; ++localZ) {
                int chunkX = Coords.cubeToSection(cubePos.getX(), localX);
                int chunkZ = Coords.cubeToSection(cubePos.getZ(), localZ);
                ChunkHolder holder = ((CubicChunkMap) context.level().getChunkSource().chunkMap)
                        .cc_getVisibleChunkIfPresent(new ChunkPos(chunkX, chunkZ).pack());
                ChunkAccess column = holder == null ? null : holder.getChunkIfPresentUnchecked(requiredStatus);
                if (column == null) {
                    throw new IllegalStateException("Scheduled vanilla column " + new ChunkPos(chunkX, chunkZ) + " was unavailable at "
                            + requiredStatus + " while projecting cube " + cubePos);
                }
                columns[columnIndex(localX, localZ)] = column;
            }
        }

        copySections(context, cube, columns);
        if (requiredStatus.isOrAfter(ChunkStatus.FEATURES)) {
            copyPostProcessing(cube, columns);
            copyBlockEntities(context, cube, columns);
            copyScheduledTicks(context, cube, columns);
        }
        if (requiredStatus.isOrAfter(ChunkStatus.LIGHT)) {
            boolean lightCorrect = true;
            for (ChunkAccess column : columns) {
                lightCorrect &= column.isLightCorrect();
            }
            cube.setLightCorrect(lightCorrect);
        }
        cube.markUnsaved();
        return CompletableFuture.completedFuture(cube);
    }

    static int sourceSectionY(CubePos cubePos, int localSectionY) {
        return Coords.cubeToSection(cubePos.getY(), localSectionY);
    }

    static int targetSectionIndex(int localSectionX, int localSectionY, int localSectionZ) {
        return Coords.sectionToIndex(localSectionX, localSectionY, localSectionZ);
    }

    static int columnIndex(int localSectionX, int localSectionZ) {
        return Coords.columnToColumnIndex(localSectionX, localSectionZ);
    }

    private static void copySections(WorldGenContext context, CubeAccess cube, ChunkAccess[] columns) {
        Registry<Biome> biomeRegistry = context.level().registryAccess().lookupOrThrow(Registries.BIOME);
        LevelChunkSection[] targetSections = cube.getSections();
        CubePos cubePos = cube.cc_getCubePos();

        for (int localX = 0; localX < CubicConstants.DIAMETER_IN_SECTIONS; ++localX) {
            for (int localZ = 0; localZ < CubicConstants.DIAMETER_IN_SECTIONS; ++localZ) {
                ChunkAccess column = columns[columnIndex(localX, localZ)];
                LevelChunkSection[] sourceSections = column.getSections();
                for (int localY = 0; localY < CubicConstants.DIAMETER_IN_SECTIONS; ++localY) {
                    int sectionY = sourceSectionY(cubePos, localY);
                    int sourceIndex = column.getSectionIndexFromSectionY(sectionY);
                    int targetIndex = targetSectionIndex(localX, localY, localZ);
                    targetSections[targetIndex] = sourceIndex >= 0 && sourceIndex < sourceSections.length ? sourceSections[sourceIndex].copy()
                            : new LevelChunkSection(biomeRegistry);
                }
            }
        }
    }

    private static void copyPostProcessing(CubeAccess cube, ChunkAccess[] columns) {
        CubePos cubePos = cube.cc_getCubePos();
        ShortList[] target = cube.getPostProcessing();
        for (int localX = 0; localX < CubicConstants.DIAMETER_IN_SECTIONS; ++localX) {
            for (int localZ = 0; localZ < CubicConstants.DIAMETER_IN_SECTIONS; ++localZ) {
                ChunkAccess column = columns[columnIndex(localX, localZ)];
                ShortList[] source = column.getPostProcessing();
                for (int localY = 0; localY < CubicConstants.DIAMETER_IN_SECTIONS; ++localY) {
                    int sourceIndex = column.getSectionIndexFromSectionY(sourceSectionY(cubePos, localY));
                    if (sourceIndex < 0 || sourceIndex >= source.length || source[sourceIndex] == null || source[sourceIndex].isEmpty()) {
                        continue;
                    }
                    target[targetSectionIndex(localX, localY, localZ)] = new ShortArrayList(source[sourceIndex]);
                }
            }
        }
    }

    private static void copyScheduledTicks(WorldGenContext context, CubeAccess cube, ChunkAccess[] columns) {
        long gameTime = context.level().getGameTime();
        long blockSubTickOrder = 0L;
        long fluidSubTickOrder = 0L;
        for (ChunkAccess column : columns) {
            blockSubTickOrder = copyScheduledTicks(gameTime, cube.cc_getCubePos(), cube.getBlockTicks(), column.getBlockTicks(), blockSubTickOrder);
            fluidSubTickOrder = copyScheduledTicks(gameTime, cube.cc_getCubePos(), cube.getFluidTicks(), column.getFluidTicks(), fluidSubTickOrder);
        }
    }

    @SuppressWarnings("unchecked")
    private static <T> long copyScheduledTicks(
            long gameTime, CubePos cubePos, TickContainerAccess<T> target, TickContainerAccess<T> source, long subTickOrder
    ) {
        if (!(source instanceof SerializableTickContainer<?> rawSerializable)) {
            return subTickOrder;
        }
        long nextSubTickOrder = subTickOrder;
        SerializableTickContainer<T> serializable = (SerializableTickContainer<T>) rawSerializable;
        for (SavedTick<T> tick : serializable.pack(gameTime)) {
            BlockPos position = tick.pos();
            if (position.getX() < cubePos.minCubeX() || position.getX() > cubePos.maxCubeX() || position.getY() < cubePos.minCubeY()
                    || position.getY() > cubePos.maxCubeY() || position.getZ() < cubePos.minCubeZ() || position.getZ() > cubePos.maxCubeZ()) {
                continue;
            }
            target.schedule(tick.unpack(gameTime, nextSubTickOrder++));
        }
        return nextSubTickOrder;
    }

    private static void copyBlockEntities(WorldGenContext context, CubeAccess cube, ChunkAccess[] columns) {
        int minY = cube.cc_getCubePos().minCubeY();
        int maxY = cube.cc_getCubePos().maxCubeY();
        for (ChunkAccess column : columns) {
            for (BlockPos blockPos : column.getBlockEntitiesPos()) {
                if (blockPos.getY() < minY || blockPos.getY() > maxY) {
                    continue;
                }
                var tag = column.getBlockEntityNbtForSaving(blockPos, context.level().registryAccess());
                if (tag != null) {
                    cube.setBlockEntityNbt(tag.copy());
                }
            }
        }
    }
}
