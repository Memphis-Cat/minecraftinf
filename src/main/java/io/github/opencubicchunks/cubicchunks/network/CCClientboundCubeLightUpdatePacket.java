package io.github.opencubicchunks.cubicchunks.network;

import static io.github.opencubicchunks.cubicchunks.network.MiscStreamCodecs.CUBE_POS_STREAM_CODEC;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cubicchunks.CubicChunks;
import io.github.opencubicchunks.cubicchunks.world.level.cube.CubeSource;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.neoforge.network.handling.IPayloadContext;
import net.neoforged.neoforge.network.handling.IPayloadHandler;

/** Replaces block- and sky-light data for every section in one loaded cube. */
public record CCClientboundCubeLightUpdatePacket(CubePos pos, CCCubeLightData lightData) implements CustomPacketPayload {
    public static final Type<CCClientboundCubeLightUpdatePacket> TYPE = new Type<>(
            ResourceLocation.fromNamespaceAndPath(CubicChunks.MODID, "cube_light_update"));

    public static final StreamCodec<FriendlyByteBuf, CCClientboundCubeLightUpdatePacket> STREAM_CODEC = StreamCodec.composite(
            CUBE_POS_STREAM_CODEC, CCClientboundCubeLightUpdatePacket::pos,
            CCCubeLightData.STREAM_CODEC, CCClientboundCubeLightUpdatePacket::lightData,
            CCClientboundCubeLightUpdatePacket::new);

    @Override public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }

    public static final class Handler implements IPayloadHandler<CCClientboundCubeLightUpdatePacket> {
        @Override public void handle(CCClientboundCubeLightUpdatePacket payload, IPayloadContext context) {
            ClientLevel level = (ClientLevel) context.player().level();
            LevelCube cube = ((CubeSource) level.getChunkSource()).cc_getCube(
                    payload.pos().getX(), payload.pos().getY(), payload.pos().getZ(), false);
            if (cube != null) {
                level.queueLightUpdate(() -> payload.lightData().apply(level, cube));
            }
        }
    }
}
