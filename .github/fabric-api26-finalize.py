#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('.')


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding='utf-8')


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
text = text.replace('    dependsOn requireLinkedCore, requireRawMinecraftClient\n', '    dependsOn requireLinkedCore, prepareMinecraftCompileHeaders\n')
text = text.replace('compileJava.dependsOn requireLinkedCore, requireRawMinecraftClient\n', 'compileJava.dependsOn requireLinkedCore, prepareMinecraftCompileHeaders\n')
write(path, text)

path = 'src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/MixinMinecraftServer.java'
text = read(path)
text = text.replace('import net.minecraft.world.level.gamerules.GameRules;\n', '')
text = text.replace('    @Shadow public abstract GameRules getGameRules();\n\n', '')
text = text.replace(
    'int cubeRadius = Coords.sectionToCubeCeil(this.getGameRules().getInt(GameRules.RULE_SPAWN_CHUNK_RADIUS));',
    'int cubeRadius = Coords.sectionToCubeCeil(value / 2);',
)
write(path, text)

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

path = 'src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinPlayerRespawnLogic.java'
text = read(path)
text = text.replace('import net.minecraft.server.level.PlayerRespawnLogic;', 'import net.minecraft.server.level.PlayerSpawnFinder;')
text = text.replace('@Mixin(value = PlayerRespawnLogic.class, priority = 999)', '@Mixin(value = PlayerSpawnFinder.class, priority = 999)')
text = text.replace('@Inject(method = "getOverworldRespawnPos"', '@Inject(method = "getLevelRespawnPos"')
write(path, text)

write('src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/client/renderer/MixinLevelRenderer.java', '''package io.github.opencubicchunks.cubicchunks.mixin.core.client.renderer;

import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cubicchunks.client.renderer.CubicLevelRenderer;
import it.unimi.dsi.fastutil.longs.LongOpenHashSet;
import net.minecraft.client.renderer.LevelRenderer;
import net.minecraft.client.renderer.SectionOcclusionGraph;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;

@Mixin(LevelRenderer.class)
public abstract class MixinLevelRenderer implements CubicLevelRenderer {
    @Shadow public abstract SectionOcclusionGraph sectionOcclusionGraph();

    @Override public void cc_onCubeReadyToRender(CubePos cubePos) {
        LongOpenHashSet added = new LongOpenHashSet(1);
        added.add(cubePos.asLong());
        this.sectionOcclusionGraph().updateLoadedChunks(added, new LongOpenHashSet());
        this.sectionOcclusionGraph().invalidate();
    }
}
''')

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

path = 'src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/LevelCube.java'
text = read(path).replace('isClientSide()()', 'isClientSide()')
write(path, text)

print('Applied final Minecraft 26.2 API migration')
