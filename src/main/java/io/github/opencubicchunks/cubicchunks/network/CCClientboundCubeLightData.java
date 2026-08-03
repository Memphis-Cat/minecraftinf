package io.github.opencubicchunks.cubicchunks.network;

import java.util.Arrays;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.api.CubicConstants;
import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import io.netty.handler.codec.DecoderException;
import io.netty.handler.codec.EncoderException;
import net.minecraft.core.SectionPos;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.chunk.DataLayer;
import net.minecraft.world.level.lighting.LevelLightEngine;
import org.jspecify.annotations.Nullable;

/** Complete block- and sky-light payload for every section contained by one cube. */
public final class CCClientboundCubeLightData {
    private static final int DATA_LAYER_BYTES = 2048;

    public static final StreamCodec<FriendlyByteBuf, CCClientboundCubeLightData> STREAM_CODEC = new StreamCodec<>() {
        @Override public CCClientboundCubeLightData decode(FriendlyByteBuf input) {
            return new CCClientboundCubeLightData(input);
        }

        @Override public void encode(FriendlyByteBuf output, CCClientboundCubeLightData value) {
            value.write(output);
        }
    };

    private final byte[][] blockLight;
    private final byte[][] skyLight;

    public CCClientboundCubeLightData(LevelCube cube, LevelLightEngine lightEngine) {
        this(capture(cube.cc_getCubePos(), lightEngine, LightLayer.BLOCK), capture(cube.cc_getCubePos(), lightEngine, LightLayer.SKY));
    }

    CCClientboundCubeLightData(byte[][] blockLight, byte[][] skyLight) {
        this.blockLight = copyAndValidate(blockLight, "block");
        this.skyLight = copyAndValidate(skyLight, "sky");
    }

    private CCClientboundCubeLightData(FriendlyByteBuf input) {
        int sectionCount = input.readVarInt();
        if (sectionCount != CubicConstants.SECTION_COUNT) {
            throw new DecoderException("Invalid cube light section count " + sectionCount + "; expected " + CubicConstants.SECTION_COUNT);
        }
        this.blockLight = new byte[sectionCount][];
        this.skyLight = new byte[sectionCount][];
        for (int index = 0; index < sectionCount; index++) {
            this.blockLight[index] = readLayer(input);
            this.skyLight[index] = readLayer(input);
        }
    }

    private void write(FriendlyByteBuf output) {
        if (this.blockLight.length != CubicConstants.SECTION_COUNT || this.skyLight.length != CubicConstants.SECTION_COUNT) {
            throw new EncoderException("Cube light payload has an invalid section count");
        }
        output.writeVarInt(CubicConstants.SECTION_COUNT);
        for (int index = 0; index < CubicConstants.SECTION_COUNT; index++) {
            writeLayer(output, this.blockLight[index]);
            writeLayer(output, this.skyLight[index]);
        }
    }

    public void apply(CubePos cubePos, LevelLightEngine lightEngine) {
        for (int index = 0; index < CubicConstants.SECTION_COUNT; index++) {
            SectionPos sectionPos = sectionPos(cubePos, index);
            lightEngine.queueSectionData(LightLayer.BLOCK, sectionPos, toDataLayer(this.blockLight[index]));
            lightEngine.queueSectionData(LightLayer.SKY, sectionPos, toDataLayer(this.skyLight[index]));
        }
    }

    byte @Nullable [] blockLight(int index) {
        return copyNullable(this.blockLight[index]);
    }

    byte @Nullable [] skyLight(int index) {
        return copyNullable(this.skyLight[index]);
    }

    private static byte[][] capture(CubePos cubePos, LevelLightEngine lightEngine, LightLayer layer) {
        byte[][] result = new byte[CubicConstants.SECTION_COUNT][];
        var listener = lightEngine.getLayerListener(layer);
        for (int index = 0; index < result.length; index++) {
            DataLayer data = listener.getDataLayerData(sectionPos(cubePos, index));
            result[index] = data == null ? null : data.getData().clone();
        }
        return result;
    }

    private static SectionPos sectionPos(CubePos cubePos, int index) {
        return SectionPos.of(
                Coords.cubeToSection(cubePos.getX(), Coords.indexToX(index)),
                Coords.cubeToSection(cubePos.getY(), Coords.indexToY(index)),
                Coords.cubeToSection(cubePos.getZ(), Coords.indexToZ(index))
        );
    }

    private static byte[][] copyAndValidate(byte[][] source, String layerName) {
        if (source.length != CubicConstants.SECTION_COUNT) {
            throw new IllegalArgumentException(layerName + " light contains " + source.length + " sections; expected " + CubicConstants.SECTION_COUNT);
        }
        byte[][] result = new byte[source.length][];
        for (int index = 0; index < source.length; index++) {
            byte[] data = source[index];
            if (data != null && data.length != DATA_LAYER_BYTES) {
                throw new IllegalArgumentException(layerName + " light section " + index + " contains " + data.length
                        + " bytes; expected " + DATA_LAYER_BYTES);
            }
            result[index] = copyNullable(data);
        }
        return result;
    }

    private static byte @Nullable [] readLayer(FriendlyByteBuf input) {
        if (!input.readBoolean()) {
            return null;
        }
        byte[] data = new byte[DATA_LAYER_BYTES];
        input.readBytes(data);
        return data;
    }

    private static void writeLayer(FriendlyByteBuf output, byte @Nullable [] data) {
        output.writeBoolean(data != null);
        if (data != null) {
            if (data.length != DATA_LAYER_BYTES) {
                throw new EncoderException("Invalid light data length " + data.length + "; expected " + DATA_LAYER_BYTES);
            }
            output.writeBytes(data);
        }
    }

    private static @Nullable DataLayer toDataLayer(byte @Nullable [] data) {
        return data == null ? null : new DataLayer(data.clone());
    }

    private static byte @Nullable [] copyNullable(byte @Nullable [] data) {
        return data == null ? null : data.clone();
    }

    @Override public boolean equals(Object object) {
        if (this == object) {
            return true;
        }
        if (!(object instanceof CCClientboundCubeLightData that)) {
            return false;
        }
        return Arrays.deepEquals(this.blockLight, that.blockLight) && Arrays.deepEquals(this.skyLight, that.skyLight);
    }

    @Override public int hashCode() {
        return 31 * Arrays.deepHashCode(this.blockLight) + Arrays.deepHashCode(this.skyLight);
    }
}
