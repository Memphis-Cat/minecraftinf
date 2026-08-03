package io.github.opencubicchunks.cubicchunks.network;

import static io.github.opencubicchunks.cubicchunks.network.MiscStreamCodecs.CLO_POS_STREAM_CODEC;

import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.CubicChunks;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;

public record CCClientboundForgetLevelCloPacket(CloPos pos) implements CustomPacketPayload {
    public static final CustomPacketPayload.Type<CCClientboundForgetLevelCloPacket> TYPE = new CustomPacketPayload.Type<>(
            Identifier.fromNamespaceAndPath(CubicChunks.MODID, "forget_clo"));

    public static final StreamCodec<ByteBuf, CCClientboundForgetLevelCloPacket> STREAM_CODEC = StreamCodec.composite(CLO_POS_STREAM_CODEC,
            CCClientboundForgetLevelCloPacket::pos, CCClientboundForgetLevelCloPacket::new);

    @Override public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
