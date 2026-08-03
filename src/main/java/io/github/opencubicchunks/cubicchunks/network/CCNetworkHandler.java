package io.github.opencubicchunks.cubicchunks.network;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;

public final class CCNetworkHandler {
    private CCNetworkHandler() {}

    public static void registerPayloadTypes() {
        PayloadTypeRegistry.clientboundPlay().register(CCClientboundLevelCubeWithLightPacket.TYPE,
                CCClientboundLevelCubeWithLightPacket.STREAM_CODEC);
        PayloadTypeRegistry.clientboundPlay().register(CCClientboundForgetLevelCloPacket.TYPE, CCClientboundForgetLevelCloPacket.STREAM_CODEC);
        PayloadTypeRegistry.clientboundPlay().register(CCClientboundSetCubeCacheCenterPacket.TYPE,
                CCClientboundSetCubeCacheCenterPacket.STREAM_CODEC);
    }
}
