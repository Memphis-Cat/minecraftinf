package io.github.opencubicchunks.cubicchunks.world.storage;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.EOFException;
import java.io.IOException;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.api.CubicConstants;
import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cubicchunks.CubicChunks;
import io.github.opencubicchunks.cubicchunks.world.level.cube.ImposterProtoCube;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import it.unimi.dsi.fastutil.longs.LongOpenHashSet;
import it.unimi.dsi.fastutil.shorts.ShortArrayList;
import it.unimi.dsi.fastutil.shorts.ShortList;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.SectionPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtIo;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.DataLayer;
import net.minecraft.world.level.chunk.LevelChunkSection;
import net.minecraft.world.level.chunk.UpgradeData;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceSerializationContext;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.ticks.LevelChunkTicks;
import net.minecraft.world.ticks.SavedTick;
import net.minecraft.world.ticks.TickPriority;

/**
 * Versioned and atomic persistence for full cubes.
 * <p>
 * Version 2 stores every cube-owned runtime payload: block/biome section palettes, pending block
 * entities, scheduled block and fluid ticks, post-processing offsets, structure data, and queued
 * sky/block light layers. Vanilla columns remain authoritative for global column heightmaps and
 * POIs.
 * </p>
 */
public final class CubeStorage {
    private static final int MAGIC = 0x43435542; // CCUB
    private static final int VERSION_SECTIONS_ONLY = 1;
    private static final int VERSION_COMPLETE = 2;
    private static final int MAX_SERIALIZED_BYTES = 64 * 1024 * 1024;
    private static final int MAX_COLLECTION_SIZE = 1_000_000;
    private static final int REGION_SHIFT = 5;

    private final Path root;

    public CubeStorage(Path root) {
        this.root = root;
    }

    public synchronized boolean saveIfUnsaved(LevelCube cube) throws IOException {
        if (!cube.tryMarkSaved()) {
            return false;
        }

        try {
            save(cube);
            return true;
        } catch (IOException | RuntimeException exception) {
            cube.markUnsaved();
            throw exception;
        }
    }

    public synchronized void save(LevelCube cube) throws IOException {
        if (!(cube.getLevel() instanceof ServerLevel level)) {
            throw new IOException("Cannot persist a cube without a ServerLevel: " + cube.cc_getCubePos());
        }

        CubePos cubePos = cube.cc_getCubePos();
        byte[] sectionData = serializeSections(cube);
        Path destination = cubePath(cubePos);
        Files.createDirectories(destination.getParent());
        Path temporary = destination.resolveSibling(destination.getFileName() + ".tmp");

        try {
            try (DataOutputStream output = new DataOutputStream(new BufferedOutputStream(Files.newOutputStream(temporary)))) {
                output.writeInt(MAGIC);
                output.writeInt(VERSION_COMPLETE);
                writeCommonHeader(output, cube, sectionData);
                writePostProcessing(output, cube.getPostProcessing());
                writeBlockEntities(output, cube, level);
                ChunkAccess.PackedTicks ticks = cube.getTicksForSerialization(level.getGameTime());
                writeTicks(output, ticks.blocks(), BuiltInRegistries.BLOCK);
                writeTicks(output, ticks.fluids(), BuiltInRegistries.FLUID);
                writeStructures(output, cube, level);
                writeLightLayers(output, cube, level);
            }
            atomicReplace(temporary, destination);
        } catch (IOException | RuntimeException exception) {
            Files.deleteIfExists(temporary);
            throw exception;
        }
    }

