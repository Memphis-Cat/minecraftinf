#!/usr/bin/env python3
"""Port DASM and transformed-call signatures to Minecraft 26.2."""

from pathlib import Path

redirect_files = (
    Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/dasmsets/ChunkToCubeSet.java"),
    Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/dasmsets/ChunkToCloSet.java"),
)

for path in redirect_files:
    text = path.read_text(encoding="utf-8")
    text = text.replace('@MethodRedirect("toLong()J")', '@MethodRedirect("pack()J")')
    text = text.replace('@MethodRedirect("asLong(II)J")', '@MethodRedirect("pack(II)J")')
    if '@MethodRedirect("toLong()J")' in text or '@MethodRedirect("asLong(II)J")' in text:
        raise SystemExit(f"Obsolete ChunkPos DASM packing redirect remains in {path}")
    path.write_text(text, encoding="utf-8")

cube = redirect_files[0].read_text(encoding="utf-8")
clo = redirect_files[1].read_text(encoding="utf-8")
if '@MethodRedirect("pack()J")' not in cube:
    raise SystemExit("Missing Minecraft 26.2 instance ChunkPos.pack redirect")
if '@MethodRedirect("pack(II)J")' not in cube or '@MethodRedirect("pack(II)J")' not in clo:
    raise SystemExit("Missing Minecraft 26.2 static ChunkPos.pack redirect")

# DistanceManager's player-ticket methods still exist, but their ChunkPos key call
# was renamed from toLong() to pack(). Keep the cubic SectionPos routing intact.
distance_manager = Path(
    "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinDistanceManager.java"
)
text = distance_manager.read_text(encoding="utf-8")
text = text.replace(
    'target = "Lnet/minecraft/world/level/ChunkPos;toLong()J"',
    'target = "Lnet/minecraft/world/level/ChunkPos;pack()J"',
)
if 'ChunkPos;toLong()J' in text:
    raise SystemExit("Obsolete DistanceManager ChunkPos.toLong injection remains")
if text.count('ChunkPos;pack()J') < 2:
    raise SystemExit("Missing Minecraft 26.2 DistanceManager ChunkPos.pack injections")
distance_manager.write_text(text, encoding="utf-8")

# shouldForceNaturalSpawning was a NeoForge-only hook and was removed from
# Minecraft 26.2 TicketStorage. CubicTicketStorage has no such API and there are
# no Fabric callers, so do not ask DASM to clone a nonexistent source method.
ticket_storage = Path(
    "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/world/level/MixinTicketStorage.java"
)
text = ticket_storage.read_text(encoding="utf-8")
method_name = "cc_shouldForceNaturalSpawning"
name_index = text.find(method_name)
if name_index >= 0:
    annotation_start = text.rfind("    // TODO move to neoforge-specific mixin", 0, name_index)
    if annotation_start < 0:
        annotation_start = text.rfind("    @AddTransformToSets", 0, name_index)
    semicolon = text.find(";", name_index)
    if annotation_start < 0 or semicolon < 0:
        raise SystemExit("Unable to locate obsolete TicketStorage natural-spawn transform")
    method_end = semicolon + 1
    while method_end < len(text) and text[method_end] == "\n":
        method_end += 1
    text = text[:annotation_start] + text[method_end:]
if method_name in text or "shouldForceNaturalSpawning" in text:
    raise SystemExit("Obsolete TicketStorage natural-spawn transform remains")
ticket_storage.write_text(text, encoding="utf-8")


def replace_native_method(source: str, method_name: str, replacement: str) -> str:
    """Replace one annotated native method, including its DASM annotations."""
    name_index = source.find(method_name)
    if name_index < 0:
        return source
    annotation_start = source.rfind("    @AddTransformToSets", 0, name_index)
    if annotation_start < 0:
        annotation_start = source.rfind("    @TransformFromMethod", 0, name_index)
    semicolon = source.find(";", name_index)
    if annotation_start < 0 or semicolon < 0:
        raise SystemExit(f"Unable to locate native method boundaries for {method_name}")
    method_end = semicolon + 1
    while method_end < len(source) and source[method_end] == "\n":
        method_end += 1
    return source[:annotation_start] + replacement + source[method_end:]


# CubeStatusTasks.full used two redirects into a DASM-generated method and lambda.
# The generated lambda name changed in Minecraft 26.2, so implement the cubic
# conversion directly: use all three CubePos coordinates for the holder lookup,
# replace the proto cube through GenerationCloHolder, and install the cube-aware
# unsaved listener without relying on WorldGenContext's vanilla listener type.
cube_status_tasks = Path(
    "src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/status/CubeStatusTasks.java"
)
text = cube_status_tasks.read_text(encoding="utf-8")
imports = (
    "import io.github.opencubicchunks.cc_core.world.level.CloPos;\n"
    "import io.github.opencubicchunks.cubicchunks.server.level.CubicChunkMap;\n"
    "import io.github.opencubicchunks.cubicchunks.server.level.GenerationCloHolder;\n"
    "import io.github.opencubicchunks.cubicchunks.world.level.cube.ImposterProtoCube;\n"
    "import io.github.opencubicchunks.cubicchunks.world.level.cube.LevelCube;\n"
    "import io.github.opencubicchunks.cubicchunks.world.level.cube.ProtoCube;\n"
)
if "import io.github.opencubicchunks.cubicchunks.server.level.GenerationCloHolder;\n" not in text:
    anchor = "import io.github.opencubicchunks.cubicchunks.mixin.dasmsets.ChunkToCubeSet;\n"
    if anchor not in text:
        raise SystemExit("Unable to locate CubeStatusTasks cubic import block")
    text = text.replace(anchor, anchor + imports, 1)
