package io.github.opencubicchunks.cubicchunks.client.multiplayer;

import static io.github.notstirred.dasm.api.annotations.transform.Visibility.PUBLIC;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReferenceArray;
import java.util.function.Consumer;

import javax.annotation.Nullable;

import io.github.notstirred.dasm.api.annotations.Dasm;
import io.github.notstirred.dasm.api.annotations.selector.Ref;
import io.github.notstirred.dasm.api.annotations.transform.TransformFromMethod;
import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.api.CubicConstants;
import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cubicchunks.mixin.dasmsets.ChunkToCubeSet;
import io.github.opencubicchunks.cubicchunks.world.level.cube.CubeSource;
import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;
import it.unimi.dsi.fastutil.longs.LongOpenHashSet;
import net.minecraft.client.multiplayer.ClientChunkCache;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.SectionPos;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.protocol.game.ClientboundLevelChunkPacketData;
import net.minecraft.world.level.chunk.LevelChunkSection;
import net.minecraft.world.level.levelgen.Heightmap;

public interface ClientCubeCache extends CubeSource {
    void cc_drop(CubePos chunkPos);

    void cc_replaceBiomes(int x, int y, int z, FriendlyByteBuf buffer);

    @Nullable LevelCube cc_replaceWithPacketData(
            int x, int y, int z, FriendlyByteBuf buffer, Map<Heightmap.Types, long[]> map,
            Consumer<ClientboundLevelChunkPacketData.BlockEntityTagOutput> consumer
    );

    void cc_updateViewCenter(int x, int y, int z);

    void cc_updateViewRadius(int viewDistance);

    @Dasm(ChunkToCubeSet.class)
    final class Storage {
        public final AtomicReferenceArray<LevelCube> chunks;
        final LongOpenHashSet loadedEmptySections = new LongOpenHashSet();
        public final int cubeRadius;
        private final int viewRange;
        public volatile int viewCenterX;
        public volatile int viewCenterY;
        public volatile int viewCenterZ;
        public int chunkCount;
        final ClientLevel level;

        public Storage(int chunkRadius, ClientLevel clientLevel) {
            this.cubeRadius = chunkRadius;
            this.viewRange = chunkRadius * 2 + 1;
            this.chunks = new AtomicReferenceArray<>(this.viewRange * this.viewRange * this.viewRange);
            this.level = clientLevel;
        }

        public int getIndex(int x, int y, int z) {
            return Math.floorMod(z, this.viewRange) * this.viewRange * this.viewRange + Math.floorMod(y, this.viewRange) * this.viewRange
                    + Math.floorMod(x, this.viewRange);
        }

        public @Nullable LevelCube replace(int chunkIndex, @Nullable LevelCube chunk) {
            LevelCube previous = this.chunks.getAndSet(chunkIndex, chunk);
            if (previous == chunk) {
                return previous;
            }
            if (previous != null) {
                --this.chunkCount;
                this.dropEmptySections(previous);
                previous.clearAllBlockEntities();
            }

            if (chunk != null) {
                ++this.chunkCount;
                this.addEmptySections(chunk);
            }
            return previous;
        }

        public boolean drop(int chunkIndex, LevelCube chunk) {
            if (!this.chunks.compareAndSet(chunkIndex, chunk, null)) {
                return false;
            }
            this.chunkCount--;
            this.dropEmptySections(chunk);
            chunk.clearAllBlockEntities();
            return true;
        }

        public void onSectionEmptinessChanged(int x, int y, int z, boolean isEmpty) {
            if (this.inRange(x, y, z)) {
                long i = SectionPos.asLong(x, y, z);
                if (isEmpty) {
                    this.loadedEmptySections.add(i);
                } else if (this.loadedEmptySections.remove(i)) {
                    this.level.onSectionBecomingNonEmpty(i);
                }
            }
        }

        public void dropEmptySections(LevelCube chunk) {
            CubePos cubePos = chunk.cc_getCubePos();

            for (int dx = 0; dx < CubicConstants.DIAMETER_IN_SECTIONS; dx++) {
                for (int dy = 0; dy < CubicConstants.DIAMETER_IN_SECTIONS; dy++) {
                    for (int dz = 0; dz < CubicConstants.DIAMETER_IN_SECTIONS; dz++) {
                        long sectionPosLong = SectionPos.asLong(Coords.cubeToSection(cubePos.getX(), dx), Coords.cubeToSection(cubePos.getY(), dy),
                                Coords.cubeToSection(cubePos.getZ(), dz));
                        this.loadedEmptySections.remove(sectionPosLong);
                    }
                }
            }
        }