    public synchronized Optional<ImposterProtoCube> load(ServerLevel level, CubePos expectedPos) throws IOException {
        Path source = cubePath(expectedPos);
        if (!Files.isRegularFile(source)) {
            return Optional.empty();
        }

        try (DataInputStream input = new DataInputStream(new BufferedInputStream(Files.newInputStream(source)))) {
            validateMagic(input.readInt(), source);
            int version = input.readInt();
            validateVersion(version, source);
            validatePosition(CubePos.of(input.readInt(), input.readInt(), input.readInt()), expectedPos);
            validateSectionCount(input.readInt());

            long inhabitedTime = input.readLong();
            boolean lightCorrect = input.readBoolean();
            byte[] sectionData = readByteArray(input, source, "section palette");
            Registry<Biome> biomeRegistry = level.registryAccess().lookupOrThrow(Registries.BIOME);
            LevelChunkSection[] sections = deserializeSections(sectionData, biomeRegistry);

            if (version == VERSION_SECTIONS_ONLY) {
                LevelCube legacyCube = new LevelCube(level, expectedPos, UpgradeData.EMPTY, new LevelChunkTicks<>(), new LevelChunkTicks<>(),
                        inhabitedTime, sections, null, null);
                // Version 1 did not contain actual light layers, so force a safe relight after load.
                legacyCube.setLightCorrect(false);
                legacyCube.tryMarkSaved();
                return loaded(expectedPos, legacyCube);
            }

            ShortList[] postProcessing = readPostProcessing(input, source);
            List<CompoundTag> blockEntities = readBlockEntities(input, source);
            List<SavedTick<Block>> blockTicks = readTicks(input, source, BuiltInRegistries.BLOCK, "block");
            List<SavedTick<Fluid>> fluidTicks = readTicks(input, source, BuiltInRegistries.FLUID, "fluid");
            StructureData structures = readStructures(input, source, level);

            LevelCube cube = new LevelCube(level, expectedPos, UpgradeData.EMPTY, new LevelChunkTicks<>(blockTicks),
                    new LevelChunkTicks<>(fluidTicks), inhabitedTime, sections, null, null);
            for (int index = 0; index < postProcessing.length; index++) {
                ShortList offsets = postProcessing[index];
                if (offsets != null && !offsets.isEmpty()) {
                    cube.addPackedPostProcess(offsets, index);
                }
            }
            blockEntities.forEach(cube::setBlockEntityNbt);
            cube.setAllStarts(structures.starts());
            cube.setAllReferences(structures.references());
            boolean completeLightPayload = readLightLayers(input, source, expectedPos, level);
            if (input.read() != -1) {
                throw new IOException("Trailing data after cube payload in " + source);
            }
            cube.setLightCorrect(lightCorrect && completeLightPayload);
            cube.tryMarkSaved();
            return loaded(expectedPos, cube);
        }
    }

    private static Optional<ImposterProtoCube> loaded(CubePos expectedPos, LevelCube cube) {
        CubicChunks.LOGGER.info("Loaded persisted cube {}", expectedPos);
        return Optional.of(new ImposterProtoCube(cube, false));
    }

    private static void writeCommonHeader(DataOutputStream output, LevelCube cube, byte[] sectionData) throws IOException {
        CubePos cubePos = cube.cc_getCubePos();
        output.writeInt(cubePos.getX());
        output.writeInt(cubePos.getY());
        output.writeInt(cubePos.getZ());
        output.writeInt(CubicConstants.SECTION_COUNT);
        output.writeLong(cube.getInhabitedTime());
        output.writeBoolean(cube.isLightCorrect());
        writeByteArray(output, sectionData);
    }

    private static void writePostProcessing(DataOutputStream output, ShortList[] sections) throws IOException {
        output.writeInt(sections.length);
        for (ShortList offsets : sections) {
            int size = offsets == null ? 0 : offsets.size();
            output.writeInt(size);
            for (int index = 0; index < size; index++) {
                output.writeShort(offsets.getShort(index));
            }
        }
    }

    private static ShortList[] readPostProcessing(DataInputStream input, Path source) throws IOException {
        int sectionCount = readCount(input, source, "post-processing section");
        if (sectionCount != CubicConstants.SECTION_COUNT) {
            throw new IOException("Post-processing section count mismatch in " + source + ": " + sectionCount);
        }
        ShortList[] output = new ShortList[sectionCount];
        for (int sectionIndex = 0; sectionIndex < sectionCount; sectionIndex++) {
            int offsetCount = readCount(input, source, "post-processing offset");
            if (offsetCount == 0) {
                continue;
            }
            ShortArrayList offsets = new ShortArrayList(offsetCount);
            for (int offsetIndex = 0; offsetIndex < offsetCount; offsetIndex++) {
                offsets.add(input.readShort());
            }
            output[sectionIndex] = offsets;
        }
        return output;
    }

