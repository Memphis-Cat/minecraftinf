from pathlib import Path


def replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected source block was not found in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


mixin = Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinChunkMap.java")
replace(
    mixin,
    "import it.unimi.dsi.fastutil.longs.Long2ObjectLinkedOpenHashMap;\n",
    "import it.unimi.dsi.fastutil.longs.Long2ObjectLinkedOpenHashMap;\nimport it.unimi.dsi.fastutil.longs.LongSet;\n",
)
replace(
    mixin,
    """    @Shadow @Final private Long2ObjectLinkedOpenHashMap<ChunkHolder> pendingUnloads;
    @Shadow @Final private ThreadedLevelLightEngine lightEngine;
""",
    """    @Shadow @Final private Long2ObjectLinkedOpenHashMap<ChunkHolder> pendingUnloads;
    @Shadow @Final private Long2ObjectLinkedOpenHashMap<ChunkHolder> updatingChunkMap;
    @Shadow @Final private LongSet toDrop;
    @Shadow @Final private ThreadedLevelLightEngine lightEngine;
""",
)
replace(
    mixin,
    """    @AddTransformToSets(ChunkToCloSet.ChunkMap_redirects.class)
    @TransformFromMethod("saveAllChunks(Z)V")
    public native void cc_saveAllChunks(boolean flush);
""",
    """    @Inject(method = "hasWork", at = @At("HEAD"))
    private void cc_queueTicketlessClosForShutdown(CallbackInfoReturnable<Boolean> cir) {
        if (((CanBeCubic) this.level).cc_isCubic() && !this.level.getServer().isRunning() && !this.updatingChunkMap.isEmpty()
                && this.toDrop.isEmpty() && !this.distanceManager.hasTickets()) {
            this.toDrop.addAll(this.updatingChunkMap.keySet());
        }
    }

    @AddTransformToSets(ChunkToCloSet.ChunkMap_redirects.class)
    @TransformFromMethod("saveAllChunks(Z)V")
    public native void cc_saveAllChunks(boolean flush);
""",
)
