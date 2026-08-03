package io.github.opencubicchunks.cubicchunks.network;

import java.util.HashMap;
import java.util.Map;
import java.util.function.Consumer;

import io.github.opencubicchunks.cubicchunks.client.multiplayer.ClientCubeCache;
import io.github.opencubicchunks.cubicchunks.client.renderer.CubicLevelRenderer;
import io.github.opencubicchunks.cubicchunks.world.level.cube.CubeSource;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.multiplayer.ClientChunkCache;
import net.minecraft.network.protocol.game.ClientboundLevelChunkPacketData;
import net.minecraft.world.level.levelgen.Heightmap;

public final class CCClientNetworkHandler implements ClientModInitializer {
    @Override public void onInitializeClient() {
        ClientPlayNetworking.registerGlobalReceiver(CCClientboundLevelCubeWithLightPacket.TYPE, CCClientNetworkHandler::handleLevelCube);
        ClientPlayNetworking.registerGlobalReceiver(CCClientboundForgetLevelCloPacket.TYPE, CCClientNetworkHandler::handleForgetClo);
        ClientPlayNetworking.registerGlobalReceiver(CCClientboundSetCubeCacheCenterPacket.TYPE, CCClientNetworkHandler::handleCubeCenter);
    }

    private static void handleLevelCube(CCClientboundLevelCubeWithLightPacket payload, ClientPlayNetworking.Context context) {
        var level = context.client().level;
        if (level == null) {
            return;
        }

        int x = payload.pos().getX();
        int y = payload.pos().getY();
        int z = payload.pos().getZ();

        // Heightmaps remain column-owned. Cube packet block-entity application is
        // still intentionally delegated to the cube packet-data implementation.
        Map<Heightmap.Types, long[]> heightmaps = new HashMap<>();
        Consumer<ClientboundLevelChunkPacketData.BlockEntityTagOutput> entityTagConsumer = ignored -> {};
        ((ClientCubeCache) level.getChunkSource()).cc_replaceWithPacketData(x, y, z, payload.cubeData().getReadBuffer(), heightmaps,
                entityTagConsumer);

        level.queueLightUpdate(() -> {
            LevelCube levelCube = ((CubeSource) level.getChunkSource()).cc_getCube(x, y, z, false);
            if (levelCube != null) {
                ((CubicLevelRenderer) context.client().levelRenderer).cc_onCubeReadyToRender(payload.pos());
            }
        });
    }

    private static void handleForgetClo(CCClientboundForgetLevelCloPacket payload, ClientPlayNetworking.Context context) {
        var level = context.client().level;
        if (level == null) {
            return;
        }
        ClientChunkCache clientChunkCache = level.getChunkSource();
        if (payload.pos().isChunk()) {
            clientChunkCache.drop(payload.pos().chunkPos());
        } else {
            ((ClientCubeCache) clientChunkCache).cc_drop(payload.pos().cubePos());
        }
    }

    private static void handleCubeCenter(CCClientboundSetCubeCacheCenterPacket payload, ClientPlayNetworking.Context context) {
        var level = context.client().level;
        if (level == null) {
            return;
        }
        ((ClientCubeCache) level.getChunkSource()).cc_updateViewCenter(payload.pos().getX(), payload.pos().getY(), payload.pos().getZ());
    }
}
