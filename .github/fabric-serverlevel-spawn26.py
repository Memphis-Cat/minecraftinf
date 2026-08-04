#!/usr/bin/env python3
"""Remove ServerLevel spawn-ticket hooks moved out of ServerLevel in Minecraft 26.2."""

from pathlib import Path

path = Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinServerLevel.java")
text = path.read_text(encoding="utf-8")
start_marker = '    @WrapOperation(method = "setDefaultSpawnPos"'
end_marker = '    @AddMethodToSets(containers = ChunkToCloSet.ServerLevel_redirects.class, method = "tickChunk'
if start_marker in text:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    text = text[:start] + text[end:]
text = text.replace('import com.llamalad7.mixinextras.injector.wrapoperation.Operation;\n', '')
text = text.replace('import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;\n', '')
text = text.replace('import net.minecraft.server.level.TicketType;\n', '')
if 'setDefaultSpawnPos' in text:
    raise SystemExit('Obsolete ServerLevel#setDefaultSpawnPos hooks remain')
path.write_text(text, encoding='utf-8')
print('Removed spawn-ticket hooks moved out of ServerLevel in Minecraft 26.2')
