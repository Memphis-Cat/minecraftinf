#!/usr/bin/env python3
"""Finish cube persistence and shutdown draining for the Fabric 26.2 port."""

from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    raise SystemExit(f"Unable to migrate {label}: expected source block was not found")


storage_path = "src/main/java/io/github/opencubicchunks/cubicchunks/world/storage/CubeStorage.java"
text = read(storage_path)

imports_anchor = "import io.github.opencubicchunks.cubicchunks.CubicChunks;\n"
extra_imports = (
    "import io.github.opencubicchunks.cubicchunks.world.level.chunklike.CloAccess;\n"
    "import io.github.opencubicchunks.cubicchunks.world.level.cube.ProtoCube;\n"
)
if extra_imports not in text:
    text = text.replace(imports_anchor, imports_anchor + extra_imports, 1)
if "import net.minecraft.world.ticks.ProtoChunkTicks;\n" not in text:
    text = text.replace(
        "import net.minecraft.world.level.chunk.PalettedContainerFactory;\n",
        "import net.minecraft.world.level.chunk.PalettedContainerFactory;\nimport net.minecraft.world.ticks.ProtoChunkTicks;\n",
        1,
    )
if "import net.minecraft.world.level.chunk.status.ChunkStatus;\n" not in text:
    text = text.replace(
        "import net.minecraft.world.level.chunk.UpgradeData;\n",
        "import net.minecraft.world.level.chunk.UpgradeData;\n"
        "import net.minecraft.world.level.chunk.status.ChunkStatus;\n"
        "import net.minecraft.world.level.chunk.status.ChunkType;\n",
        1,
    )

text = text.replace(
    " * Version 2 stores every cube-owned runtime payload: block/biome section palettes, pending block\n"
    " * entities, scheduled block and fluid ticks, post-processing offsets, structure data, and queued\n"
    " * sky/block light layers. Vanilla columns remain authoritative for global column heightmaps and\n"
    " * POIs.\n",
    " * Version 3 also stores the persisted generation status, allowing ProtoCube states to survive\n"
    " * unloading and server shutdown without being promoted to full cubes. Vanilla columns remain\n"
    " * authoritative for global column heightmaps and POIs.\n",
)
text = text.replace(
    "    private static final int VERSION_COMPLETE = 2;\n",
    "    private static final int VERSION_COMPLETE = 2;\n    private static final int VERSION_STATUS = 3;\n",
)

text = replace_once(
    text,
    """    private final Path root;

    public CubeStorage(Path root) {
        this.root = root;
    }
""",
    """    private final Path root;
    private final ServerLevel level;
    private final Registry<Structure> structureRegistry;
    private final StructurePieceSerializationContext structureContext;

    public CubeStorage(Path root, ServerLevel level) {
        this.root = root;
        this.level = level;
        this.structureRegistry = level.registryAccess().lookupOrThrow(Registries.STRUCTURE);
        this.structureContext = StructurePieceSerializationContext.fromLevel(level);
    }
""",
    "CubeStorage server context",
)

text = replace_once(
    text,
    """    public synchronized boolean saveIfUnsaved(LevelCube cube) throws IOException {
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
""",
    """    public synchronized boolean saveIfUnsaved(CloAccess cube) throws IOException {
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

    public synchronized void save(CloAccess cube) throws IOException {
        if (!cube.cc_getCloPos().isCube()) {
            throw new IOException("CubeStorage cannot persist a column: " + cube.cc_getCloPos());
        }

        CubePos cubePos = cube.cc_getCloPos().cubePos();
        byte[] sectionData = serializeSections(cube);
        Path destination = cubePath(cubePos);
        Files.createDirectories(destination.getParent());
        Path temporary = destination.resolveSibling(destination.getFileName() + ".tmp");

        try {
            try (DataOutputStream output = new DataOutputStream(new BufferedOutputStream(Files.newOutputStream(temporary)))) {
                output.writeInt(MAGIC);
                output.writeInt(VERSION_STATUS);
                writeCommonHeader(output, cube, sectionData);
                output.writeUTF(cube.getPersistedStatus().getName());
                writePostProcessing(output, cube.getPostProcessing());
                writeBlockEntities(output, cube);
                ChunkAccess.PackedTicks ticks = cube.getTicksForSerialization(this.level.getGameTime());
                writeTicks(output, ticks.blocks(), BuiltInRegistries.BLOCK);
                writeTicks(output, ticks.fluids(), BuiltInRegistries.FLUID);
                writeStructures(output, cube);
                writeLightLayers(output, cube);
            }
            atomicReplace(temporary, destination);
        } catch (IOException | RuntimeException exception) {
            Files.deleteIfExists(temporary);
            throw exception;
        }
    }
""",
    "general cube save",
)

