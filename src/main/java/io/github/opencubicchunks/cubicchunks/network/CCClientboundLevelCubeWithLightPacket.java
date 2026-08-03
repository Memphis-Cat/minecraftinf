package io.github.opencubicchunks.cubicchunks.network;

import static io.github.opencubicchunks.cubicchunks.network.MiscStreamCodecs.CUBE_POS_STREAM_CODEC;

import java.util.Objects;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cubicchunks.CubicChunks;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.lighting.LevelLightEngine;

/** Full cube sections, block entities, block light and sky light. */
public record CCClientboundLevelCubeWithLightPacket(
        CubePos pos, CCClientboundLevelCubePacketData cubeData, CCClientboundCubeLightData lightData
) implements CustomPacketPayload {
    public static final Type<CCClientboundLevelCubeWithLightPacket> TYPE = new Type<>(
            Identifier.fromNamespaceAndPath(CubicChunks.MODID, "level_cube_with_light"));

    public static final StreamCodec<FriendlyByteBuf, CCClientboundLevelCubeWithLightPacket> STREAM_CODEC = new StreamCodec<>() {
        @Override public CCClientboundLevelCubeWithLightPacket decode(FriendlyByteBuf input) {
            CubePos pos = CUBE_POS_STREAM_CODEC.decode(input);
            CCClientboundLevelCubePacketData cubeData = CCClientboundLevelCubePacketData.STREAM_CODEC.decode(input);
            CCClientboundCubeLightData lightData = CCClientboundCubeLightData.STREAM_CODEC.decode(input);
            return new CCClientboundLevelCubeWithLightPacket(pos, cubeData, lightData);
        }

        @Override public void encode(FriendlyByteBuf output, CCClientboundLevelCubeWithLightPacket value) {
            CUBE_POS_STREAM_CODEC.encode(output, value.pos);
            CCClientboundLevelCubePacketData.STREAM_CODEC.encode(output, value.cubeData);
            CCClientboundCubeLightData.STREAM_CODEC.encode(output, value.lightData);
        }
    };

    public CCClientboundLevelCubeWithLightPacket {
        Objects.requireNonNull(pos, "pos");
        Objects.requireNonNull(cubeData, "cubeData");
        Objects.requireNonNull(lightData, "lightData");
        cubeData.validateFor(pos);
    }

    public CCClientboundLevelCubeWithLightPacket(LevelCube cube, LevelLightEngine lightEngine) {
        this(cube.cc_getCubePos(), new CCClientboundLevelCubePacketData(cube), new CCClientboundCubeLightData(cube, lightEngine));
    }

    @Override public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
