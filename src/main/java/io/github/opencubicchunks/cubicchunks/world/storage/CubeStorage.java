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
import java.util.Optional;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.api.CubicConstants;
import io.github.opencubicchunks.cubicchunks.CubicChunks;
import io.github.opencubicchunks.cubicchunks.world.level.cube.ImposterProtoCube;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.chunk.LevelChunkSection;
import net.minecraft.world.level.chunk.UpgradeData;
import net.minecraft.world.ticks.LevelChunkTicks;

/**
 * Minimal versioned persistence for full cubes.
 * <p>
 * This is the Phase 1 storage baseline. It deliberately stores one palette payload per cube so save/reload behavior can be verified before
 * RegionLib batching, block entities, ticks, lighting, structures and heightmaps are added.
 * </p>
 */
public final class CubeStorage {
    private static final int MAGIC = 0x43435542; // CCUB
    private static final int VERSION = 1;
    private static final int MAX_SERIALIZED_BYTES = 64 * 1024 * 1024;
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
        CubePos cubePos = cube.cc_getCubePos();
        byte[] sectionData = serializeSections(cube);
        Path destination = cubePath(cubePos);
        Files.createDirectories(destination.getParent());
        Path temporary = destination.resolveSibling(destination.getFileName() + ".tmp");

        try (DataOutputStream output = new DataOutputStream(new BufferedOutputStream(Files.newOutputStream(temporary)))) {
            output.writeInt(MAGIC);
            output.writeInt(VERSION);
            output.writeInt(cubePos.getX());
            output.writeInt(cubePos.getY());
            output.writeInt(cubePos.getZ());
            output.writeInt(CubicConstants.SECTION_COUNT);
            output.writeLong(cube.getInhabitedTime());
            output.writeBoolean(cube.isLightCorrect());
            output.writeInt(sectionData.length);
            output.write(sectionData);
        }

        try {
            Files.move(temporary, destination, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
        } catch (AtomicMoveNotSupportedException ignored) {
            Files.move(temporary, destination, StandardCopyOption.REPLACE_EXISTING);
        }
    }

    public synchronized Optional<ImposterProtoCube> load(ServerLevel level, CubePos expectedPos) throws IOException {
        Path source = cubePath(expectedPos);
        if (!Files.isRegularFile(source)) {
            return Optional.empty();
        }

        try (DataInputStream input = new DataInputStream(new BufferedInputStream(Files.newInputStream(source)))) {
            validateMagic(input.readInt(), source);
            validateVersion(input.readInt(), source);
            validatePosition(CubePos.of(input.readInt(), input.readInt(), input.readInt()), expectedPos);
            validateSectionCount(input.readInt());

            long inhabitedTime = input.readLong();
            boolean lightCorrect = input.readBoolean();
            byte[] sectionData = readSectionData(input, source);
            Registry<Biome> biomeRegistry = level.registryAccess().lookupOrThrow(Registries.BIOME);
            LevelChunkSection[] sections = deserializeSections(sectionData, biomeRegistry);
            LevelCube cube = new LevelCube(level, expectedPos, UpgradeData.EMPTY, new LevelChunkTicks<>(), new LevelChunkTicks<>(), inhabitedTime,
                    sections, null, null);
            cube.setLightCorrect(lightCorrect);
            cube.tryMarkSaved();
            CubicChunks.LOGGER.info("Loaded persisted cube {}", expectedPos);
            return Optional.of(new ImposterProtoCube(cube, false));
        }
    }

    private Path cubePath(CubePos pos) {
        Path region = root.resolve("r." + (pos.getX() >> REGION_SHIFT) + "." + (pos.getY() >> REGION_SHIFT) + "." + (pos.getZ() >> REGION_SHIFT));
        return region.resolve("c." + pos.getX() + "." + pos.getY() + "." + pos.getZ() + ".ccube");
    }

    private static void validateMagic(int magic, Path source) throws IOException {
        if (magic != MAGIC) {
            throw new IOException("Invalid cube storage magic in " + source);
        }
    }

    private static void validateVersion(int version, Path source) throws IOException {
        if (version != VERSION) {
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

    private static byte[] readSectionData(DataInputStream input, Path source) throws IOException {
        int byteCount = input.readInt();
        if (byteCount < 0 || byteCount > MAX_SERIALIZED_BYTES) {
            throw new IOException("Invalid cube section payload size " + byteCount + " in " + source);
        }

        byte[] sectionData = input.readNBytes(byteCount);
        if (sectionData.length != byteCount) {
            throw new EOFException("Truncated cube section payload in " + source);
        }
        if (input.read() != -1) {
            throw new IOException("Trailing data after cube payload in " + source);
        }
        return sectionData;
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
}
