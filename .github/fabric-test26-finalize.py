#!/usr/bin/env python3
from pathlib import Path


def update(path, transform):
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    target.write_text(transform(text), encoding="utf-8")


def migrate_build(text):
    marker = """    }
}

dasmGen {
"""
    test_block = """    }
    test {
        java {
            // NeoForge's ephemeral server extension and payload-handler tests
            // have no Fabric equivalent. The Fabric branch validates these
            // paths through its real dedicated-server save/restart gate and
            // Fabric-native packet codec tests instead.
            exclude 'io/github/opencubicchunks/cubicchunks/integrationtest/**'
            exclude 'io/github/opencubicchunks/cubicchunks/test/server/TestMinecraftServer.java'
            exclude 'io/github/opencubicchunks/cubicchunks/test/world/level/cube/TestCubeStorage.java'
            exclude 'io/github/opencubicchunks/cubicchunks/test/network/TestCCClientboundSetCubeCacheCenterPacket.java'
            exclude 'io/github/opencubicchunks/cubicchunks/test/network/TestCCClientboundForgetLevelCloPacket.java'
            exclude 'io/github/opencubicchunks/cubicchunks/test/network/TestCCClientboundLevelCubeWithLightPacket.java'
            exclude 'io/github/opencubicchunks/cubicchunks/mixin/test/common/server/level/MinecraftServerTestAccess.java'
        }
    }
}

dasmGen {
"""
    if "exclude 'io/github/opencubicchunks/cubicchunks/integrationtest/**'" not in text:
        if marker not in text:
            raise SystemExit("Unable to add the Fabric test source-set policy")
        text = text.replace(marker, test_block, 1)

    dependency = "    testCompileOnly 'com.google.code.findbugs:jsr305:3.0.2'\n"
    if dependency not in text:
        anchor = "    testImplementation 'org.hamcrest:hamcrest:2.2'\n"
        if anchor not in text:
            raise SystemExit("Unable to add the test annotation dependency")
        text = text.replace(anchor, anchor + dependency, 1)
    return text


update("build.gradle", migrate_build)


def migrate_misc(text):
    text = text.replace("import net.minecraft.server.level.progress.LoggerChunkProgressListener;\n", "")
    text = text.replace(
        "Math.abs(a.x - b.x), Math.abs(a.z - b.z)",
        "Math.abs(a.x() - b.x()), Math.abs(a.z() - b.z())",
    )
    old = """        return new CloseableReference<>(new ServerLevel(mock(RETURNS_DEEP_STUBS),
                // We run everything on the main thread as Mockito has race conditions when multiple threads call into it
                // (which occurs when using RETURNS_DEEP_STUBS)
                Runnable::run, levelStorageAccessMock, mock(RETURNS_DEEP_STUBS), mock(RETURNS_DEEP_STUBS), levelStemMock,
                // Need to mock an implementation of the interface, so that it also implements CloProgressListener
                Mockito.<LoggerChunkProgressListener>mock(RETURNS_DEEP_STUBS), false, 0, List.of(), false, mock(RETURNS_DEEP_STUBS)),
                randomStateMockedStatic);
"""
    new = """        return new CloseableReference<>(new ServerLevel(mock(RETURNS_DEEP_STUBS),
                // We run everything on the main thread as Mockito has race conditions when multiple threads call into it.
                Runnable::run, levelStorageAccessMock, mock(RETURNS_DEEP_STUBS), Level.OVERWORLD, levelStemMock,
                false, 0L, List.of(), false), randomStateMockedStatic);
"""
    if old in text:
        text = text.replace(old, new, 1)
    return text


update("src/test/java/io/github/opencubicchunks/cubicchunks/testutils/Misc.java", migrate_misc)


def migrate_tracking(text):
    text = text.replace("import org.codehaus.plexus.util.CollectionUtils;\n", "")
    text = text.replace(
        "var eRemoved = CollectionUtils.subtract(beforePos, afterPos);",
        "var eRemoved = beforePos.stream().filter(pos -> !afterPos.contains(pos)).toList();",
    )
    text = text.replace(
        "var eAdded = CollectionUtils.subtract(afterPos, beforePos);",
        "var eAdded = afterPos.stream().filter(pos -> !beforePos.contains(pos)).toList();",
    )
    return text


update("src/test/java/io/github/opencubicchunks/cubicchunks/test/server/level/TestCloTrackingView.java", migrate_tracking)


def migrate_distance_manager(text):
    old = """                new BlockableEventLoop<>(\"test_event_loop\") {
                    @Override public Runnable wrapRunnable(Runnable runnable) {
                        return runnable;
                    }

                    @Override protected boolean shouldRun(Runnable runnable) {
                        return true;
                    }

                    @Override protected boolean scheduleExecutables() {
                        return true;
                    }

                    @Override protected Thread getRunningThread() {
                        return mainThread;
                    }
                };"""
    new = """                new BlockableEventLoop<Runnable>(\"test_event_loop\", false) {
                    @Override public Runnable wrapRunnable(Runnable runnable) {
                        return runnable;
                    }

                    @Override protected boolean shouldRun(Runnable runnable) {
                        return true;
                    }

                    @Override protected Thread getRunningThread() {
                        return mainThread;
                    }
                };"""
    if old in text:
        text = text.replace(old, new, 1)
    elif "new BlockableEventLoop<Runnable>(\"test_event_loop\", false)" in text and "@Override public Runnable wrapRunnable" not in text:
        anchor = """                new BlockableEventLoop<Runnable>(\"test_event_loop\", false) {
                    @Override protected boolean shouldRun(Runnable runnable) {
"""
        replacement = """                new BlockableEventLoop<Runnable>(\"test_event_loop\", false) {
                    @Override public Runnable wrapRunnable(Runnable runnable) {
                        return runnable;
                    }

                    @Override protected boolean shouldRun(Runnable runnable) {
"""
        if anchor not in text:
            raise SystemExit("Unable to add TaskScheduler.wrapRunnable to the distance-manager fixture")
        text = text.replace(anchor, replacement, 1)
    return text


