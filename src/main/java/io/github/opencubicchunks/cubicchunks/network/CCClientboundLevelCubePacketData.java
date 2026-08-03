package io.github.opencubicchunks.cubicchunks.network;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map.Entry;
import java.util.Objects;
import java.util.function.Consumer;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.api.CubicConstants;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import io.netty.handler.codec.DecoderException;
import io.netty.handler.codec.EncoderException;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.game.ClientboundLevelChunkPacketData;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.chunk.LevelChunkSection;
import org.jspecify.annotations.Nullable;

/** Serialized cube sections and block-entity update tags. Heightmaps remain column-owned. */
public final class CCClientboundLevelCubePacketData {
    private static final int TWO_MEGABYTES = 2 * 1024 * 1024;

    public static final StreamCodec<FriendlyByteBuf, CCClientboundLevelCubePacketData> STREAM_CODEC = new StreamCodec<>() {
        @Override public CCClientboundLevelCubePacketData decode(FriendlyByteBuf input) {
            return new CCClientboundLevelCubePacketData(input);
        }

        @Override public void encode(FriendlyByteBuf output, CCClientboundLevelCubePacketData value) {
            value.write(output);
        }
    };

    private final byte[] buffer;
    private final List<BlockEntityInfo> blockEntitiesData;

    public CCClientboundLevelCubePacketData(LevelCube cube) {
        this.buffer = new byte[calculateCubeSize(cube)];
        extractCubeData(new FriendlyByteBuf(this.getWriteBuffer()), cube);
        List<BlockEntityInfo> blockEntities = new ArrayList<>(cube.getBlockEntities().size());
        for (Entry<BlockPos, BlockEntity> entry : cube.getBlockEntities().entrySet()) {
            BlockEntity blockEntity = entry.getValue();
            if (!cube.cc_getCubePos().contains(blockEntity.getBlockPos())) {
                throw new IllegalStateException("Block entity " + blockEntity.getBlockPos() + " is outside cube " + cube.cc_getCubePos());
            }
            blockEntities.add(BlockEntityInfo.create(blockEntity));
        }
        this.blockEntitiesData = List.copyOf(blockEntities);
    }

    CCClientboundLevelCubePacketData(byte[] buffer, List<BlockEntityInfo> blockEntitiesData) {
        if (buffer.length > TWO_MEGABYTES) {
            throw new IllegalArgumentException("Cube section data exceeds the two-megabyte packet limit");
        }
        if (blockEntitiesData.size() > CubicConstants.BLOCK_COUNT) {
            throw new IllegalArgumentException("Cube packet contains more block entities than cube blocks");
        }
        this.buffer = buffer.clone();
        this.blockEntitiesData = List.copyOf(blockEntitiesData);
    }

    private CCClientboundLevelCubePacketData(FriendlyByteBuf input) {
        int sectionBytes = input.readVarInt();
        if (sectionBytes < 0 || sectionBytes > TWO_MEGABYTES) {
            throw new DecoderException("Cube packet section data length " + sectionBytes + " is outside 0.." + TWO_MEGABYTES);
        }
        this.buffer = new byte[sectionBytes];
        input.readBytes(this.buffer);

        int blockEntityCount = input.readVarInt();
        if (blockEntityCount < 0 || blockEntityCount > CubicConstants.BLOCK_COUNT) {
            throw new DecoderException("Cube packet block-entity count " + blockEntityCount + " is outside 0.." + CubicConstants.BLOCK_COUNT);
        }
        List<BlockEntityInfo> blockEntities = new ArrayList<>(blockEntityCount);
        for (int index = 0; index < blockEntityCount; index++) {
            blockEntities.add(BlockEntityInfo.decode(input));
        }
        this.blockEntitiesData = List.copyOf(blockEntities);
    }

    public void write(FriendlyByteBuf output) {
        if (this.buffer.length > TWO_MEGABYTES) {
            throw new EncoderException("Cube packet section data exceeds the two-megabyte limit");
        }
        output.writeVarInt(this.buffer.length);
        output.writeBytes(this.buffer);
        output.writeVarInt(this.blockEntitiesData.size());
        for (BlockEntityInfo blockEntity : this.blockEntitiesData) {
            blockEntity.write(output);
        }
    }

