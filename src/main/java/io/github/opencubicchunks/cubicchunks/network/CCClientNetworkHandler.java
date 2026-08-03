package io.github.opencubicchunks.cubicchunks.network;

import java.util.Map;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.api.CubicConstants;
import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cubicchunks.client.multiplayer.ClientCubeCache;
import io.github.opencubicchunks.cubicchunks.client.renderer.CubicLevelRenderer;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.multiplayer.ClientChunkCache;
import net.minecraft.core.SectionPos;
import net.minecraft.world.level.chunk.LevelChunkSection;

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

        CubePos cubePos = payload.pos();
        LevelCube cube = ((ClientCubeCache) level.getChunkSource()).cc_replaceWithPacketData(
                cubePos.getX(), cubePos.getY(), cubePos.getZ(), payload.cubeData().getReadBuffer(), Map.of(),
                payload.cubeData().getBlockEntitiesTagsConsumer()
        );
        if (cube == null) {
            return;
        }

        level.queueLightUpdate(() -> {
            var lightEngine = level.getLightEngine();
            payload.lightData().apply(cubePos, lightEngine);

            LevelChunkSection[] sections = cube.getSections();
            for (int index = 0; index < CubicConstants.SECTION_COUNT; index++) {
                SectionPos sectionPos = SectionPos.of(
                        Coords.cubeToSection(cubePos.getX(), Coords.indexToX(index)),
                        Coords.cubeToSection(cubePos.getY(), Coords.indexToY(index)),
                        Coords.cubeToSection(cubePos.getZ(), Coords.indexToZ(index))
                );
                lightEngine.updateSectionStatus(sectionPos, sections[index].hasOnlyAir());
            }

            int minSectionX = Coords.cubeToSection(cubePos.getX(), 0);
            int minSectionY = Coords.cubeToSection(cubePos.getY(), 0);
            int minSectionZ = Coords.cubeToSection(cubePos.getZ(), 0);
            int maxLocal = CubicConstants.DIAMETER_IN_SECTIONS - 1;
            int maxSectionX = Coords.cubeToSection(cubePos.getX(), maxLocal);
            int maxSectionY = Coords.cubeToSection(cubePos.getY(), maxLocal);
            int maxSectionZ = Coords.cubeToSection(cubePos.getZ(), maxLocal);
            level.setSectionRangeDirty(minSectionX - 1, minSectionY - 1, minSectionZ - 1,
                    maxSectionX + 1, maxSectionY + 1, maxSectionZ + 1);

            ((CubicLevelRenderer) context.client().levelRenderer).cc_onCubeReadyToRender(cubePos);
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
