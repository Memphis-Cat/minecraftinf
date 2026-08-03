#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('.')


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def write(path: str, text: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8')


def ensure_import(text: str, import_line: str, anchor: str) -> str:
    if import_line not in text:
        if anchor not in text:
            raise SystemExit(f'Unable to insert {import_line.strip()}: missing anchor {anchor.strip()}')
        text = text.replace(anchor, anchor + import_line, 1)
    return text


# Gradle 9 / raw Minecraft 26.2 compile bridge.
path = 'build.gradle'
text = read(path)
if "options.compilerArgs.addAll(['-Xmaxerrs', '1000'])" not in text:
    text = text.replace("    options.release = 25\n", "    options.release = 25\n    options.compilerArgs.addAll(['-Xmaxerrs', '1000'])\n", 1)
text = text.replace("            exclude 'io/github/opencubicchunks/cubicchunks/movetoforgesourcesetlater/**'", "            exclude '**/movetoforgesourcesetlater/**'")
legacy_accessor = "            exclude 'io/github/opencubicchunks/cubicchunks/mixin/access/common/SectionOcclusionGraph$GraphEventsAccess.java'\n"
if legacy_accessor not in text:
    text = text.replace("            exclude 'io/github/opencubicchunks/cubicchunks/client/gui/**'\n", "            exclude 'io/github/opencubicchunks/cubicchunks/client/gui/**'\n" + legacy_accessor)
if 'def widenedMinecraftClientJar' not in text:
    text = text.replace(
        "def rawMinecraftClientJar = new File(loomMinecraftCache, 'minecraft-client.jar')\n",
        "def rawMinecraftClientJar = new File(loomMinecraftCache, 'minecraft-client.jar')\n"
        "def widenedMinecraftClientJar = file(\"${buildDir}/fabric-header-libs/minecraft-client-access-widened.jar\")\n",
    )
text = text.replace('    compileOnly files(rawMinecraftClientJar)\n', '    compileOnly files(widenedMinecraftClientJar)\n')
prepare = """def prepareMinecraftCompileHeaders = tasks.register('prepareMinecraftCompileHeaders', Exec) {
    group = 'verification'
    description = 'Applies cubicchunks.accesswidener to the raw Minecraft 26.2 compile-only jar.'
    dependsOn requireRawMinecraftClient
    inputs.file(rawMinecraftClientJar)
    inputs.file('src/main/resources/cubicchunks.accesswidener')
    inputs.file('.github/widen-minecraft-headers.py')
    outputs.file(widenedMinecraftClientJar)
    commandLine 'python3', '.github/widen-minecraft-headers.py',
            '--input', rawMinecraftClientJar,
            '--access-widener', file('src/main/resources/cubicchunks.accesswidener'),
            '--output', widenedMinecraftClientJar
}

"""
if 'def prepareMinecraftCompileHeaders' not in text:
    text = text.replace("tasks.register('printMainCompileClasspath') {\n", prepare + "tasks.register('printMainCompileClasspath') {\n")
classpath_fix = """// Loom 1.17 currently contributes a resources-only merged-deobf 26.2 jar before
// Mojang's complete public client jar. Remove that incomplete artifact from every
// javac task and put the access-widened complete jar first so javac sees the same
// API that Fabric launches at runtime.
tasks.withType(JavaCompile).configureEach {
    dependsOn prepareMinecraftCompileHeaders
    doFirst {
        def normalizedWidenedPath = widenedMinecraftClientJar.canonicalPath
        def filteredClasspath = classpath.filter { candidate ->
            def normalized = candidate.canonicalPath.replace('\\\\', '/')
            candidate.canonicalPath != normalizedWidenedPath &&
                    !(candidate.name.startsWith('minecraft-merged-deobf-') && normalized.contains('/fabric-loom/minecraftMaven/'))
        }
        classpath = files(widenedMinecraftClientJar) + filteredClasspath
    }
}

"""
if 'Loom 1.17 currently contributes a resources-only merged-deobf 26.2 jar' not in text:
    text = text.replace("tasks.register('printMainCompileClasspath') {\n", classpath_fix + "tasks.register('printMainCompileClasspath') {\n")
text = text.replace('    dependsOn requireLinkedCore, requireRawMinecraftClient\n', '    dependsOn requireLinkedCore, prepareMinecraftCompileHeaders\n')
text = text.replace('compileJava.dependsOn requireLinkedCore, requireRawMinecraftClient\n', 'compileJava.dependsOn requireLinkedCore, prepareMinecraftCompileHeaders\n')
text = text.replace('    enabled = false\n', '')
write(path, text)


# Spawn-radius migration.
path = 'src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/MixinMinecraftServer.java'
text = read(path)
text = text.replace('import net.minecraft.world.level.gamerules.GameRules;\n', '')
text = text.replace('    @Shadow public abstract GameRules getGameRules();\n\n', '')
text = text.replace(
    'int cubeRadius = Coords.sectionToCubeCeil(this.getGameRules().getInt(GameRules.RULE_SPAWN_CHUNK_RADIUS));',
    'int cubeRadius = Coords.sectionToCubeCeil(value / 2);',
)
write(path, text)


# Distance-manager nested trackers are accessible through the widened Minecraft jar.
path = 'src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinDistanceManager.java'
text = read(path)
if 'cc_markTrackerCubic' in text:
    shadow_anchor = '    @Shadow @Final private SimulationChunkTracker simulationChunkTracker;\n'
    shadows = ('    @Shadow @Final private DistanceManager.FixedPlayerDistanceChunkTracker naturalSpawnChunkCounter;\n'
               '    @Shadow @Final private DistanceManager.PlayerTicketTracker playerTicketManager;\n')
    if shadows not in text:
        text = text.replace(shadow_anchor, shadow_anchor + shadows)
    text = text.replace('        cc_markTrackerCubic("naturalSpawnChunkCounter");\n        cc_markTrackerCubic("playerTicketManager");',
                        '        ((MarkableAsCubic) this.naturalSpawnChunkCounter).cc_setCubic();\n'
                        '        ((MarkableAsCubic) this.playerTicketManager).cc_setCubic();')
    start = text.find('    private void cc_markTrackerCubic(String fieldName) {')
    if start >= 0:
        end = text.find('    @Override public boolean cc_isCubic()', start)
        if end < 0:
            raise SystemExit('Unable to remove reflection tracker helper')
        text = text[:start] + text[end:]
write(path, text)


# Player spawn finder rename.
path = 'src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinPlayerRespawnLogic.java'
text = read(path)
text = text.replace('import net.minecraft.server.level.PlayerRespawnLogic;', 'import net.minecraft.server.level.PlayerSpawnFinder;')
text = text.replace('@Mixin(value = PlayerRespawnLogic.class, priority = 999)', '@Mixin(value = PlayerSpawnFinder.class, priority = 999)')
text = text.replace('@Inject(method = "getOverworldRespawnPos"', '@Inject(method = "getLevelRespawnPos"')
write(path, text)


# PalettedContainerFactory replaced biome registries in chunk/cube constructors, but
# Holder<Biome> remains part of the noise-biome API and therefore still needs Biome imports.
for path in (
    'src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/CubeAccess.java',
    'src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/ProtoCube.java',
):
    text = read(path)
    text = ensure_import(text, 'import net.minecraft.world.level.biome.Biome;\n', 'import net.minecraft.world.level.LevelHeightAccessor;\n')
    write(path, text)

path = 'src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/LevelCube.java'
text = read(path)
text = text.replace(
    'super(pos, data, level, level.registryAccess().lookupOrThrow(Registries.BIOME), inhabitedTime, sections, blendingData);',
    'super(pos, data, level, level.palettedContainerFactory(), inhabitedTime, sections, blendingData);',
)
text = text.replace('import net.minecraft.core.registries.Registries;\n', '')
text = text.replace('isClientSide()()', 'isClientSide()')
write(path, text)


# ChunkPos packing is now instance pack() or static pack(x,z).
for path in (
    'src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinPlayerTicketTracker.java',
    'src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinChunkMap.java',
):
    text = read(path)
    text = text.replace('.toLong()', '.pack()')
    write(path, text)

path = 'src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinChunkGenerationTask.java'
text = read(path).replace('ChunkPos.asLong(x, z)', 'ChunkPos.pack(x, z)')
write(path, text)


# Vanilla 26.2 unload no longer calls NeoForge hooks. Keep the exact vanilla column
# unload sequence while preserving the custom CubeStorage path for cubes.
path = 'src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinChunkMap.java'
text = read(path)
text = text.replace('                net.neoforged.neoforge.common.CommonHooks.onChunkUnload(this.poiManager, chunkAccess);\n', '')
text = text.replace('                this.chunkTypeCache.remove(chunkAccess.getPos().pack());\n', '')
text = text.replace('                    net.neoforged.neoforge.common.NeoForge.EVENT_BUS.post(new net.neoforged.neoforge.event.level.ChunkEvent.Unload(levelChunk));\n', '')
write(path, text)


# getCurrentDifficultyAt moved from Level to ServerLevel and now uses positional moon
# brightness plus the overworld clock. Move the cubic override to the correct mixin.
path = 'src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/world/level/MixinLevel.java'
text = read(path)
old_difficulty = '''    // getCurrentDifficultyAt
    // This function isn't worth trying to wrap due to its complexity, so we just replace it entirely
    // Local difficulty is not something people mod so this is fine
    @Inject(method = "getCurrentDifficultyAt", at = @At(value = "HEAD"), cancellable = true)
    private void cc_replaceGetCurrentDifficultyAt(BlockPos blockPos, CallbackInfoReturnable<DifficultyInstance> cir) {
        if (cc_isCubic) {
            long i = 0L;
            float f = 0.0F;
            if (this.cc_hasCubeAt(blockPos)) {
                f = this.getMoonBrightness();
                i = this.cc_getCubeAt(blockPos).getInhabitedTime();
            }
            cir.setReturnValue(new DifficultyInstance(this.getDifficulty(), this.getDayTime(), i, f));
        }
    }
'''
text = text.replace(old_difficulty, '')
text = text.replace('import net.minecraft.world.DifficultyInstance;\n', '')
text = text.replace('    @Shadow public abstract long getDayTime();\n\n', '')
write(path, text)

path = 'src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinServerLevel.java'
text = read(path)
text = ensure_import(text, 'import net.minecraft.util.RandomSource;\n', 'import net.minecraft.server.level.TicketType;\n')
text = ensure_import(text, 'import net.minecraft.world.DifficultyInstance;\n', 'import net.minecraft.util.profiling.ProfilerFiller;\n')
text = ensure_import(text, 'import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;\n', 'import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;\n')
shadow_anchor = '    @Shadow @Final private ServerChunkCache chunkSource;\n'
server_shadows = '''    @Shadow @Final protected RandomSource random;
    @Shadow public abstract float getMoonBrightness(BlockPos pos);
    @Shadow public abstract long getOverworldClockTime();
'''
if server_shadows not in text:
    text = text.replace(shadow_anchor, shadow_anchor + server_shadows)
text = text.replace('blockState.randomTick(serverLevel, blockPos, serverLevel.random);', 'blockState.randomTick(serverLevel, blockPos, this.random);')
text = text.replace('fluidState.randomTick(serverLevel, blockPos, serverLevel.random);', 'fluidState.randomTick(serverLevel, blockPos, this.random);')
difficulty_method = '''
    @Inject(method = "getCurrentDifficultyAt", at = @At("HEAD"), cancellable = true)
    private void cc_replaceGetCurrentDifficultyAt(BlockPos blockPos, CallbackInfoReturnable<DifficultyInstance> cir) {
        if (!this.cc_isCubic) {
            return;
        }
        long inhabitedTime = 0L;
        float moonBrightness = 0.0F;
        if (this.cc_hasCubeAt(blockPos)) {
            inhabitedTime = this.cc_getCubeAt(blockPos).getInhabitedTime();
            moonBrightness = this.getMoonBrightness(blockPos);
        }
        cir.setReturnValue(new DifficultyInstance(this.getDifficulty(), this.getOverworldClockTime(), inhabitedTime, moonBrightness));
    }
'''
if 'private void cc_replaceGetCurrentDifficultyAt' not in text:
    insertion = '    // TODO (P2) waitForChunkAndEntities\n'
    text = text.replace(insertion, difficulty_method + '\n' + insertion, 1)
write(path, text)


# Client-only methods are present in the runtime jar but absent from Loom's compile
# header. Invoke/access them through mixin bridges instead of deleting renderer logic.
write('src/main/java/io/github/opencubicchunks/cubicchunks/mixin/access/client/ClientLevelAccess.java', '''package io.github.opencubicchunks.cubicchunks.mixin.access.client;

import net.minecraft.client.multiplayer.ClientLevel;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

@Mixin(ClientLevel.class)
public interface ClientLevelAccess {
    @Invoker("onSectionBecomingNonEmpty")
    void cc_invokeOnSectionBecomingNonEmpty(long sectionPos);
}
''')

write('src/main/java/io/github/opencubicchunks/cubicchunks/mixin/access/client/ViewAreaAccess.java', '''package io.github.opencubicchunks.cubicchunks.mixin.access.client;

import net.minecraft.client.renderer.ViewArea;
import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

@Mixin(ViewArea.class)
public interface ViewAreaAccess {
    @Accessor("level")
    Level cc_getLevel();
}
''')

path = 'src/main/java/io/github/opencubicchunks/cubicchunks/client/multiplayer/ClientCubeCache.java'
text = read(path)
text = ensure_import(text, 'import io.github.opencubicchunks.cubicchunks.mixin.access.client.ClientLevelAccess;\n',
                     'import io.github.opencubicchunks.cubicchunks.client.renderer.CubicLevelRenderer;\n')
text = text.replace('this.level.onSectionBecomingNonEmpty(i);',
                    '((ClientLevelAccess) (Object) this.level).cc_invokeOnSectionBecomingNonEmpty(i);')
text = text.replace('this.level.onSectionBecomingNonEmpty(sectionPosLong);',
                    '((ClientLevelAccess) (Object) this.level).cc_invokeOnSectionBecomingNonEmpty(sectionPosLong);')
write(path, text)

write('src/main/java/io/github/opencubicchunks/cubicchunks/client/renderer/CubicLevelRenderer.java', '''package io.github.opencubicchunks.cubicchunks.client.renderer;

import io.github.opencubicchunks.cc_core.api.CubePos;

public interface CubicLevelRenderer {
    void cc_onCubeReadyToRender(CubePos cubePos);

    void cc_invalidateCulling();
}
''')

write('src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/client/renderer/MixinLevelRenderer.java', '''package io.github.opencubicchunks.cubicchunks.mixin.core.client.renderer;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cubicchunks.client.renderer.CubicLevelRenderer;
import it.unimi.dsi.fastutil.longs.LongOpenHashSet;
import net.minecraft.client.renderer.LevelRenderer;
import net.minecraft.client.renderer.SectionOcclusionGraph;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;

@Mixin(LevelRenderer.class)
public abstract class MixinLevelRenderer implements CubicLevelRenderer {
    @Shadow @Final private SectionOcclusionGraph sectionOcclusionGraph;

    @Override public void cc_onCubeReadyToRender(CubePos cubePos) {
        LongOpenHashSet added = new LongOpenHashSet(1);
        added.add(cubePos.asLong());
        this.sectionOcclusionGraph.updateLoadedChunks(added, new LongOpenHashSet());
        this.sectionOcclusionGraph.invalidate();
    }

    @Override public void cc_invalidateCulling() {
        this.sectionOcclusionGraph.invalidate();
    }
}
''')

path = 'src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/client/renderer/MixinViewArea.java'
text = read(path)
text = ensure_import(text, 'import io.github.opencubicchunks.cubicchunks.client.renderer.CubicLevelRenderer;\n',
                     'import io.github.opencubicchunks.cubicchunks.CanBeCubic;\n')
text = text.replace('this.levelRenderer.getSectionOcclusionGraph().invalidate();',
                    '((CubicLevelRenderer) this.levelRenderer).cc_invalidateCulling();')
write(path, text)

path = 'src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/client/renderer/MixinSectionOcclusionGraph$GraphStorage.java'
text = read(path)
text = ensure_import(text, 'import io.github.opencubicchunks.cubicchunks.mixin.access.client.ViewAreaAccess;\n',
                     'import io.github.opencubicchunks.cubicchunks.CanBeCubic;\n')
text = text.replace('((CanBeCubic) instance.getLevelHeightAccessor()).cc_isCubic()',
                    '((CanBeCubic) ((ViewAreaAccess) (Object) instance).cc_getLevel()).cc_isCubic()')
write(path, text)


# Remove the obsolete GraphEvents transform and port SectionPos API changes.
path = 'src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/client/renderer/MixinSectionOcclusionGraph.java'
text = read(path)
for line in (
    'import io.github.notstirred.dasm.api.annotations.redirect.redirects.AddMethodToSets;\n',
    'import io.github.notstirred.dasm.api.annotations.redirect.redirects.AddTransformToSets;\n',
    'import io.github.notstirred.dasm.api.annotations.transform.TransformFromMethod;\n',
    'import io.github.opencubicchunks.cubicchunks.mixin.access.common.SectionOcclusionGraph$GraphEventsAccess;\n',
):
    text = text.replace(line, '')
text = text.replace('import net.minecraft.client.renderer.SectionOcclusionGraph;\n', 'import net.minecraft.client.Minecraft;\nimport net.minecraft.client.renderer.SectionOcclusionGraph;\n')
start = text.find('    @AddTransformToSets(ChunkToCubeSet.SectionOcclusionGraph_redirects.class)')
if start >= 0:
    end = text.find('    @WrapOperation(method = "initializeQueueForFullUpdate"', start)
    if end < 0:
        raise SystemExit('Unable to remove obsolete GraphEvents code')
    text = text[:start] + text[end:]
text = text.replace(
    'cc_isCubic = viewArea != null && ((CanBeCubic) viewArea.getLevelHeightAccessor()).cc_isCubic();',
    'cc_isCubic = viewArea != null && Minecraft.getInstance().level != null\n'
    '                && ((CanBeCubic) Minecraft.getInstance().level).cc_isCubic();',
)
text = text.replace('Lnet/minecraft/core/SectionPos;sectionToChunk(J)J', 'Lnet/minecraft/world/level/ChunkPos;fromSectionNode(J)J')
for value in ('x(originSectionPosLong)', 'y(originSectionPosLong)', 'z(originSectionPosLong)',
              'x(sectionPosLong)', 'y(sectionPosLong)', 'z(sectionPosLong)'):
    text = text.replace(f'Coords.blockToCube(SectionPos.{value})', f'Coords.sectionToCube(SectionPos.{value})')
write(path, text)

print('Applied final Minecraft 26.2 API migration')