    public void validateFor(CubePos cubePos) {
        for (BlockEntityInfo blockEntity : this.blockEntitiesData) {
            if (!cubePos.contains(blockEntity.pos())) {
                throw new DecoderException("Block entity " + blockEntity.pos() + " is outside packet cube " + cubePos);
            }
        }
    }

    public Consumer<ClientboundLevelChunkPacketData.BlockEntityTagOutput> getBlockEntitiesTagsConsumer() {
        return output -> {
            for (BlockEntityInfo data : this.blockEntitiesData) {
                output.accept(data.pos(), data.type(), data.tag());
            }
        };
    }

    public FriendlyByteBuf getReadBuffer() {
        return new FriendlyByteBuf(Unpooled.wrappedBuffer(this.buffer));
    }

    List<BlockEntityInfo> blockEntitiesData() {
        return this.blockEntitiesData;
    }

    private ByteBuf getWriteBuffer() {
        ByteBuf byteBuf = Unpooled.wrappedBuffer(this.buffer);
        byteBuf.writerIndex(0);
        return byteBuf;
    }

    private static int calculateCubeSize(LevelCube cube) {
        int total = 0;
        for (LevelChunkSection section : cube.getSections()) {
            total += section.getSerializedSize();
        }
        if (total > TWO_MEGABYTES) {
            throw new IllegalStateException("Cube section data requires " + total + " bytes, exceeding the packet limit");
        }
        return total;
    }

    public static void extractCubeData(FriendlyByteBuf output, LevelCube cube) {
        for (LevelChunkSection section : cube.getSections()) {
            section.write(output);
        }
        if (output.writerIndex() != output.capacity()) {
            throw new IllegalStateException("Did not fill cube buffer: expected " + output.capacity() + " bytes, got " + output.writerIndex());
        }
    }

    public record BlockEntityInfo(BlockPos pos, BlockEntityType<?> type, @Nullable CompoundTag tag) {
        public BlockEntityInfo {
            pos = pos.immutable();
            Objects.requireNonNull(type, "type");
            tag = tag == null ? null : tag.copy();
        }

        @Override public @Nullable CompoundTag tag() {
            return this.tag == null ? null : this.tag.copy();
        }

        private static BlockEntityInfo decode(FriendlyByteBuf input) {
            BlockPos pos = input.readBlockPos();
            int typeId = input.readVarInt();
            BlockEntityType<?> type = BuiltInRegistries.BLOCK_ENTITY_TYPE.byId(typeId);
            if (type == null) {
                throw new DecoderException("Unknown block-entity type id " + typeId);
            }
            return new BlockEntityInfo(pos, type, input.readNbt());
        }

        private void write(FriendlyByteBuf output) {
            output.writeBlockPos(this.pos);
            int typeId = BuiltInRegistries.BLOCK_ENTITY_TYPE.getId(this.type);
            if (typeId < 0) {
                throw new EncoderException("Unregistered block-entity type " + this.type);
            }
            output.writeVarInt(typeId);
            output.writeNbt(this.tag);
        }

        private static BlockEntityInfo create(BlockEntity blockEntity) {
            if (blockEntity.getLevel() == null) {
                throw new IllegalStateException("Cannot serialize an unbound block entity at " + blockEntity.getBlockPos());
            }
            CompoundTag updateTag = blockEntity.getUpdateTag(blockEntity.getLevel().registryAccess());
            return new BlockEntityInfo(blockEntity.getBlockPos(), blockEntity.getType(), updateTag.isEmpty() ? null : updateTag);
        }
    }

    @Override public boolean equals(Object object) {
        if (this == object) {
            return true;
        }
        if (!(object instanceof CCClientboundLevelCubePacketData that)) {
            return false;
        }
        return Arrays.equals(this.buffer, that.buffer) && this.blockEntitiesData.equals(that.blockEntitiesData);
    }

    @Override public int hashCode() {
        return 31 * Arrays.hashCode(this.buffer) + this.blockEntitiesData.hashCode();
    }
}
