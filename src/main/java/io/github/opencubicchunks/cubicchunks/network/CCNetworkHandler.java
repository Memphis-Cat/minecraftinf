package io.github.opencubicchunks.cubicchunks.network;

import io.github.opencubicchunks.cubicchunks.CubicChunks;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.network.registration.PayloadRegistrar;

@EventBusSubscriber(bus = EventBusSubscriber.Bus.MOD)
public class CCNetworkHandler {
    private CCNetworkHandler() {}

    @SubscribeEvent
    public static void register(final RegisterPayloadHandlersEvent event) {
        final PayloadRegistrar registrar = event.registrar(CubicChunks.MODID);

        registrar.playToClient(CCClientboundLevelCubeWithLightPacket.TYPE, CCClientboundLevelCubeWithLightPacket.STREAM_CODEC,
                new CCClientboundLevelCubeWithLightPacket.Handler());
        registrar.playToClient(CCClientboundCubeLightUpdatePacket.TYPE, CCClientboundCubeLightUpdatePacket.STREAM_CODEC,
                new CCClientboundCubeLightUpdatePacket.Handler());
        registrar.playToClient(CCClientboundForgetLevelCloPacket.TYPE, CCClientboundForgetLevelCloPacket.STREAM_CODEC,
                new CCClientboundForgetLevelCloPacket.Handler());
        registrar.playToClient(CCClientboundSetCubeCacheCenterPacket.TYPE, CCClientboundSetCubeCacheCenterPacket.STREAM_CODEC,
                new CCClientboundSetCubeCacheCenterPacket.Handler());
    }
}
