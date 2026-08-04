#!/usr/bin/env python3
"""Port ChunkHolder synthetic promotion hook to Minecraft 26.2."""

from pathlib import Path

path = Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinChunkHolder.java")
text = path.read_text(encoding="utf-8")
text = text.replace('"lambda$scheduleFullChunkPromotion$4",', '"lambda$scheduleFullChunkPromotion$0",')
if 'lambda$scheduleFullChunkPromotion$4' in text:
    raise SystemExit('Obsolete ChunkHolder promotion lambda remains')
if 'lambda$scheduleFullChunkPromotion$0' not in text:
    raise SystemExit('Minecraft 26.2 ChunkHolder promotion lambda hook is missing')
path.write_text(text, encoding='utf-8')
print('Migrated ChunkHolder promotion lambda to Minecraft 26.2')