        public void addEmptySections(LevelCube chunk) {
            CubePos cubePos = chunk.cc_getCubePos();
            LevelChunkSection[] chunkSections = chunk.getSections();

            for (int dx = 0; dx < CubicConstants.DIAMETER_IN_SECTIONS; dx++) {
                for (int dy = 0; dy < CubicConstants.DIAMETER_IN_SECTIONS; dy++) {
                    for (int dz = 0; dz < CubicConstants.DIAMETER_IN_SECTIONS; dz++) {
                        LevelChunkSection chunkSection = chunkSections[Coords.sectionToIndex(dx, dy, dz)];
                        long sectionPosLong = SectionPos.asLong(Coords.cubeToSection(cubePos.getX(), dx), Coords.cubeToSection(cubePos.getY(), dy),
                                Coords.cubeToSection(cubePos.getZ(), dz));
                        if (chunkSection.hasOnlyAir()) {
                            this.loadedEmptySections.add(sectionPosLong);
                        }
                    }
                }
            }
        }

        public void refreshEmptySections(LevelCube chunk) {
            CubePos cubePos = chunk.cc_getCubePos();
            LevelChunkSection[] chunkSections = chunk.getSections();

            for (int dx = 0; dx < CubicConstants.DIAMETER_IN_SECTIONS; dx++) {
                for (int dy = 0; dy < CubicConstants.DIAMETER_IN_SECTIONS; dy++) {
                    for (int dz = 0; dz < CubicConstants.DIAMETER_IN_SECTIONS; dz++) {
                        LevelChunkSection chunkSection = chunkSections[Coords.sectionToIndex(dx, dy, dz)];
                        long sectionPosLong = SectionPos.asLong(Coords.cubeToSection(cubePos.getX(), dx), Coords.cubeToSection(cubePos.getY(), dy),
                                Coords.cubeToSection(cubePos.getZ(), dz));
                        if (chunkSection.hasOnlyAir()) {
                            this.loadedEmptySections.add(sectionPosLong);
                        } else if (this.loadedEmptySections.remove(sectionPosLong)) {
                            this.level.onSectionBecomingNonEmpty(sectionPosLong);
                        }
                    }
                }
            }
        }

        public boolean inRange(int x, int y, int z) {
            return Math.abs(x - this.viewCenterX) <= this.cubeRadius && Math.abs(y - this.viewCenterY) <= this.cubeRadius
                    && Math.abs(z - this.viewCenterZ) <= this.cubeRadius;
        }

        @TransformFromMethod(owner = @Ref(ClientChunkCache.Storage.class), value = "getChunk(I)Lnet/minecraft/world/level/chunk/LevelChunk;", visibility = PUBLIC)
        public native @Nullable LevelCube getChunk(int chunkIndex);

        public void dumpChunks(String filePath) {
            Path output = Path.of(filePath);
            try {
                Path parent = output.getParent();
                if (parent != null) {
                    Files.createDirectories(parent);
                }
                try (BufferedWriter writer = Files.newBufferedWriter(output, StandardCharsets.UTF_8)) {
                    writer.write("index\tcube_x\tcube_y\tcube_z\tempty_sections\ttotal_sections");
                    writer.newLine();
                    for (int index = 0; index < this.chunks.length(); ++index) {
                        LevelCube cube = this.chunks.get(index);
                        if (cube == null) {
                            continue;
                        }
                        CubePos cubePos = cube.cc_getCubePos();
                        int emptySections = 0;
                        LevelChunkSection[] sections = cube.getSections();
                        for (LevelChunkSection section : sections) {
                            if (section.hasOnlyAir()) {
                                ++emptySections;
                            }
                        }
                        writer.write(index + "\t" + cubePos.getX() + "\t" + cubePos.getY() + "\t" + cubePos.getZ() + "\t" + emptySections + "\t"
                                + sections.length);
                        writer.newLine();
                    }
                }
            } catch (IOException exception) {
                throw new UncheckedIOException("Failed to dump client cube cache to " + output, exception);
            }
        }
    }
}
