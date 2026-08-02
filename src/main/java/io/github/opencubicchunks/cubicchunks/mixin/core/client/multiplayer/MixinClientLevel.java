package io.github.opencubicchunks.cubicchunks.mixin.core.client.multiplayer;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.api.CubicConstants;
import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cubicchunks.client.multiplayer.ClientCubeAvailability;
import io.github.opencubicchunks.cubicchunks.client.multiplayer.ClientCubeCache;
import io.github.opencubicchunks.cubicchunks.client.multiplayer.CubicClientLevel;
import io.github.opencubicchunks.cubicchunks.mixin.core.common.world.level.MixinLevel;
import it.unimi.dsi.fastutil.longs.Long2IntOpenHashMap;
import it.unimi.dsi.fastutil.objects.Object2ObjectArrayMap;
import net.minecraft.client.color.block.BlockTintCache;
import net.minecraft.client.multiplayer.ClientChunkCache;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.ColorResolver;
import net.minecraft.world.level.entity.TransientEntitySectionManager;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;

@Mixin(ClientLevel.class)
public abstract class MixinClientLevel extends MixinLevel implements CubicClientLevel {
    @Shadow @Final private ClientChunkCache chunkSource;
    @Shadow @Final private TransientEntitySectionManager<Entity> entityStorage;
    @Shadow @Final private Object2ObjectArrayMap<ColorResolver, BlockTintCache> tintCaches;

    @Unique
    private final Long2IntOpenHashMap cc_loadedCubeColumns = new Long2IntOpenHashMap();

    @Override public boolean cc_hasCube(int cubeX, int cubeY, int cubeZ) {
        return ClientCubeAvailability.hasCube((ClientCubeCache) this.chunkSource, cubeX, cubeY, cubeZ);
    }

    @Override public void cc_onCubeLoaded(CubePos cubePos) {
        for (int dx = 0; dx < CubicConstants.DIAMETER_IN_SECTIONS; ++dx) {
            for (int dz = 0; dz < CubicConstants.DIAMETER_IN_SECTIONS; ++dz) {
                int chunkX = Coords.cubeToSection(cubePos.getX(), dx);
                int chunkZ = Coords.cubeToSection(cubePos.getZ(), dz);
                this.tintCaches.forEach((resolver, cache) -> cache.invalidateForChunk(chunkX, chunkZ));
                long chunkPosLong = ChunkPos.asLong(chunkX, chunkZ);
                int previousCount = this.cc_loadedCubeColumns.addTo(chunkPosLong, 1);
                if (previousCount == 0) {
                    ChunkPos chunkPos = new ChunkPos(chunkX, chunkZ);
                    this.entityStorage.startTicking(chunkPos);
                    this.chunkSource.getLightEngine().setLightEnabled(chunkPos, true);
                }
            }
        }
    }

    @Override public void cc_onCubeUnloaded(CubePos cubePos) {
        for (int dx = 0; dx < CubicConstants.DIAMETER_IN_SECTIONS; ++dx) {
            for (int dz = 0; dz < CubicConstants.DIAMETER_IN_SECTIONS; ++dz) {
                int chunkX = Coords.cubeToSection(cubePos.getX(), dx);
                int chunkZ = Coords.cubeToSection(cubePos.getZ(), dz);
                long chunkPosLong = ChunkPos.asLong(chunkX, chunkZ);
                int previousCount = this.cc_loadedCubeColumns.get(chunkPosLong);
                if (previousCount <= 1) {
                    this.cc_loadedCubeColumns.remove(chunkPosLong);
                    ChunkPos chunkPos = new ChunkPos(chunkX, chunkZ);
                    this.chunkSource.getLightEngine().setLightEnabled(chunkPos, false);
                    this.entityStorage.stopTicking(chunkPos);
                } else {
                    this.cc_loadedCubeColumns.put(chunkPosLong, previousCount - 1);
                }
            }
        }
    }

    @Override public ClientCubeCache cc_getCubeSource() {
        return (ClientCubeCache) this.chunkSource;
    }
}
