package io.github.opencubicchunks.cubicchunks.network;

import static io.github.opencubicchunks.cubicchunks.network.MiscStreamCodecs.CUBE_POS_STREAM_CODEC;

import java.util.Map;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cubicchunks.CubicChunks;
import io.github.opencubicchunks.cubicchunks.client.multiplayer.ClientCubeCache;
import io.github.opencubicchunks.cubicchunks.client.renderer.CubicLevelRenderer;
import io.github.opencubicchunks.cubicchunks.world.level.cube.CubeSource;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.lighting.LevelLightEngine;
import net.neoforged.neoforge.network.handling.IPayloadContext;
import net.neoforged.neoforge.network.handling.IPayloadHandler;

/** Complete cube section, block-entity and lighting payload. */
public record CCClientboundLevelCubeWithLightPacket(CubePos pos, CCClientboundLevelCubePacketData cubeData, CCCubeLightData lightData)
        implements CustomPacketPayload {
    public static final Type<CCClientboundLevelCubeWithLightPacket> TYPE = new Type<>(
            ResourceLocation.fromNamespaceAndPath(CubicChunks.MODID, "level_cube_with_light"));

    public static final StreamCodec<FriendlyByteBuf, CCClientboundLevelCubeWithLightPacket> STREAM_CODEC = StreamCodec.composite(
            CUBE_POS_STREAM_CODEC, CCClientboundLevelCubeWithLightPacket::pos,
            CCClientboundLevelCubePacketData.STREAM_CODEC, CCClientboundLevelCubeWithLightPacket::cubeData,
            CCCubeLightData.STREAM_CODEC, CCClientboundLevelCubeWithLightPacket::lightData,
            CCClientboundLevelCubeWithLightPacket::new);

    @Override public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }

    public CCClientboundLevelCubeWithLightPacket(LevelCube cube) {
        this(cube, cube.getLevel().getLightEngine());
    }

    public CCClientboundLevelCubeWithLightPacket(LevelCube cube, LevelLightEngine lightEngine) {
        this(cube.cc_getCubePos(), new CCClientboundLevelCubePacketData(cube), new CCCubeLightData(cube.cc_getCubePos(), lightEngine));
    }

    public static class Handler implements IPayloadHandler<CCClientboundLevelCubeWithLightPacket> {
        @Override public void handle(CCClientboundLevelCubeWithLightPacket payload, IPayloadContext context) {
            Level level = context.player().level();
            int x = payload.pos().getX();
            int y = payload.pos().getY();
            int z = payload.pos().getZ();
            ClientCubeCache cubeCache = (ClientCubeCache) level.getChunkSource();

            // Heightmaps and structures remain authoritative on the vanilla columns, which are sent first.
            Map<Heightmap.Types, long[]> columnOwnedHeightmaps = Map.of();
            LevelCube cube = cubeCache.cc_replaceWithPacketData(x, y, z, payload.cubeData().getReadBuffer(), columnOwnedHeightmaps,
                    payload.cubeData().getBlockEntitiesTagsConsumer());
            if (cube == null) {
                return;
            }

            ClientLevel clientLevel = (ClientLevel) level;
            clientLevel.queueLightUpdate(() -> {
                payload.lightData().apply(clientLevel, cube);
                LevelCube loadedCube = ((CubeSource) level.getChunkSource()).cc_getCube(x, y, z, false);
                if (loadedCube != null) {
                    ((CubicLevelRenderer) Minecraft.getInstance().levelRenderer).cc_onCubeReadyToRender(payload.pos());
                }
            });
        }
    }
}
