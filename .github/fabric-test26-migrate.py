#!/usr/bin/env python3
"""Port legacy NeoForge/older-Minecraft tests to Fabric and Minecraft 26.2."""

from pathlib import Path
import re


def update(path: str, transform) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    migrated = transform(text)
    target.write_text(migrated, encoding="utf-8")


def remove_exact(text: str, block: str) -> str:
    return text.replace(block, "")


def migrate_level_test(text: str) -> str:
    text = text.replace("import java.util.Collection;\n", "")
    text = text.replace("import net.neoforged.neoforge.entity.PartEntity;\n", "")
    if "import net.minecraft.world.attribute.EnvironmentAttributeSystem;\n" not in text:
        text = text.replace(
            "import net.minecraft.world.TickRateManager;\n",
            "import net.minecraft.world.TickRateManager;\nimport net.minecraft.world.attribute.EnvironmentAttributeSystem;\n",
            1,
        )

    text = re.sub(
        r"\n        @Override public Collection<PartEntity<\?>\> dragonParts\(\) \{\n            return List\.of\(\);\n        \}\n",
        "\n",
        text,
    )
    text = remove_exact(text, """
        @Override public void explode(
                @Nullable Entity source, @Nullable DamageSource damageSource, @Nullable ExplosionDamageCalculator damageCalculator, double x,
                double y, double z, float radius, boolean fire, ExplosionInteraction explosionInteraction, ParticleOptions smallExplosionParticles,
                ParticleOptions largeExplosionParticles, Holder<SoundEvent> explosionSound
        ) {

        }
""")
    for block in (
        """
        @Override public void setDayTimeFraction(float dayTimeFraction) {

        }
""",
        """
        @Override public float getDayTimeFraction() {
            return 0;
        }
""",
        """
        @Override public float getDayTimePerTick() {
            return 0;
        }
""",
        """
        @Override public void setDayTimePerTick(float dayTimePerTick) {

        }
""",
        """
        @Override public float getShade(Direction direction, boolean shade) {
            return 0;
        }
""",
    ):
        text = remove_exact(text, block)

    if "@Override public EnvironmentAttributeSystem environmentAttributes()" not in text:
        anchor = """
        @Override public ChunkSource getChunkSource() {
            return mockChunkSource;
        }
"""
        replacement = """
        @Override public EnvironmentAttributeSystem environmentAttributes() {
            return mock(EnvironmentAttributeSystem.class);
        }

        @Override public ChunkSource getChunkSource() {
            return mockChunkSource;
        }
"""
        if anchor not in text:
            raise SystemExit("Unable to add the Minecraft 26.2 environment attribute fixture")
        text = text.replace(anchor, replacement, 1)

    # getCurrentDifficultyAt moved from Level to ServerLevel in 26.2. This
    # Level-only fixture cannot test that server-only method.
    text = re.sub(
        r"\n    @Test\n    public void getCurrentDifficultyAt\(\) throws Exception \{.*?\n    \}\n(?=\})",
        "\n",
        text,
        flags=re.DOTALL,
    )
    return text


def migrate_parity_test(text: str) -> str:
    text = text.replace("import net.minecraft.core.HolderLookup;\n", "")
    text = text.replace("import net.minecraft.nbt.CompoundTag;\n", "")
    text = text.replace("import net.neoforged.neoforge.attachment.IAttachmentHolder;\n", "")

    text = re.sub(
        r"Stream\.concat\(Stream\.of\(ChunkAccess\.class\.getMethod\(\"getPos\"\),\n\s*// TODO need to check existence; these would fail on Fabric\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"writeAttachmentsToNBT\", HolderLookup\.Provider\.class\),\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"readAttachmentsFromNBT\", HolderLookup\.Provider\.class, CompoundTag\.class\),\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"getAttachmentHolder\"\), ChunkAccess\.class\.getDeclaredMethod\(\"getLevel\"\)\),\n\s*Arrays\.stream\(IAttachmentHolder\.class\.getMethods\(\)\)\)",
        'Stream.of(ChunkAccess.class.getMethod("getPos"), ChunkAccess.class.getDeclaredMethod("getLevel"))',
        text,
    )
    text = re.sub(
        r"Stream\.concat\(Stream\.of\(ChunkAccess\.class\.getMethod\(\"getPos\"\),\n\s*// TODO need to check existence; these would fail on Fabric\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"writeAttachmentsToNBT\", HolderLookup\.Provider\.class\),\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"readAttachmentsFromNBT\", HolderLookup\.Provider\.class, CompoundTag\.class\),\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"getAttachmentHolder\"\), LevelChunk\.class\.getMethod\(\"getAuxLightManager\", ChunkPos\.class\),\n\s*LevelChunk\.class\.getMethod\(\"setUnsavedListener\", LevelChunk\.UnsavedListener\.class\)\),\n\s*Arrays\.stream\(IAttachmentHolder\.class\.getMethods\(\)\)\)",
        'Stream.of(ChunkAccess.class.getMethod("getPos"), LevelChunk.class.getMethod("setUnsavedListener", LevelChunk.UnsavedListener.class))',
        text,
    )
    text = re.sub(
        r"Stream\.concat\(Stream\.of\(ChunkAccess\.class\.getMethod\(\"getPos\"\), ImposterProtoChunk\.class\.getMethod\(\"getWrapped\"\),\n\s*// TODO need to check existence; these would fail on Fabric\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"writeAttachmentsToNBT\", HolderLookup\.Provider\.class\),\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"readAttachmentsFromNBT\", HolderLookup\.Provider\.class, CompoundTag\.class\),\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"getAttachmentHolder\"\), ChunkAccess\.class\.getDeclaredMethod\(\"getLevel\"\)\),\n\s*Arrays\.stream\(IAttachmentHolder\.class\.getMethods\(\)\)\)",
        'Stream.of(ChunkAccess.class.getMethod("getPos"), ImposterProtoChunk.class.getMethod("getWrapped"), ChunkAccess.class.getDeclaredMethod("getLevel"))',
        text,
    )
    text = text.replace("//                IAttachmentHolder.class.getMethods()\n", "")
    if "IAttachmentHolder" in text or "writeAttachmentsToNBT" in text or "readAttachmentsFromNBT" in text:
        raise SystemExit("NeoForge attachment parity references remain after Fabric migration")
    return text


