from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text()
    if text.count(old) != 1:
        raise SystemExit(f"Expected source block exactly once in {path}")
    file.write_text(text.replace(old, new))


level_cube = "src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/LevelCube.java"
replace_once(
    level_cube,
    """    static final Logger LOGGER = LogUtils.getLogger();
    private static final TickingBlockEntity NULL_TICKER = new TickingBlockEntity() {
""",
    """    static final Logger LOGGER = LogUtils.getLogger();
    private static final int POST_PROCESSING_Y_SHIFT = 4;
    private static final int POST_PROCESSING_Z_SHIFT = 8;
    private static final int POST_PROCESSING_UPDATE_FLAGS = 276;
    private static final TickingBlockEntity NULL_TICKER = new TickingBlockEntity() {
""",
)
replace_once(
    level_cube,
    """                int localY = packedPosition >> 4 & SectionPos.SECTION_MASK;
                int localZ = packedPosition >> 8 & SectionPos.SECTION_MASK;
""",
    """                int localY = packedPosition >> POST_PROCESSING_Y_SHIFT & SectionPos.SECTION_MASK;
                int localZ = packedPosition >> POST_PROCESSING_Z_SHIFT & SectionPos.SECTION_MASK;
""",
)
replace_once(
    level_cube,
    "serverLevel.setBlock(blockPos, updatedState, 276);",
    "serverLevel.setBlock(blockPos, updatedState, POST_PROCESSING_UPDATE_FLAGS);",
)

bridge = "src/main/java/io/github/opencubicchunks/cubicchunks/world/level/cube/status/CubeColumnBridge.java"
replace_once(
    bridge,
    """    private static <T> long copyScheduledTicks(
            long gameTime, CubePos cubePos, TickContainerAccess<T> target, TickContainerAccess<T> source, long subTickOrder
    ) {
        if (!(source instanceof SerializableTickContainer<?> rawSerializable)) {
            return subTickOrder;
        }
        SerializableTickContainer<T> serializable = (SerializableTickContainer<T>) rawSerializable;
        for (SavedTick<T> tick : serializable.pack(gameTime)) {
            BlockPos position = tick.pos();
            if (position.getX() < cubePos.minCubeX() || position.getX() > cubePos.maxCubeX()
                    || position.getY() < cubePos.minCubeY() || position.getY() > cubePos.maxCubeY()
                    || position.getZ() < cubePos.minCubeZ() || position.getZ() > cubePos.maxCubeZ()) {
                continue;
            }
            target.schedule(tick.unpack(gameTime, subTickOrder++));
        }
        return subTickOrder;
    }
""",
    """    private static <T> long copyScheduledTicks(
            long gameTime, CubePos cubePos, TickContainerAccess<T> target, TickContainerAccess<T> source, long subTickOrder
    ) {
        if (!(source instanceof SerializableTickContainer<?> rawSerializable)) {
            return subTickOrder;
        }
        long nextSubTickOrder = subTickOrder;
        SerializableTickContainer<T> serializable = (SerializableTickContainer<T>) rawSerializable;
        for (SavedTick<T> tick : serializable.pack(gameTime)) {
            BlockPos position = tick.pos();
            if (position.getX() < cubePos.minCubeX() || position.getX() > cubePos.maxCubeX()
                    || position.getY() < cubePos.minCubeY() || position.getY() > cubePos.maxCubeY()
                    || position.getZ() < cubePos.minCubeZ() || position.getZ() > cubePos.maxCubeZ()) {
                continue;
            }
            target.schedule(tick.unpack(gameTime, nextSubTickOrder++));
        }
        return nextSubTickOrder;
    }
""",
)
