from pathlib import Path

ROOT = Path(".")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


# Remove optional 1.21-era loading-screen UI and old loader-specific sources from the 26.2 compile set.
build = "build.gradle"
text = read(build)
needle = """            exclude 'io/github/opencubicchunks/cubicchunks/movetoforgesourcesetlater/**'
            exclude 'io/github/opencubicchunks/cubicchunks/mixin/core/forge/**'
"""
replacement = """            exclude 'io/github/opencubicchunks/cubicchunks/movetoforgesourcesetlater/**'
            exclude 'io/github/opencubicchunks/cubicchunks/mixin/core/forge/**'
            exclude 'io/github/opencubicchunks/cubicchunks/mixin/core/common/movetoforgesourcesetlater/**'
            exclude 'io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/progress/**'
            exclude 'io/github/opencubicchunks/cubicchunks/mixin/core/client/gui/**'
            exclude 'io/github/opencubicchunks/cubicchunks/mixin/core/client/worldselection/**'
            exclude 'io/github/opencubicchunks/cubicchunks/client/gui/**'
"""
if needle in text:
    text = text.replace(needle, replacement, 1)
write(build, text)

# Simple public namespace moves in 26.2.
for java in (ROOT / "src/main/java").rglob("*.java"):
    text = java.read_text(encoding="utf-8")
    text = text.replace("import net.minecraft.Util;", "import net.minecraft.util.Util;")
    text = text.replace("import net.minecraft.world.level.GameRules;", "import net.minecraft.world.level.gamerules.GameRules;")
    java.write_text(text, encoding="utf-8")

# Progress listeners no longer participate in ServerLevel/ChunkMap construction in 26.2.
path = "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/dasmsets/GlobalSet.java"
text = read(path)
for line in (
    "import io.github.opencubicchunks.cubicchunks.server.level.progress.CloProgressListener;\n",
    "import net.minecraft.server.level.progress.ChunkProgressListener;\n",
    "import net.minecraft.server.level.progress.StoringChunkProgressListener;\n",
):
    text = text.replace(line, "")
start = text.find("    @TypeRedirect(from = @Ref(ChunkProgressListener.class)")
if start >= 0:
    end = text.find("    @TypeRedirect(from = @Ref(ChunkStatusUpdateListener.class)", start)
    if end < 0:
        raise SystemExit("Unable to remove the legacy progress-listener redirect")
    text = text[:start] + text[end:]
text = text.replace(
    """
    @IntraOwnerContainer(@Ref(StoringChunkProgressListener.class))
    class StoringChunkProgressListener_redirects {}
""",
    "\n",
)
write(path, text)

path = "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/dasmsets/ChunkToCloSet.java"
text = read(path)
for line in (
    "import net.minecraft.server.level.progress.LoggerChunkProgressListener;\n",
    "import net.minecraft.server.level.progress.ProcessorChunkProgressListener;\n",
    "import net.minecraft.server.level.progress.StoringChunkProgressListener;\n",
    "import net.minecraft.world.level.chunk.storage.ChunkStorage;\n",
):
    text = text.replace(line, "")
if "import net.minecraft.world.level.chunk.storage.SimpleRegionStorage;" not in text:
    anchor = "import net.minecraft.world.level.chunk.status.ChunkStatus;\n"
    text = text.replace(anchor, anchor + "import net.minecraft.world.level.chunk.storage.SimpleRegionStorage;\n")
text = text.replace("@IntraOwnerContainer(@Ref(ChunkStorage.class))", "@IntraOwnerContainer(@Ref(SimpleRegionStorage.class))")
text = text.replace("class ChunkStorage_redirects {}", "class SimpleRegionStorage_redirects {}")
text = text.replace("class ChunkMap_redirects extends ChunkStorage_redirects {}", "class ChunkMap_redirects extends SimpleRegionStorage_redirects {}")
for block in (
    """    @IntraOwnerContainer(@Ref(ProcessorChunkProgressListener.class))
    class ProcessorChunkProgressListener_redirects {}

""",
    """    @IntraOwnerContainer(@Ref(LoggerChunkProgressListener.class))
    class LoggerChunkProgressListener_redirects {}

""",
    """    @IntraOwnerContainer(@Ref(StoringChunkProgressListener.class))
    class StoringChunkProgressListener_redirects {}

""",
):
    text = text.replace(block, "")