    private static void writeBlockEntities(DataOutputStream output, LevelCube cube, ServerLevel level) throws IOException {
        List<CompoundTag> tags = new ArrayList<>();
        for (BlockPos blockPos : cube.getBlockEntitiesPos()) {
            CompoundTag tag = cube.getBlockEntityNbtForSaving(blockPos, level.registryAccess());
            if (tag != null) {
                tags.add(tag);
            }
        }
        output.writeInt(tags.size());
        for (CompoundTag tag : tags) {
            NbtIo.write(tag, output);
        }
    }

    private static List<CompoundTag> readBlockEntities(DataInputStream input, Path source) throws IOException {
        int count = readCount(input, source, "block entity");
        List<CompoundTag> tags = new ArrayList<>(count);
        for (int index = 0; index < count; index++) {
            tags.add(NbtIo.read(input));
        }
        return tags;
    }

    private static <T> void writeTicks(DataOutputStream output, List<SavedTick<T>> ticks, Registry<T> registry) throws IOException {
        output.writeInt(ticks.size());
        for (SavedTick<T> tick : ticks) {
            ResourceLocation key = registry.getKey(tick.type());
            if (key == null) {
                throw new IOException("Scheduled tick references an unregistered value at " + tick.pos());
            }
            output.writeUTF(key.toString());
            output.writeInt(tick.pos().getX());
            output.writeInt(tick.pos().getY());
            output.writeInt(tick.pos().getZ());
            output.writeInt(tick.delay());
            output.writeInt(tick.priority().getValue());
        }
    }

    private static <T> List<SavedTick<T>> readTicks(DataInputStream input, Path source, Registry<T> registry, String kind) throws IOException {
        int count = readCount(input, source, kind + " tick");
        List<SavedTick<T>> ticks = new ArrayList<>(count);
        for (int index = 0; index < count; index++) {
            ResourceLocation key = ResourceLocation.tryParse(input.readUTF());
            T type = key == null ? null : registry.getValue(key);
            if (type == null) {
                throw new IOException("Unknown " + kind + " tick type " + key + " in " + source);
            }
            BlockPos pos = new BlockPos(input.readInt(), input.readInt(), input.readInt());
            int delay = input.readInt();
            TickPriority priority = TickPriority.byValue(input.readInt());
            ticks.add(new SavedTick<>(type, pos, delay, priority));
        }
        return ticks;
    }

    private static void writeStructures(DataOutputStream output, LevelCube cube, ServerLevel level) throws IOException {
        Registry<Structure> registry = level.registryAccess().lookupOrThrow(Registries.STRUCTURE);
        StructurePieceSerializationContext context = StructurePieceSerializationContext.fromLevel(level);
        Map<Structure, StructureStart> starts = cube.getAllStarts();
        output.writeInt(starts.size());
        for (Map.Entry<Structure, StructureStart> entry : starts.entrySet()) {
            ResourceLocation key = registry.getKey(entry.getKey());
            if (key == null) {
                throw new IOException("Cube contains an unregistered structure start");
            }
            output.writeUTF(key.toString());
            NbtIo.write(entry.getValue().createTag(context, entry.getValue().getChunkPos()), output);
        }

        Map<Structure, it.unimi.dsi.fastutil.longs.LongSet> references = cube.getAllReferences();
        output.writeInt(references.size());
        for (Map.Entry<Structure, it.unimi.dsi.fastutil.longs.LongSet> entry : references.entrySet()) {
            ResourceLocation key = registry.getKey(entry.getKey());
            if (key == null) {
                throw new IOException("Cube contains references to an unregistered structure");
            }
            output.writeUTF(key.toString());
            long[] values = entry.getValue().toLongArray();
            output.writeInt(values.length);
            for (long value : values) {
                output.writeLong(value);
            }
        }
    }