for import_line, anchor in (
    ("import net.minecraft.util.ProblemReporter;\n", "import net.minecraft.server.level.ServerLevel;\n"),
    ("import net.minecraft.world.entity.EntitySpawnReason;\n", "import net.minecraft.util.ProblemReporter;\n"),
    ("import net.minecraft.world.entity.EntityType;\n", "import net.minecraft.world.entity.EntitySpawnReason;\n"),
    ("import net.minecraft.world.level.storage.TagValueInput;\n", "import net.minecraft.world.level.chunk.status.WorldGenContext;\n"),
):
    if import_line not in text:
        if anchor not in text:
            raise SystemExit(f"Unable to locate import anchor for {import_line.strip()}")
        text = text.replace(anchor, anchor + import_line, 1)

if "private static boolean isLighted(CubeAccess cube) {" not in text:
    text = replace_native_method(
        text,
        "isLighted(CubeAccess cube)",
        "    private static boolean isLighted(CubeAccess cube) {\n"
        "        return cube.getPersistedStatus().isOrAfter(ChunkStatus.LIGHT) && cube.isLightCorrect();\n"
        "    }\n\n",
    )

if "GenerationCloHolder cubeHolder" not in text:
    text = replace_native_method(
        text,
        "CompletableFuture<CubeAccess> full(",
        '''    public static CompletableFuture<CubeAccess> full(
            WorldGenContext context, CubeStep step, StaticCache3D<GenerationChunkHolder> cubes, CubeAccess cube
    ) {
        var cubePos = cube.cc_getCubePos();
        GenerationChunkHolder holder = cubes.get(cubePos.getX(), cubePos.getY(), cubePos.getZ());
        GenerationCloHolder cubeHolder = (GenerationCloHolder) holder;
        return CompletableFuture.supplyAsync(() -> {
            ProtoCube protoCube = (ProtoCube) cube;
            ServerLevel level = context.level();
            LevelCube levelCube;
            if (protoCube instanceof ImposterProtoCube imposter) {
                levelCube = (LevelCube) imposter.cc_getWrappedClo();
            } else {
                levelCube = new LevelCube(level, protoCube, loadedCube -> {
                    try (ProblemReporter.ScopedCollector reporter = new ProblemReporter.ScopedCollector(cube.problemPath(), LOGGER)) {
                        postLoadProtoCube(level, TagValueInput.create(reporter, level.registryAccess(), protoCube.getEntities()));
                    }
                });
                cubeHolder.cc_replaceProtoCube(new ImposterProtoCube(levelCube, false));
            }

            levelCube.setFullStatus(holder::getFullStatus);
            levelCube.runPostLoad();
            levelCube.setLoaded(true);
            levelCube.registerAllBlockEntitiesAfterLevelLoad();
            levelCube.registerTickContainerInLevel(level);
            CubicChunkMap chunkMap = (CubicChunkMap) level.getChunkSource().chunkMap;
            levelCube.setUnsavedListener(pos -> chunkMap.cc_setCloUnsaved(CloPos.cube(pos)));
            return levelCube;
        }, context.mainThreadExecutor());
    }

''',
    )

if "EntityType.loadEntitiesRecursive" not in text:
    text = replace_native_method(
        text,
        "postLoadProtoCube(",
        '''    private static void postLoadProtoCube(ServerLevel level, ValueInput.ValueInputList entities) {
        if (!entities.isEmpty()) {
            level.addWorldGenChunkEntities(EntityType.loadEntitiesRecursive(entities, level, EntitySpawnReason.LOAD));
        }
    }

''',
    )

for required in (
    "private static boolean isLighted(CubeAccess cube) {",
    "GenerationCloHolder cubeHolder",
    "cubes.get(cubePos.getX(), cubePos.getY(), cubePos.getZ())",
    "EntityType.loadEntitiesRecursive",
):
    if required not in text:
        raise SystemExit(f"Missing direct Minecraft 26.2 cube status implementation: {required}")
cube_status_tasks.write_text(text, encoding="utf-8")

status_mixin = Path(
    "src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/world/level/cube/status/MixinCubeStatusTasks.java"
)
status_mixin.write_text(
    '''package io.github.opencubicchunks.cubicchunks.mixin.core.common.world.level.cube.status;

import io.github.opencubicchunks.cubicchunks.world.level.cube.status.CubeStatusTasks;
import org.spongepowered.asm.mixin.Mixin;

/**
 * Reserved mixin target for cube status-task integration.
 *
 * <p>The Fabric 26.2 implementation performs the 3D holder lookup and installs
 * the cubic unsaved listener directly in CubeStatusTasks.full, so no generated
 * lambda redirects are required.</p>
 */
@Mixin(CubeStatusTasks.class)
public class MixinCubeStatusTasks {
}
''',
    encoding="utf-8",
)

print("Migrated Minecraft 26.2 DASM redirects, ticket hooks and cube status completion")