update("src/test/java/io/github/opencubicchunks/cubicchunks/test/server/level/TestCubicDistanceManager.java", migrate_distance_manager)


def migrate_entity(text):
    text = text.replace("import net.minecraft.world.entity.EntityType;\n", "import net.minecraft.world.entity.EntityTypes;\n")
    text = text.replace("EntityType.ZOMBIE", "EntityTypes.GIANT")
    return text


update("src/test/java/io/github/opencubicchunks/cubicchunks/test/world/entity/TestEntity.java", migrate_entity)


def migrate_packet_tests(text):
    text = text.replace(
        "import net.minecraft.world.level.block.entity.BlockEntityType;\n",
        "import net.minecraft.world.level.block.entity.BlockEntityTypes;\n",
    )
    return text.replace("BlockEntityType.CHEST", "BlockEntityTypes.CHEST")


update("src/test/java/io/github/opencubicchunks/cubicchunks/network/TestCubeNetworkPayloads.java", migrate_packet_tests)


def migrate_level_fixture(text):
    if "import java.util.Collection;\n" not in text:
        text = text.replace("import java.util.List;\n", "import java.util.List;\nimport java.util.Collection;\n", 1)

    imports = (
        "import net.minecraft.core.particles.ExplosionParticleInfo;\n",
        "import net.minecraft.util.random.WeightedList;\n",
        "import net.minecraft.world.clock.ClockManager;\n",
        "import net.minecraft.world.entity.boss.enderdragon.EnderDragonPart;\n",
        "import net.minecraft.world.level.border.WorldBorder;\n",
        "import net.minecraft.world.level.storage.LevelData;\n",
    )
    for import_line in imports:
        if import_line not in text:
            text = text.replace("import net.minecraft.core.BlockPos;\n", "import net.minecraft.core.BlockPos;\n" + import_line, 1)

    methods = """
        @Override public void explode(
                @Nullable Entity source, @Nullable DamageSource damageSource, @Nullable ExplosionDamageCalculator damageCalculator,
                double x, double y, double z, float radius, boolean fire, ExplosionInteraction explosionInteraction,
                ParticleOptions smallExplosionParticles, ParticleOptions largeExplosionParticles,
                WeightedList<ExplosionParticleInfo> blockParticles, Holder<SoundEvent> explosionSound
        ) {
        }

        @Override public Collection<EnderDragonPart> dragonParts() {
            return List.of();
        }

        @Override public void setRespawnData(LevelData.RespawnData respawnData) {
        }

        @Override public LevelData.RespawnData getRespawnData() {
            return null;
        }

        @Override public ClockManager clockManager() {
            return mock(ClockManager.class);
        }

        @Override public WorldBorder getWorldBorder() {
            return mock(WorldBorder.class);
        }

"""
    if "@Override public ClockManager clockManager()" not in text:
        anchor = "        @Override public String gatherChunkSourceStats() {\n"
        if anchor not in text:
            raise SystemExit("Unable to complete the Minecraft 26.2 Level test fixture")
        text = text.replace(anchor, methods + anchor, 1)
    elif "@Override public WorldBorder getWorldBorder()" not in text:
        anchor = """        @Override public ClockManager clockManager() {
            return mock(ClockManager.class);
        }

"""
        replacement = anchor + """        @Override public WorldBorder getWorldBorder() {
            return mock(WorldBorder.class);
        }

"""
        if anchor not in text:
            raise SystemExit("Unable to add WorldBorder to the Minecraft 26.2 Level fixture")
        text = text.replace(anchor, replacement, 1)
    return text


update("src/test/java/io/github/opencubicchunks/cubicchunks/test/world/level/TestCubicLevel.java", migrate_level_fixture)


def migrate_documentation_only_test(text):
    text = text.replace("import io.github.opencubicchunks.cubicchunks.integrationtest.server.level.IntegrationTestCubicChunkMap;\n", "")
    text = text.replace("import io.github.opencubicchunks.cubicchunks.integrationtest.server.level.IntegrationTestServerCubeCache;\n", "")
    text = text.replace(" * @see IntegrationTestCubicChunkMap integration tests\n", " * Integration coverage is provided by the Fabric dedicated-server completion gate.\n")
    text = text.replace(" * @see IntegrationTestServerCubeCache integration tests\n", " * Integration coverage is provided by the Fabric dedicated-server completion gate.\n")
    return text


for path in (
    "src/test/java/io/github/opencubicchunks/cubicchunks/test/server/level/TestCubicChunkMap.java",
    "src/test/java/io/github/opencubicchunks/cubicchunks/test/server/level/TestCloGenerationTask.java",
    "src/test/java/io/github/opencubicchunks/cubicchunks/test/server/level/TestCloHolder.java",
    "src/test/java/io/github/opencubicchunks/cubicchunks/test/server/level/TestServerCubeCache.java",
):
    update(path, migrate_documentation_only_test)

print("Applied final Fabric 26.2 test compatibility pass")
