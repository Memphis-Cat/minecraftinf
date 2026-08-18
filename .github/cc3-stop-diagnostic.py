from pathlib import Path


def replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected source block was not found in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


script = Path(".github/scripts/server-persistence-smoke.sh")
replace(
    script,
    '''    echo "Server did not stop cleanly after the RCON stop command." >&2
    cat "${log_file}" >&2
    return 1
''',
    '''    capture_save_flush_thread_dumps
    echo "Server did not stop cleanly after the RCON stop command." >&2
    cat "${log_file}" >&2
    return 1
''',
)

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
    """    private CubeStorage cc_cubeStorage;

    // TODO once we can target non-return locations in constructors, do this when the vanilla field is set
""",
    """    private CubeStorage cc_cubeStorage;
    private long cc_shutdownDiagnosticCounter;

    @Inject(method = "hasWork", at = @At("RETURN"))
    private void cc_logStaleShutdownWork(CallbackInfoReturnable<Boolean> cir) {
        if (((CanBeCubic) this.level).cc_isCubic() && cir.getReturnValue() && ++this.cc_shutdownDiagnosticCounter % 1000L == 0L) {
            CubicChunks.LOGGER.warn(
                    "Cubic shutdown work remains: updating={}, pendingUnloads={}, toDrop={}, unloadQueue={}, light={}, poi={}, tickets={}",
                    this.updatingChunkMap.size(), this.pendingUnloads.size(), this.toDrop.size(), this.unloadQueue.size(),
                    this.lightEngine.hasLightWork(), this.poiManager.hasWork(), this.distanceManager.hasTickets());
        }
    }

    // TODO once we can target non-return locations in constructors, do this when the vanilla field is set
""",
)
