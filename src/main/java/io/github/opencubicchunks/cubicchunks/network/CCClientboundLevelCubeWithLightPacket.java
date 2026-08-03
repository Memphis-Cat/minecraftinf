package io.github.opencubicchunks.cubicchunks.network;

import static io.github.opencubicchunks.cubicchunks.network.MiscStreamCodecs.CUBE_POS_STREAM_CODEC;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cubicchunks.CubicChunks;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;

// TODO (P2) the name is currently a lie; no light data :)
public record CCClientboundLevelCubeWithLightPacket(CubePos pos, CCClientboundLevelCubePacketData cubeData) implements CustomPacketPayload {
    public static final Type<CCClientboundLevelCubeWithLightPacket> TYPE = new Type<>(
            Identifier.fromNamespaceAndPath(CubicChunks.MODID, "level_cube_with_light"));

    public static final StreamCodec<FriendlyByteBuf, CCClientboundLevelCubeWithLightPacket> STREAM_CODEC = StreamCodec.composite(
            CUBE_POS_STREAM_CODEC, CCClientboundLevelCubeWithLightPacket::pos, CCClientboundLevelCubePacketData.STREAM_CODEC,
            CCClientboundLevelCubeWithLightPacket::cubeData, CCClientboundLevelCubeWithLightPacket::new);

    @Override public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }

    public CCClientboundLevelCubeWithLightPacket(LevelCube cube) {
        this(cube.cc_getCloPos().cubePos(), new CCClientboundLevelCubePacketData(cube));
    }
}