if "    public synchronized Optional<CloAccess> load(" not in text:
    start = text.index("    public synchronized Optional<ImposterProtoCube> load(")
    end = text.index("    private static void writeCommonHeader", start)
    new_load = """    public synchronized Optional<CloAccess> load(ServerLevel level, CubePos expectedPos) throws IOException {
        if (level != this.level) {
            throw new IOException("CubeStorage used with a different ServerLevel for " + expectedPos);
        }
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
            PalettedContainerFactory containerFactory = level.palettedContainerFactory();
            LevelChunkSection[] sections = deserializeSections(sectionData, containerFactory);

            if (version == VERSION_SECTIONS_ONLY) {
                LevelCube legacyCube = new LevelCube(level, expectedPos, UpgradeData.EMPTY, new LevelChunkTicks<>(), new LevelChunkTicks<>(),
                        inhabitedTime, sections, null, null);
                legacyCube.setLightCorrect(false);
                legacyCube.tryMarkSaved();
                return loadedFull(expectedPos, legacyCube);
            }

            ChunkStatus status = version >= VERSION_STATUS ? ChunkStatus.byName(input.readUTF()) : ChunkStatus.FULL;
            if (status == null) {
                throw new IOException("Unknown persisted cube status in " + source);
            }

            ShortList[] postProcessing = readPostProcessing(input, source);
            List<CompoundTag> blockEntities = readBlockEntities(input, source);
            List<SavedTick<Block>> blockTicks = readTicks(input, source, BuiltInRegistries.BLOCK, "block");
            List<SavedTick<Fluid>> fluidTicks = readTicks(input, source, BuiltInRegistries.FLUID, "fluid");
            StructureData structures = readStructures(input, source);
            boolean completeLightPayload = readLightLayers(input, source, expectedPos, level);
            if (input.read() != -1) {
                throw new IOException("Trailing data after cube payload in " + source);
            }

            if (status.getChunkType() == ChunkType.LEVELCHUNK) {
                LevelCube cube = new LevelCube(level, expectedPos, UpgradeData.EMPTY, new LevelChunkTicks<>(blockTicks),
                        new LevelChunkTicks<>(fluidTicks), inhabitedTime, sections, null, null);
                restoreCommonPayload(cube, postProcessing, blockEntities, structures, lightCorrect && completeLightPayload);
                cube.tryMarkSaved();
                return loadedFull(expectedPos, cube);
            }

            ProtoCube cube = new ProtoCube(expectedPos, UpgradeData.EMPTY, sections, ProtoChunkTicks.load(blockTicks),
                    ProtoChunkTicks.load(fluidTicks), level, containerFactory, null);
            cube.setPersistedStatus(status);
            cube.setInhabitedTime(inhabitedTime);
            restoreCommonPayload(cube, postProcessing, blockEntities, structures, lightCorrect && completeLightPayload);
            cube.tryMarkSaved();
            CubicChunks.LOGGER.info("Loaded persisted proto cube {} at status {}", expectedPos, status.getName());
            return Optional.of(cube);
        }
    }

    private static void restoreCommonPayload(
            CloAccess cube, ShortList[] postProcessing, List<CompoundTag> blockEntities, StructureData structures, boolean lightCorrect
    ) {
        for (int index = 0; index < postProcessing.length; index++) {
            ShortList offsets = postProcessing[index];
            if (offsets != null && !offsets.isEmpty()) {
                cube.addPackedPostProcess(offsets, index);
            }
        }
        blockEntities.forEach(cube::setBlockEntityNbt);
        cube.setAllStarts(structures.starts());
        cube.setAllReferences(structures.references());
        cube.setLightCorrect(lightCorrect);
    }

    private static Optional<CloAccess> loadedFull(CubePos expectedPos, LevelCube cube) {
        CubicChunks.LOGGER.info("Loaded persisted cube {}", expectedPos);
        return Optional.of(new ImposterProtoCube(cube, false));
    }

"""
    text = text[:start] + new_load + text[end:]

