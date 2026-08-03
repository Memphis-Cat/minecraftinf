package io.github.opencubicchunks.cubicchunks.network;

import static io.github.opencubicchunks.cubicchunks.network.MiscStreamCodecs.CLO_POS_STREAM_CODEC;

import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.CubicChunks;
import io.github.opencubicchunks.cubicchunks.client.multiplayer.ClientCubeCache;
import io.netty.buffer.ByteBuf;
import net.minecraft.client.multiplayer.ClientChunkCache;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.neoforge.network.handling.IPayloadContext;
import net.neoforged.neoforge.network.handling.IPayloadHandler;

public record CCClientboundForgetLevelCloPacket(CloPos pos) implements CustomPacketPayload {
    public static final CustomPacketPayload.Type<CCClientboundForgetLevelCloPacket> TYPE = new CustomPacketPayload.Type<>(
            ResourceLocation.fromNamespaceAndPath(CubicChunks.MODID, "forget_clo"));

    public static final StreamCodec<ByteBuf, CCClientboundForgetLevelCloPacket> STREAM_CODEC = StreamCodec.composite(CLO_POS_STREAM_CODEC,
            CCClientboundForgetLevelCloPacket::pos, CCClientboundForgetLevelCloPacket::new);

    @Override public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }

    public static class Handler implements IPayloadHandler<CCClientboundForgetLevelCloPacket> {
        @Override public void handle(CCClientboundForgetLevelCloPacket payload, IPayloadContext context) {
            ClientLevel level = (ClientLevel) context.player().level();
            ClientChunkCache clientChunkCache = level.getChunkSource();
            if (payload.pos.isChunk()) {
                clientChunkCache.drop(payload.pos.chunkPos());
            } else {
                level.queueLightUpdate(() -> CCCubeLightData.clear(level, payload.pos.cubePos()));
                ((ClientCubeCache) clientChunkCache).cc_drop(payload.pos.cubePos());
            }
        }
    }
}
