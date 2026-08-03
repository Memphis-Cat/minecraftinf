package io.github.opencubicchunks.cubicchunks.network;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.function.Consumer;

import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.game.ClientboundLevelChunkPacketData;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.chunk.LevelChunkSection;

/** Section palettes and block-entity update data for one full cube. */
public class CCClientboundLevelCubePacketData {
    private static final int TWO_MEGABYTES = 2_097_152;
    private static final int MAX_BLOCK_ENTITIES = 65_536;

    private final byte[] buffer;
    private final List<BlockEntityData> blockEntities;

    public static final StreamCodec<FriendlyByteBuf, CCClientboundLevelCubePacketData> STREAM_CODEC = new StreamCodec<>() {
        @Override public CCClientboundLevelCubePacketData decode(FriendlyByteBuf buffer) {
            return new CCClientboundLevelCubePacketData(buffer);
        }

        @Override public void encode(FriendlyByteBuf buffer, CCClientboundLevelCubePacketData data) {
            data.write(buffer);
        }
    };

    public CCClientboundLevelCubePacketData(LevelCube cube) {
        this.buffer = new byte[calculateChunkSize(cube)];
        extractChunkData(new FriendlyByteBuf(this.getWriteBuffer()), cube);
        this.blockEntities = new ArrayList<>(cube.getBlockEntities().size());
        for (BlockEntity blockEntity : cube.getBlockEntities().values()) {
            this.blockEntities.add(BlockEntityData.create(blockEntity, cube.getLevel().registryAccess()));
        }
    }

    public CCClientboundLevelCubePacketData(FriendlyByteBuf byteBuf) {
        int byteCount = byteBuf.readVarInt();
        if (byteCount < 0 || byteCount > TWO_MEGABYTES) {
            throw new IllegalArgumentException("Cube packet payload is too large: " + byteCount);
        }
        this.buffer = new byte[byteCount];
        byteBuf.readBytes(this.buffer);

        int blockEntityCount = byteBuf.readVarInt();
        if (blockEntityCount < 0 || blockEntityCount > MAX_BLOCK_ENTITIES) {
            throw new IllegalArgumentException("Cube packet block-entity count is invalid: " + blockEntityCount);
        }
        this.blockEntities = new ArrayList<>(blockEntityCount);
        for (int index = 0; index < blockEntityCount; ++index) {
            this.blockEntities.add(BlockEntityData.read(byteBuf));
        }
    }

    public void write(FriendlyByteBuf byteBuf) {
        byteBuf.writeVarInt(this.buffer.length);
        byteBuf.writeBytes(this.buffer);
        byteBuf.writeVarInt(this.blockEntities.size());
        for (BlockEntityData blockEntity : this.blockEntities) {
            blockEntity.write(byteBuf);
        }
    }

    private ByteBuf getWriteBuffer() {
        ByteBuf bytebuf = Unpooled.wrappedBuffer(this.buffer);
        bytebuf.writerIndex(0);
        return bytebuf;
    }

    private static int calculateChunkSize(LevelCube cube) {
        int size = 0;
        for (LevelChunkSection section : cube.getSections()) {
            size = Math.addExact(size, section.getSerializedSize());
        }
        return size;
    }

    public static void extractChunkData(FriendlyByteBuf buffer, LevelCube cube) {
        for (LevelChunkSection section : cube.getSections()) {
            section.write(buffer);
        }

        if (buffer.writerIndex() != buffer.capacity()) {
            throw new IllegalStateException("Didn't fill cube buffer: expected " + buffer.capacity() + " bytes, got " + buffer.writerIndex());
        }
    }

    public FriendlyByteBuf getReadBuffer() {
        return new FriendlyByteBuf(Unpooled.wrappedBuffer(this.buffer));
    }

    public Consumer<ClientboundLevelChunkPacketData.BlockEntityTagOutput> getBlockEntitiesTagsConsumer() {
        return output -> {
            for (BlockEntityData blockEntity : this.blockEntities) {
                output.accept(blockEntity.position(), blockEntity.type(), blockEntity.tag().copy());
            }
        };
    }

    @Override public boolean equals(Object other) {
        if (!(other instanceof CCClientboundLevelCubePacketData that)) {
            return false;
        }
        return Arrays.equals(this.buffer, that.buffer) && this.blockEntities.equals(that.blockEntities);
    }

    @Override public int hashCode() {
        return Objects.hash(Arrays.hashCode(this.buffer), this.blockEntities);
    }

    private record BlockEntityData(BlockPos position, BlockEntityType<?> type, CompoundTag tag) {
        private static BlockEntityData create(BlockEntity blockEntity, net.minecraft.core.HolderLookup.Provider registries) {
            return new BlockEntityData(blockEntity.getBlockPos(), blockEntity.getType(), blockEntity.getUpdateTag(registries));
        }

        private static BlockEntityData read(FriendlyByteBuf buffer) {
            BlockPos position = buffer.readBlockPos();
            int typeId = buffer.readVarInt();
            BlockEntityType<?> type = BuiltInRegistries.BLOCK_ENTITY_TYPE.byId(typeId);
            if (type == null) {
                throw new IllegalArgumentException("Unknown block entity type id " + typeId);
            }
            CompoundTag tag = buffer.readNbt();
            return new BlockEntityData(position, type, tag == null ? new CompoundTag() : tag);
        }

        private void write(FriendlyByteBuf buffer) {
            int typeId = BuiltInRegistries.BLOCK_ENTITY_TYPE.getId(this.type);
            if (typeId < 0) {
                throw new IllegalStateException("Unregistered block entity type " + this.type);
            }
            buffer.writeBlockPos(this.position);
            buffer.writeVarInt(typeId);
            buffer.writeNbt(this.tag);
        }
    }
}