text = text.replace(
    "@IntraOwnerContainer(@Ref(ChunkMap.TrackedEntity.class))",
    "@IntraOwnerContainer(@Ref(string = \"net.minecraft.server.level.ChunkMap$TrackedEntity\"))",
)
text = text.replace("import net.minecraft.core.Registry;\n", "")
text = text.replace("import net.minecraft.world.level.biome.Biome;\n", "")
if "import net.minecraft.world.level.chunk.PalettedContainerFactory;" not in text:
    text = text.replace(
        "import net.minecraft.world.level.chunk.LevelChunkSection;\n",
        "import net.minecraft.world.level.chunk.LevelChunkSection;\nimport net.minecraft.world.level.chunk.PalettedContainerFactory;\n",
    )
text = text.replace("Lnet/minecraft/core/Registry;", "Lnet/minecraft/world/level/chunk/PalettedContainerFactory;")
text = text.replace("Registry<Biome> biomeRegistry", "PalettedContainerFactory containerFactory")
write(path, text)

# Retarget the old ChunkStorage mixin to SimpleRegionStorage, which owns the same IO methods in 26.2.
path = "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/world/level/chunk/storage/MixinChunkStorage.java"
text = read(path)
text = text.replace(
    "import net.minecraft.world.level.chunk.storage.ChunkStorage;",
    "import net.minecraft.world.level.chunk.storage.SimpleRegionStorage;",
)
text = text.replace("@Ref(ChunkStorage.class)", "@Ref(SimpleRegionStorage.class)")
text = text.replace("@Mixin(ChunkStorage.class)", "@Mixin(SimpleRegionStorage.class)")
text = text.replace("ChunkToCloSet.ChunkStorage_redirects", "ChunkToCloSet.SimpleRegionStorage_redirects")
write(path, text)

# ServerLevel constructor dropped progress listeners and RandomSequences.
path = "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinServerLevel.java"
text = read(path)
text = text.replace("import net.minecraft.server.level.progress.ChunkProgressListener;\n", "")
text = text.replace("import net.minecraft.world.RandomSequences;\n", "")
text = text.replace(
    """            ResourceKey dimension, LevelStem levelStem, ChunkProgressListener progressListener, boolean isDebug, long biomeZoomSeed,
            List customSpawners, boolean tickTime, RandomSequences randomSequences, CallbackInfo ci
""",
    """            ResourceKey dimension, LevelStem levelStem, boolean isDebug, long biomeZoomSeed, List customSpawners, boolean tickTime, CallbackInfo ci
""",
)
write(path, text)

# ServerChunkCache constructor dropped the progress listener. MinecraftServer is the public main-thread event loop.
path = "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinServerChunkCache.java"
text = read(path)
text = text.replace("import net.minecraft.server.level.progress.ChunkProgressListener;\n", "")
text = text.replace("    @Shadow @Final private ServerChunkCache.MainThreadExecutor mainThreadProcessor;\n", "")
text = text.replace(
    """            boolean sync, ChunkProgressListener progressListener, ChunkStatusUpdateListener chunkStatusListener, Supplier overworldDataStorage,
            CallbackInfo ci
""",
    """            boolean sync, ChunkStatusUpdateListener chunkStatusListener, Supplier overworldDataStorage, CallbackInfo ci
""",
)
text = text.replace("this.mainThreadProcessor", "this.level.getServer()")
write(path, text)

# ChunkMap no longer stores a progress listener and extends SimpleRegionStorage directly.
path = "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinChunkMap.java"
text = read(path)
text = text.replace("import io.github.opencubicchunks.cubicchunks.server.level.progress.CloProgressListener;\n", "")
text = text.replace("import net.minecraft.server.level.progress.ChunkProgressListener;\n", "")
text = text.replace("import net.neoforged.neoforge.network.PacketDistributor;\n", "")
if "import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;" not in text:
    text = text.replace(
        "import net.minecraft.ReportedException;\n",
        "import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;\nimport net.minecraft.ReportedException;\n",
    )