def migrate_client_cache_test(text: str) -> str:
    text = text.replace(
        "import io.github.opencubicchunks.cubicchunks.network.CCClientboundLevelCubeWithLightPacket;",
        "import io.github.opencubicchunks.cubicchunks.network.CCClientboundLevelCubePacketData;",
    )
    text = re.sub(
        r"new CCClientboundLevelCubeWithLightPacket\(([^)]+)\)",
        r"new CCClientboundLevelCubePacketData(\1)",
        text,
    )
    text = text.replace(".getCubeData().getReadBuffer()", ".getReadBuffer()")
    text = text.replace(".cubeData().getReadBuffer()", ".getReadBuffer()")
    return text


def migrate_progress_listener(text: str) -> str:
    text = text.replace("import net.minecraft.server.level.progress.ChunkProgressListener;\n", "")
    text = text.replace("import net.minecraft.world.level.ChunkPos;\n", "")
    text = text.replace(
        "public class DummyChunkProgressListener implements ChunkProgressListener, CloProgressListener {",
        "public class DummyChunkProgressListener implements CloProgressListener {",
    )
    for block in (
        """
    @Override public void updateSpawnPos(ChunkPos center) {

    }
""",
        """
    @Override public void onStatusChange(ChunkPos chunkPos, @Nullable ChunkStatus chunkStatus) {

    }
""",
        """
    @Override public void start() {

    }
""",
        """
    @Override public void stop() {

    }
""",
    ):
        text = remove_exact(text, block)
    return text


def migrate_distance_manager(text: str) -> str:
    text = text.replace("TicketType.START", "TicketType.FORCED")
    text = text.replace("ChunkPos.ZERO.toLong()", "ChunkPos.ZERO.pack()")
    text = text.replace(".pos.chunk().toLong()", ".pos.chunk().pack()")
    return text


def migrate_server_level(text: str) -> str:
    text = re.sub(
        r"\n    // TODO: Phase 3 - This is part of the neoforge API.*?\n    @Test\n    public void testVanillaInvalidateCapabilities\(\) throws Exception \{.*?\n    \}\n",
        "\n",
        text,
        flags=re.DOTALL,
    )
    return text


def migrate_chunk_tracker(text: str) -> str:
    text = text.replace("tracker.getLevel(testPos.toLong())", "tracker.getLevel(testPos.pack())")
    text = text.replace("testPos.x, testPos.z", "testPos.x(), testPos.z()")
    return text


def migrate_entity_test(text: str) -> str:
    return text.replace("EntityType.GIANT", "EntityType.ZOMBIE")


def migrate_cube_access_test(text: str) -> str:
    text = text.replace("import net.minecraft.core.Registry;\n", "")
    text = text.replace("import net.minecraft.world.level.biome.Biome;\n", "")
    if "import net.minecraft.world.level.chunk.PalettedContainerFactory;\n" not in text:
        text = text.replace(
            "import net.minecraft.world.level.chunk.LevelChunkSection;\n",
            "import net.minecraft.world.level.chunk.LevelChunkSection;\nimport net.minecraft.world.level.chunk.PalettedContainerFactory;\n",
            1,
        )
    text = text.replace("Registry<Biome> biomeRegistry", "PalettedContainerFactory palettedContainerFactory")
    text = text.replace("levelHeightAccessor, biomeRegistry, inhabitedTime", "levelHeightAccessor, palettedContainerFactory, inhabitedTime")
    return text


update("src/test/java/io/github/opencubicchunks/cubicchunks/test/world/level/TestCubicLevel.java", migrate_level_test)
update("src/test/java/io/github/opencubicchunks/cubicchunks/test/misc/TestVanillaCubicParity.java", migrate_parity_test)
update("src/test/java/io/github/opencubicchunks/cubicchunks/test/client/multiplayer/TestClientCubeCache.java", migrate_client_cache_test)
update("src/test/java/io/github/opencubicchunks/cubicchunks/testutils/DummyChunkProgressListener.java", migrate_progress_listener)
update("src/test/java/io/github/opencubicchunks/cubicchunks/test/server/level/TestCubicDistanceManager.java", migrate_distance_manager)
update("src/test/java/io/github/opencubicchunks/cubicchunks/test/server/level/TestCubicServerLevel.java", migrate_server_level)
update("src/test/java/io/github/opencubicchunks/cubicchunks/test/server/level/TestCubicChunkTracker.java", migrate_chunk_tracker)
update("src/test/java/io/github/opencubicchunks/cubicchunks/test/world/entity/TestEntity.java", migrate_entity_test)
update("src/test/java/io/github/opencubicchunks/cubicchunks/test/world/level/cube/TestCubeAccess.java", migrate_cube_access_test)

print("Applied Fabric and Minecraft 26.2 test-source migration")