text = text.replace(
    "private static void writeCommonHeader(DataOutputStream output, LevelCube cube, byte[] sectionData)",
    "private static void writeCommonHeader(DataOutputStream output, CloAccess cube, byte[] sectionData)",
)
text = text.replace("CubePos cubePos = cube.cc_getCubePos();", "CubePos cubePos = cube.cc_getCloPos().cubePos();")
text = text.replace(
    "private static void writeBlockEntities(DataOutputStream output, LevelCube cube, ServerLevel level)",
    "private void writeBlockEntities(DataOutputStream output, CloAccess cube)",
)
text = text.replace(
    "cube.getBlockEntityNbtForSaving(blockPos, level.registryAccess())",
    "cube.getBlockEntityNbtForSaving(blockPos, this.level.registryAccess())",
)
text = text.replace(
    "private static void writeStructures(DataOutputStream output, LevelCube cube, ServerLevel level)",
    "private void writeStructures(DataOutputStream output, CloAccess cube)",
)
text = text.replace(
    "        Registry<Structure> registry = level.registryAccess().lookupOrThrow(Registries.STRUCTURE);\n"
    "        StructurePieceSerializationContext context = StructurePieceSerializationContext.fromLevel(level);\n",
    "",
)
text = text.replace("Identifier key = registry.getKey(entry.getKey());", "Identifier key = this.structureRegistry.getKey(entry.getKey());")
text = text.replace(
    "entry.getValue().createTag(context, entry.getValue().getChunkPos())",
    "entry.getValue().createTag(this.structureContext, entry.getValue().getChunkPos())",
)
text = text.replace(
    "private static StructureData readStructures(DataInputStream input, Path source, ServerLevel level)",
    "private StructureData readStructures(DataInputStream input, Path source)",
)
text = text.replace(
    "Structure structure = key == null ? null : registry.getValue(key);",
    "Structure structure = key == null ? null : this.structureRegistry.getValue(key);",
)
text = text.replace(
    "StructureStart.loadStaticStart(context, tag, level.getSeed())",
    "StructureStart.loadStaticStart(this.structureContext, tag, this.level.getSeed())",
)
text = text.replace(
    "private static void writeLightLayers(DataOutputStream output, LevelCube cube, ServerLevel level)",
    "private void writeLightLayers(DataOutputStream output, CloAccess cube)",
)
text = text.replace("writeDataLayer(output, level, LightLayer.BLOCK, sectionPos);", "writeDataLayer(output, this.level, LightLayer.BLOCK, sectionPos);")
text = text.replace("writeDataLayer(output, level, LightLayer.SKY, sectionPos);", "writeDataLayer(output, this.level, LightLayer.SKY, sectionPos);")
text = text.replace("private static byte[] serializeSections(LevelCube cube)", "private static byte[] serializeSections(CloAccess cube)")
text = text.replace(
    "if (version != VERSION_SECTIONS_ONLY && version != VERSION_COMPLETE) {",
    "if (version != VERSION_SECTIONS_ONLY && version != VERSION_COMPLETE && version != VERSION_STATUS) {",
)

for required in (
    "VERSION_STATUS = 3",
    "void save(CloAccess cube)",
    "Optional<CloAccess> load",
    "ProtoChunkTicks.load(blockTicks)",
    "loadedFull",
    "this.structureRegistry",
):
    if required not in text:
        raise SystemExit(f"CubeStorage persistence migration is incomplete: missing {required}")
write(storage_path, text)

mixin_path = "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinChunkMap.java"
text = read(mixin_path)
if "import it.unimi.dsi.fastutil.longs.LongSet;\n" not in text:
    text = text.replace(
        "import it.unimi.dsi.fastutil.longs.Long2ObjectLinkedOpenHashMap;\n",
        "import it.unimi.dsi.fastutil.longs.Long2ObjectLinkedOpenHashMap;\nimport it.unimi.dsi.fastutil.longs.LongSet;\n",
        1,
    )