text = text.replace("    @Shadow @Final private ChunkMap.DistanceManager distanceManager;\n", "")
text = text.replace(
    """    // TODO this one being on GlobalSet is a bit jank
    @AddFieldToSets(containers = GlobalSet.ChunkMap_redirects.class, field = "progressListener:Lnet/minecraft/server/level/progress/ChunkProgressListener;")
    private CloProgressListener cc_progressListener;
""",
    "",
)
text = text.replace(
    """            ChunkGenerator generator, ChunkProgressListener progressListener, ChunkStatusUpdateListener chunkStatusListener,
            Supplier overworldDataStorage, TicketStorage ticketStorage, int serverViewDistance, boolean sync, CallbackInfo ci
""",
    """            ChunkGenerator generator, ChunkStatusUpdateListener chunkStatusListener, Supplier overworldDataStorage,
            TicketStorage ticketStorage, int serverViewDistance, boolean sync, CallbackInfo ci
""",
)
text = text.replace("            cc_progressListener = ((CloProgressListener) progressListener);\n", "")
text = text.replace(
    "            ((MarkableAsCubic) distanceManager).cc_setCubic();",
    "            ((MarkableAsCubic) ((ChunkMap) (Object) this).getDistanceManager()).cc_setCubic();",
)
text = text.replace("            this.cc_progressListener.cc_onStatusChange(cloPos, null);\n", "")
text = text.replace(
    "PacketDistributor.sendToPlayer(player,\n                new CCClientboundSetCubeCacheCenterPacket",
    "ServerPlayNetworking.send(player,\n                new CCClientboundSetCubeCacheCenterPacket",
)
write(path, text)

# Identifier replaced ResourceLocation in the public 26.2 namespace.
path = "src/main/java/io/github/opencubicchunks/cubicchunks/world/storage/CubeStorage.java"
text = read(path)
text = text.replace("import net.minecraft.resources.ResourceLocation;", "import net.minecraft.resources.Identifier;")
text = text.replace("ResourceLocation", "Identifier")
text = text.replace(
    "Registry<Biome> biomeRegistry = level.registryAccess().lookupOrThrow(Registries.BIOME);",
    "PalettedContainerFactory containerFactory = level.palettedContainerFactory();",
)
text = text.replace("deserializeSections(sectionData, biomeRegistry)", "deserializeSections(sectionData, containerFactory)")
text = text.replace(
    "private static LevelChunkSection[] deserializeSections(byte[] serialized, Registry<Biome> biomeRegistry)",
    "private static LevelChunkSection[] deserializeSections(byte[] serialized, PalettedContainerFactory containerFactory)",
)
text = text.replace("new LevelChunkSection(biomeRegistry)", "new LevelChunkSection(containerFactory)")
text = text.replace("import net.minecraft.core.Registries;\n", "")
text = text.replace("import net.minecraft.world.level.biome.Biome;\n", "")
if "import net.minecraft.world.level.chunk.PalettedContainerFactory;" not in text:
    text = text.replace(
        "import net.minecraft.world.level.chunk.LevelChunkSection;\n",
        "import net.minecraft.world.level.chunk.LevelChunkSection;\nimport net.minecraft.world.level.chunk.PalettedContainerFactory;\n",
    )
write(path, text)

# Cube/Proto constructors now use the level's PalettedContainerFactory.
for path in (
    "src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/CubeAccess.java",
    "src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/ProtoCube.java",
    "src/main/java/io/github/opencubicchunks/cubicchunks/world/level/chunklike/ProtoClo.java",
):
    text = read(path)
    text = text.replace("import net.minecraft.core.Registry;\n", "")
    text = text.replace("import net.minecraft.world.level.biome.Biome;\n", "")
    if "import net.minecraft.world.level.chunk.PalettedContainerFactory;" not in text:
        text = text.replace(
            "import net.minecraft.world.level.chunk.LevelChunkSection;\n",
            "import net.minecraft.world.level.chunk.LevelChunkSection;\nimport net.minecraft.world.level.chunk.PalettedContainerFactory;\n",
        )
    text = text.replace("Registry<Biome> biomeRegistry", "PalettedContainerFactory containerFactory")
    text = text.replace("biomeRegistry", "containerFactory")
    write(path, text)

path = "src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/status/CubeColumnBridge.java"
text = read(path)
text = text.replace(
    "Registry<Biome> biomeRegistry = context.level().registryAccess().lookupOrThrow(Registries.BIOME);",
    "PalettedContainerFactory containerFactory = context.level().palettedContainerFactory();",
)
text = text.replace("new LevelChunkSection(biomeRegistry)", "new LevelChunkSection(containerFactory)")
text = text.replace("import net.minecraft.core.Registries;\n", "")
text = text.replace("import net.minecraft.core.Registry;\n", "")
text = text.replace("import net.minecraft.world.level.biome.Biome;\n", "")
if "import net.minecraft.world.level.chunk.PalettedContainerFactory;" not in text:
    text = text.replace(
        "import net.minecraft.world.level.chunk.LevelChunkSection;\n",
        "import net.minecraft.world.level.chunk.LevelChunkSection;\nimport net.minecraft.world.level.chunk.PalettedContainerFactory;\n",
    )