    private static StructureData readStructures(DataInputStream input, Path source, ServerLevel level) throws IOException {
        Registry<Structure> registry = level.registryAccess().lookupOrThrow(Registries.STRUCTURE);
        StructurePieceSerializationContext context = StructurePieceSerializationContext.fromLevel(level);
        Map<Structure, StructureStart> starts = new java.util.HashMap<>();
        int startCount = readCount(input, source, "structure start");
        for (int index = 0; index < startCount; index++) {
            ResourceLocation key = ResourceLocation.tryParse(input.readUTF());
            Structure structure = key == null ? null : registry.getValue(key);
            CompoundTag tag = NbtIo.read(input);
            if (structure == null) {
                throw new IOException("Unknown structure start " + key + " in " + source);
            }
            StructureStart start = StructureStart.loadStaticStart(context, tag, level.getSeed());
            if (start != null) {
                starts.put(structure, start);
            }
        }

        Map<Structure, it.unimi.dsi.fastutil.longs.LongSet> references = new java.util.HashMap<>();
        int referenceCount = readCount(input, source, "structure reference");
        for (int index = 0; index < referenceCount; index++) {
            ResourceLocation key = ResourceLocation.tryParse(input.readUTF());
            Structure structure = key == null ? null : registry.getValue(key);
            if (structure == null) {
                throw new IOException("Unknown structure reference " + key + " in " + source);
            }
            int valueCount = readCount(input, source, "structure reference position");
            LongOpenHashSet values = new LongOpenHashSet(valueCount);
            for (int valueIndex = 0; valueIndex < valueCount; valueIndex++) {
                values.add(input.readLong());
            }
            references.put(structure, values);
        }
        return new StructureData(starts, references);
    }

    private static void writeLightLayers(DataOutputStream output, LevelCube cube, ServerLevel level) throws IOException {
        CubePos cubePos = cube.cc_getCubePos();
        output.writeInt(CubicConstants.SECTION_COUNT);
        for (int sectionIndex = 0; sectionIndex < CubicConstants.SECTION_COUNT; sectionIndex++) {
            SectionPos sectionPos = sectionPos(cubePos, sectionIndex);
            writeDataLayer(output, level, LightLayer.BLOCK, sectionPos);
            writeDataLayer(output, level, LightLayer.SKY, sectionPos);
        }
    }

    private static boolean readLightLayers(DataInputStream input, Path source, CubePos cubePos, ServerLevel level) throws IOException {
        int sectionCount = readCount(input, source, "light section");
        if (sectionCount != CubicConstants.SECTION_COUNT) {
            throw new IOException("Light section count mismatch in " + source + ": " + sectionCount);
        }
        boolean complete = true;
        for (int sectionIndex = 0; sectionIndex < sectionCount; sectionIndex++) {
            SectionPos sectionPos = sectionPos(cubePos, sectionIndex);
            complete &= readDataLayer(input, source, level, LightLayer.BLOCK, sectionPos);
            complete &= readDataLayer(input, source, level, LightLayer.SKY, sectionPos);
        }
        return complete;
    }

    private static void writeDataLayer(DataOutputStream output, ServerLevel level, LightLayer layer, SectionPos sectionPos) throws IOException {
        DataLayer data = level.getLightEngine().getLayerListener(layer).getDataLayerData(sectionPos);
        output.writeBoolean(data != null);
        if (data != null) {
            writeByteArray(output, data.getData());
        }
    }

    private static boolean readDataLayer(DataInputStream input, Path source, ServerLevel level, LightLayer layer, SectionPos sectionPos)
            throws IOException {
        if (!input.readBoolean()) {
            return false;
        }
        byte[] data = readByteArray(input, source, layer.name().toLowerCase(java.util.Locale.ROOT) + " light");
        if (data.length != DataLayer.SIZE) {
            throw new IOException("Invalid " + layer + " light layer size " + data.length + " in " + source);
        }
        level.getLightEngine().queueSectionData(layer, sectionPos, new DataLayer(data));
        return true;
    }

    private static SectionPos sectionPos(CubePos cubePos, int sectionIndex) {
        return SectionPos.of(Coords.cubeToSection(cubePos.getX(), Coords.indexToX(sectionIndex)),
                Coords.cubeToSection(cubePos.getY(), Coords.indexToY(sectionIndex)),
                Coords.cubeToSection(cubePos.getZ(), Coords.indexToZ(sectionIndex)));
    }

    private Path cubePath(CubePos pos) {
        Path region = root.resolve("r." + (pos.getX() >> REGION_SHIFT) + "." + (pos.getY() >> REGION_SHIFT) + "." + (pos.getZ() >> REGION_SHIFT));
        return region.resolve("c." + pos.getX() + "." + pos.getY() + "." + pos.getZ() + ".ccube");
    }

