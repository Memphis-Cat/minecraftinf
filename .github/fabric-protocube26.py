#!/usr/bin/env python3
"""Replace unresolved ProtoChunk post-processing DASM copies with direct 26.2 implementations."""
from pathlib import Path

path = Path("src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/ProtoCube.java")
text = path.read_text(encoding="utf-8")

old_mark = '''    // dasm + mixin
    @TransformFromMethod(value = "markPosForPostprocessing(Lnet/minecraft/core/BlockPos;)V", owner = @Ref(ProtoChunk.class))
    @Override public native void markPosForPostprocessing(BlockPos pos);

    @TransformFromMethod(value = "addPackedPostProcess(Lit/unimi/dsi/fastutil/shorts/ShortList;I)V", owner = @Ref(ProtoChunk.class))
    @Override public native void addPackedPostProcess(ShortList offsets, int index);
'''
new_mark = '''    @Override public void markPosForPostprocessing(BlockPos pos) {
        if (this.isInsideBuildHeight(pos)) {
            CubeAccess.getOrCreateOffsetList(this.postProcessing, Coords.blockToIndex(pos)).add(packOffsetCoordinates(pos));
        }
    }

    @Override public void addPackedPostProcess(ShortList offsets, int index) {
        CubeAccess.getOrCreateOffsetList(this.postProcessing, index).addAll(offsets);
    }
'''

if old_mark in text:
    text = text.replace(old_mark, new_mark, 1)
elif "@Override public void markPosForPostprocessing(BlockPos pos)" not in text:
    raise SystemExit("Unable to locate ProtoCube post-processing transforms")

if 'markPosForPostprocessing(Lnet/minecraft/core/BlockPos;)V' in text:
    raise SystemExit("Unresolved ProtoCube markPosForPostprocessing DASM transform remains")
if 'addPackedPostProcess(Lit/unimi/dsi/fastutil/shorts/ShortList;I)V' in text:
    raise SystemExit("Unresolved ProtoCube addPackedPostProcess DASM transform remains")

path.write_text(text, encoding="utf-8")
print("Implemented ProtoCube post-processing directly for Minecraft 26.2")