text = replace_once(
    text,
    """    @Shadow @Final private Long2ObjectLinkedOpenHashMap<ChunkHolder> pendingUnloads;
    @Shadow @Final private ThreadedLevelLightEngine lightEngine;
""",
    """    @Shadow @Final private Long2ObjectLinkedOpenHashMap<ChunkHolder> pendingUnloads;
    @Shadow @Final private Long2ObjectLinkedOpenHashMap<ChunkHolder> updatingChunkMap;
    @Shadow @Final private LongSet toDrop;
    @Shadow @Final private ThreadedLevelLightEngine lightEngine;
""",
    "ChunkMap shutdown fields",
)
text = text.replace(
    "new CubeStorage(levelStorageAccess.getDimensionPath(level.dimension()).resolve(\"cubicchunks\").resolve(\"cubes\"))",
    "new CubeStorage(levelStorageAccess.getDimensionPath(level.dimension()).resolve(\"cubicchunks\").resolve(\"cubes\"), level)",
)
text = replace_once(
    text,
    """            CloPos cloPos = cloAccess.cc_getCloPos();
            if (cloAccess instanceof LevelCube levelCube) {
                levelCube.setLoaded(false);
                this.cc_save(levelCube);
                ((CubicServerLevel) this.level).cc_unloadClo(levelCube);
            } else {
""",
    """            CloPos cloPos = cloAccess.cc_getCloPos();
            if (cloPos.isCube()) {
                if (cloAccess instanceof LevelCube levelCube) {
                    levelCube.setLoaded(false);
                }
                this.cc_save(cloAccess);
                if (cloAccess instanceof LevelCube levelCube) {
                    ((CubicServerLevel) this.level).cc_unloadClo(levelCube);
                }
            } else {
""",
    "ProtoCube unload persistence",
)
text = text.replace(
    "Optional<ImposterProtoCube> storedCube = cc_cubeStorage.load(level, cloPos.cubePos());",
    "Optional<CloAccess> storedCube = cc_cubeStorage.load(level, cloPos.cubePos());",
)
text = replace_once(
    text,
    """    private boolean cc_save(CloAccess cloAccess) {
        LevelCube cube = cc_asLevelCube(cloAccess);
        if (cube == null || !cube.tryMarkSaved()) {
            return false;
        }

        try {
            cc_cubeStorage.save(cube);
            return true;
        } catch (Exception exception) {
            cube.markUnsaved();
            CubicChunks.LOGGER.error("Failed to save cube {}", cube.cc_getCubePos(), exception);
            return false;
        }
    }

    private static @Nullable LevelCube cc_asLevelCube(CloAccess cloAccess) {
        if (cloAccess instanceof LevelCube levelCube) {
            return levelCube;
        }
        if (cloAccess instanceof ImposterProtoClo imposter && imposter.cc_getWrappedClo() instanceof LevelCube levelCube) {
            return levelCube;
        }
        return null;
    }
""",
    """    private boolean cc_save(CloAccess cloAccess) {
        if (!cloAccess.cc_getCloPos().isCube() || !cloAccess.tryMarkSaved()) {
            return false;
        }

        try {
            cc_cubeStorage.save(cloAccess);
            return true;
        } catch (Exception exception) {
            cloAccess.markUnsaved();
            CubicChunks.LOGGER.error("Failed to save cube {}", cloAccess.cc_getCloPos(), exception);
            return false;
        }
    }
""",
    "general ChunkMap cube save",
)
shutdown = """    @Inject(method = "hasWork", at = @At("HEAD"))
    private void cc_queueTicketlessClosForShutdown(CallbackInfoReturnable<Boolean> cir) {
        if (((CanBeCubic) this.level).cc_isCubic() && !this.level.getServer().isRunning() && !this.updatingChunkMap.isEmpty()
                && this.toDrop.isEmpty() && !((ChunkMap) (Object) this).getDistanceManager().hasTickets()) {
            this.toDrop.addAll(this.updatingChunkMap.keySet());
        }
    }

"""
if "cc_queueTicketlessClosForShutdown" not in text:
    marker = "    @AddTransformToSets(ChunkToCloSet.ChunkMap_redirects.class)\n    @TransformFromMethod(\"saveAllChunks(Z)V\")\n"
    if marker not in text:
        raise SystemExit("Unable to add the shutdown drain before saveAllChunks")
    text = text.replace(marker, shutdown + marker, 1)
for required in (
    "new CubeStorage(levelStorageAccess.getDimensionPath(level.dimension()).resolve(\"cubicchunks\").resolve(\"cubes\"), level)",
    "Optional<CloAccess> storedCube",
    "cc_cubeStorage.save(cloAccess)",
    "cc_queueTicketlessClosForShutdown",
    "LongSet toDrop",
):
    if required not in text:
        raise SystemExit(f"ChunkMap persistence migration is incomplete: missing {required}")
if "cc_asLevelCube" in text:
    raise SystemExit("LevelCube-only save helper survived persistence migration")
write(mixin_path, text)

print("Applied Fabric 26.2 ProtoCube persistence and shutdown drain")