    private static void atomicReplace(Path temporary, Path destination) throws IOException {
        try {
            Files.move(temporary, destination, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
        } catch (AtomicMoveNotSupportedException ignored) {
            Files.move(temporary, destination, StandardCopyOption.REPLACE_EXISTING);
        }
    }

    private static void validateMagic(int magic, Path source) throws IOException {
        if (magic != MAGIC) {
            throw new IOException("Invalid cube storage magic in " + source);
        }
    }

    private static void validateVersion(int version, Path source) throws IOException {
        if (version != VERSION_SECTIONS_ONLY && version != VERSION_COMPLETE) {
            throw new IOException("Unsupported cube storage version " + version + " in " + source);
        }
    }

    private static void validatePosition(CubePos storedPos, CubePos expectedPos) throws IOException {
        if (!storedPos.equals(expectedPos)) {
            throw new IOException("Cube file position mismatch: expected " + expectedPos + ", found " + storedPos);
        }
    }

    private static void validateSectionCount(int sectionCount) throws IOException {
        if (sectionCount != CubicConstants.SECTION_COUNT) {
            throw new IOException("Cube section count mismatch: expected " + CubicConstants.SECTION_COUNT + ", found " + sectionCount);
        }
    }

    private static int readCount(DataInputStream input, Path source, String name) throws IOException {
        int count = input.readInt();
        if (count < 0 || count > MAX_COLLECTION_SIZE) {
            throw new IOException("Invalid " + name + " count " + count + " in " + source);
        }
        return count;
    }

    private static void writeByteArray(DataOutputStream output, byte[] bytes) throws IOException {
        if (bytes.length > MAX_SERIALIZED_BYTES) {
            throw new IOException("Serialized payload is too large: " + bytes.length + " bytes");
        }
        output.writeInt(bytes.length);
        output.write(bytes);
    }

    private static byte[] readByteArray(DataInputStream input, Path source, String name) throws IOException {
        int byteCount = input.readInt();
        if (byteCount < 0 || byteCount > MAX_SERIALIZED_BYTES) {
            throw new IOException("Invalid " + name + " payload size " + byteCount + " in " + source);
        }
        byte[] data = input.readNBytes(byteCount);
        if (data.length != byteCount) {
            throw new EOFException("Truncated " + name + " payload in " + source);
        }
        return data;
    }

    private static byte[] serializeSections(LevelCube cube) throws IOException {
        int expectedSize = 0;
        for (LevelChunkSection section : cube.getSections()) {
            expectedSize = Math.addExact(expectedSize, section.getSerializedSize());
        }
        if (expectedSize > MAX_SERIALIZED_BYTES) {
            throw new IOException("Cube section payload is too large: " + expectedSize + " bytes");
        }

        ByteBuf byteBuf = Unpooled.buffer(expectedSize, expectedSize);
        try {
            FriendlyByteBuf friendlyByteBuf = new FriendlyByteBuf(byteBuf);
            for (LevelChunkSection section : cube.getSections()) {
                section.write(friendlyByteBuf);
            }
            if (friendlyByteBuf.writerIndex() != expectedSize) {
                throw new IOException("Cube section payload size mismatch: expected " + expectedSize + ", wrote " + friendlyByteBuf.writerIndex());
            }

            byte[] output = new byte[expectedSize];
            friendlyByteBuf.getBytes(0, output);
            return output;
        } finally {
            byteBuf.release();
        }
    }

    private static LevelChunkSection[] deserializeSections(byte[] serialized, Registry<Biome> biomeRegistry) throws IOException {
        LevelChunkSection[] sections = new LevelChunkSection[CubicConstants.SECTION_COUNT];
        ByteBuf byteBuf = Unpooled.wrappedBuffer(serialized);
        try {
            FriendlyByteBuf friendlyByteBuf = new FriendlyByteBuf(byteBuf);
            for (int index = 0; index < sections.length; index++) {
                LevelChunkSection section = new LevelChunkSection(biomeRegistry);
                try {
                    section.read(friendlyByteBuf);
                } catch (RuntimeException exception) {
                    throw new IOException("Failed to decode cube section " + index, exception);
                }
                sections[index] = section;
            }
            if (friendlyByteBuf.readableBytes() != 0) {
                throw new IOException("Cube section payload has " + friendlyByteBuf.readableBytes() + " unread bytes");
            }
            return sections;
        } finally {
            byteBuf.release();
        }
    }

    private record StructureData(Map<Structure, StructureStart> starts, Map<Structure, it.unimi.dsi.fastutil.longs.LongSet> references) {}
}
