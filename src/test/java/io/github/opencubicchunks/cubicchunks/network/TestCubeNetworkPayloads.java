package io.github.opencubicchunks.cubicchunks.network;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotSame;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.List;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.api.CubicConstants;
import io.netty.buffer.Unpooled;
import io.netty.handler.codec.DecoderException;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.world.level.block.entity.BlockEntityType;
import org.junit.jupiter.api.Test;

class TestCubeNetworkPayloads {
    @Test
    void cubePacketRoundTripsSectionsBlockEntitiesAndLight() {
        CubePos cubePos = CubePos.of(0, 0, 0);
        CompoundTag updateTag = new CompoundTag();
        updateTag.putString("test_value", "cubicchunks");

        var blockEntity = new CCClientboundLevelCubePacketData.BlockEntityInfo(
                new BlockPos(3, 7, 11), BlockEntityType.CHEST, updateTag
        );
        var cubeData = new CCClientboundLevelCubePacketData(new byte[] { 1, 2, 3, 4, 5 }, List.of(blockEntity));

        byte[][] blockLight = new byte[CubicConstants.SECTION_COUNT][];
        byte[][] skyLight = new byte[CubicConstants.SECTION_COUNT][];
        blockLight[0] = filledLayer((byte) 0x15);
        skyLight[CubicConstants.SECTION_COUNT - 1] = filledLayer((byte) 0x7A);
        var lightData = new CCClientboundCubeLightData(blockLight, skyLight);
        var original = new CCClientboundLevelCubeWithLightPacket(cubePos, cubeData, lightData);

        FriendlyByteBuf buffer = new FriendlyByteBuf(Unpooled.buffer());
        try {
            CCClientboundLevelCubeWithLightPacket.STREAM_CODEC.encode(buffer, original);
            CCClientboundLevelCubeWithLightPacket decoded = CCClientboundLevelCubeWithLightPacket.STREAM_CODEC.decode(buffer);

            assertEquals(original.pos(), decoded.pos());
            assertEquals(original.cubeData(), decoded.cubeData());
            assertEquals(original.lightData(), decoded.lightData());
            assertEquals(0, buffer.readableBytes());

            var decodedEntity = decoded.cubeData().blockEntitiesData().getFirst();
            assertEquals(blockEntity.pos(), decodedEntity.pos());
            assertEquals(blockEntity.type(), decodedEntity.type());
            assertEquals(updateTag, decodedEntity.tag());
            assertArrayEquals(blockLight[0], decoded.lightData().blockLight(0));
            assertArrayEquals(skyLight[CubicConstants.SECTION_COUNT - 1],
                    decoded.lightData().skyLight(CubicConstants.SECTION_COUNT - 1));
            assertNull(decoded.lightData().skyLight(0));
        } finally {
            buffer.release();
        }
    }

    @Test
    void lightPayloadDefensivelyCopiesSectionArrays() {
        byte[][] blockLight = new byte[CubicConstants.SECTION_COUNT][];
        byte[][] skyLight = new byte[CubicConstants.SECTION_COUNT][];
        blockLight[0] = filledLayer((byte) 1);

        var data = new CCClientboundCubeLightData(blockLight, skyLight);
        byte[] firstRead = data.blockLight(0);
        byte[] secondRead = data.blockLight(0);
        assertNotSame(firstRead, secondRead);
        firstRead[0] = 99;
        assertEquals(1, secondRead[0]);
    }

    @Test
    void packetRejectsBlockEntitiesOutsideItsCube() {
        var entity = new CCClientboundLevelCubePacketData.BlockEntityInfo(
                new BlockPos(CubicConstants.DIAMETER_IN_BLOCKS, 0, 0), BlockEntityType.CHEST, null
        );
        var data = new CCClientboundLevelCubePacketData(new byte[0], List.of(entity));
        byte[][] blockLight = new byte[CubicConstants.SECTION_COUNT][];
        byte[][] skyLight = new byte[CubicConstants.SECTION_COUNT][];

        assertThrows(DecoderException.class,
                () -> new CCClientboundLevelCubeWithLightPacket(CubePos.of(0, 0, 0), data,
                        new CCClientboundCubeLightData(blockLight, skyLight)));
    }

    private static byte[] filledLayer(byte value) {
        byte[] result = new byte[2048];
        java.util.Arrays.fill(result, value);
        return result;
    }
}
