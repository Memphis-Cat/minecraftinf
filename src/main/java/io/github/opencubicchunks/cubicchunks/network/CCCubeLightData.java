package io.github.opencubicchunks.cubicchunks.network;

import java.util.Arrays;
import java.util.Objects;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.api.CubicConstants;
import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.SectionPos;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.chunk.DataLayer;
import net.minecraft.world.level.lighting.LayerLightEventListener;
import net.minecraft.world.level.lighting.LevelLightEngine;

/** Complete block- and sky-light section data for one cube. */
public final class CCCubeLightData {
    private static final int DATA_LAYER_BYTES = DataLayer.SIZE;

    public static final StreamCodec<FriendlyByteBuf, CCCubeLightData> STREAM_CODEC = new StreamCodec<>() {
        @Override public CCCubeLightData decode(FriendlyByteBuf buffer) {
            return new CCCubeLightData(readLayers(buffer), readLayers(buffer));
        }

        @Override public void encode(FriendlyByteBuf buffer, CCCubeLightData value) {
            writeLayers(buffer, value.blockLight);
            writeLayers(buffer, value.skyLight);
        }
    };

    private final byte[][] blockLight;
    private final byte[][] skyLight;

    public CCCubeLightData(CubePos cubePos, LevelLightEngine lightEngine) {
        this(readLayers(cubePos, lightEngine, LightLayer.BLOCK), readLayers(cubePos, lightEngine, LightLayer.SKY));
    }

    private CCCubeLightData(byte[][] blockLight, byte[][] skyLight) {
        this.blockLight = cloneLayers(blockLight);
        this.skyLight = cloneLayers(skyLight);
    }

    public void apply(ClientLevel level, LevelCube cube) {
        LevelLightEngine lightEngine = level.getLightEngine();
        CubePos cubePos = cube.cc_getCubePos();
        for (int index = 0; index < CubicConstants.SECTION_COUNT; ++index) {
            SectionPos sectionPos = sectionPos(cubePos, index);
            lightEngine.updateSectionStatus(sectionPos, cube.getSection(index).hasOnlyAir());
            lightEngine.queueSectionData(LightLayer.BLOCK, sectionPos, new DataLayer(blockLight[index].clone()));
            lightEngine.queueSectionData(LightLayer.SKY, sectionPos, new DataLayer(skyLight[index].clone()));
            level.setSectionDirtyWithNeighbors(sectionPos.x(), sectionPos.y(), sectionPos.z());
        }
    }

    public static void clear(ClientLevel level, CubePos cubePos) {
        LevelLightEngine lightEngine = level.getLightEngine();
        for (int index = 0; index < CubicConstants.SECTION_COUNT; ++index) {
            SectionPos sectionPos = sectionPos(cubePos, index);
            lightEngine.queueSectionData(LightLayer.BLOCK, sectionPos, null);
            lightEngine.queueSectionData(LightLayer.SKY, sectionPos, null);
            lightEngine.updateSectionStatus(sectionPos, true);
            level.setSectionDirtyWithNeighbors(sectionPos.x(), sectionPos.y(), sectionPos.z());
        }
    }

    private static SectionPos sectionPos(CubePos cubePos, int index) {
        return SectionPos.of(
                Coords.cubeToSection(cubePos.getX(), Coords.indexToX(index)),
                Coords.cubeToSection(cubePos.getY(), Coords.indexToY(index)),
                Coords.cubeToSection(cubePos.getZ(), Coords.indexToZ(index)));
    }

    private static byte[][] readLayers(CubePos cubePos, LevelLightEngine lightEngine, LightLayer layer) {
        byte[][] output = new byte[CubicConstants.SECTION_COUNT][];
        LayerLightEventListener listener = lightEngine.getLayerListener(layer);
        for (int index = 0; index < output.length; ++index) {
            DataLayer dataLayer = listener.getDataLayerData(sectionPos(cubePos, index));
            output[index] = dataLayer == null ? new byte[DATA_LAYER_BYTES] : dataLayer.copy().getData().clone();
        }
        return output;
    }

    private static byte[][] readLayers(FriendlyByteBuf buffer) {
        int sectionCount = buffer.readVarInt();
        if (sectionCount != CubicConstants.SECTION_COUNT) {
            throw new IllegalArgumentException("Cube light section count mismatch: " + sectionCount);
        }
        byte[][] output = new byte[sectionCount][];
        for (int index = 0; index < sectionCount; ++index) {
            output[index] = buffer.readByteArray(DATA_LAYER_BYTES);
            if (output[index].length != DATA_LAYER_BYTES) {
                throw new IllegalArgumentException("Invalid cube light layer size " + output[index].length + " at section " + index);
            }
        }
        return output;
    }

    private static void writeLayers(FriendlyByteBuf buffer, byte[][] layers) {
        buffer.writeVarInt(layers.length);
        for (byte[] layer : layers) {
            buffer.writeByteArray(layer);
        }
    }

    private static byte[][] cloneLayers(byte[][] layers) {
        byte[][] output = new byte[layers.length][];
        for (int index = 0; index < layers.length; ++index) {
            output[index] = layers[index].clone();
        }
        return output;
    }

    @Override public boolean equals(Object other) {
        return other instanceof CCCubeLightData data && Arrays.deepEquals(this.blockLight, data.blockLight)
                && Arrays.deepEquals(this.skyLight, data.skyLight);
    }

    @Override public int hashCode() {
        return Objects.hash(Arrays.deepHashCode(this.blockLight), Arrays.deepHashCode(this.skyLight));
    }
}