write(path, text)

# 26.2 Level/lighting/block-entity public APIs.
path = "src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/LevelCube.java"
text = read(path)
text = text.replace(
    "LightEngine.hasDifferentLightProperties(this, pos, previousState, state)",
    "LightEngine.hasDifferentLightProperties(previousState, state)",
)
text = text.replace("this.level.isClientSide", "this.level.isClientSide()")
text = text.replace(" && !this.level.captureBlockSnapshots", "")
text = text.replace(".key().location()", ".key().identifier()")
text = text.replace("blockentity.handleUpdateTag(TagValueInput.create(", "blockentity.loadWithComponents(TagValueInput.create(")
write(path, text)

# Private nested targets use string selectors to compile outside their package.
replacements = {
    "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinPlayerTicketTracker.java": (
        ("@Mixin(DistanceManager.PlayerTicketTracker.class)", "@Mixin(targets = \"net.minecraft.server.level.DistanceManager$PlayerTicketTracker\")"),
    ),
    "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinFixedPlayerDistanceChunkTracker.java": (
        ("@Mixin(DistanceManager.FixedPlayerDistanceChunkTracker.class)", "@Mixin(targets = \"net.minecraft.server.level.DistanceManager$FixedPlayerDistanceChunkTracker\")"),
    ),
    "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinChunkMap$TrackedEntity.java": (
        ("target = @Ref(ChunkMap.TrackedEntity.class)", "target = @Ref(string = \"net.minecraft.server.level.ChunkMap$TrackedEntity\")"),
        ("@Mixin(ChunkMap.TrackedEntity.class)", "@Mixin(targets = \"net.minecraft.server.level.ChunkMap$TrackedEntity\")"),
    ),
    "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/dasmsets/ChunkToCubeSet.java": (
        (
            "@TypeRedirect(from = @Ref(ClientChunkCache.Storage.class), to = @Ref(ClientCubeCache.Storage.class))",
            "@TypeRedirect(from = @Ref(string = \"net.minecraft.client.multiplayer.ClientChunkCache$Storage\"), to = @Ref(ClientCubeCache.Storage.class))",
        ),
    ),
    "src/main/java/io/github/opencubicchunks/cubicchunks/client/multiplayer/ClientCubeCache.java": (
        ("owner = @Ref(ClientChunkCache.Storage.class)", "owner = @Ref(string = \"net.minecraft.client.multiplayer.ClientChunkCache$Storage\")"),
    ),
}
for path, pairs in replacements.items():
    text = read(path)
    for old, new in pairs:
        text = text.replace(old, new)
    write(path, text)

# Access private DistanceManager tracker fields reflectively; the target objects still receive MarkableAsCubic through mixins.
path = "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinDistanceManager.java"
text = read(path)
text = text.replace("    @Shadow @Final private DistanceManager.FixedPlayerDistanceChunkTracker naturalSpawnChunkCounter;\n", "")
text = text.replace("    @Shadow @Final private DistanceManager.PlayerTicketTracker playerTicketManager;\n", "")
text = text.replace(
    """        ((MarkableAsCubic) this.naturalSpawnChunkCounter).cc_setCubic();
        ((MarkableAsCubic) this.playerTicketManager).cc_setCubic();
""",
    """        cc_markTrackerCubic("naturalSpawnChunkCounter");
        cc_markTrackerCubic("playerTicketManager");
""",
)
insert = """
    private void cc_markTrackerCubic(String fieldName) {
        try {
            java.lang.reflect.Field field = DistanceManager.class.getDeclaredField(fieldName);
            field.setAccessible(true);
            ((MarkableAsCubic) field.get(this)).cc_setCubic();
        } catch (ReflectiveOperationException exception) {
            throw new IllegalStateException("Unable to initialize cubic distance tracker " + fieldName, exception);
        }
    }
"""
marker = "    @Override public boolean cc_isCubic() {\n"
if insert.strip() not in text:
    text = text.replace(marker, insert + "\n" + marker)
write(path, text)

print("Applied Minecraft 26.2 source migration batch")
