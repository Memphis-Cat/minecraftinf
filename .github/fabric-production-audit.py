#!/usr/bin/env python3
"""Reject known no-op or placeholder CubicChunks runtime implementations before publishing Fabric 26.2."""

from __future__ import annotations

from pathlib import Path

ROOT = Path("src/main/java")
TEST_ROOT = Path("src/test/java")

STORAGE = ROOT / "io/github/opencubicchunks/cubicchunks/mixin/core/common/world/level/chunk/storage/MixinChunkStorage.java"
PACKET = ROOT / "io/github/opencubicchunks/cubicchunks/network/CCClientboundLevelCubeWithLightPacket.java"
PACKET_DATA = ROOT / "io/github/opencubicchunks/cubicchunks/network/CCClientboundLevelCubePacketData.java"
LIGHT_DATA = ROOT / "io/github/opencubicchunks/cubicchunks/network/CCClientboundCubeLightData.java"
CLIENT_HANDLER = ROOT / "io/github/opencubicchunks/cubicchunks/network/CCClientNetworkHandler.java"
SENDER = ROOT / "io/github/opencubicchunks/cubicchunks/mixin/core/common/server/network/MixinPlayerChunkSender.java"
NETWORK_TEST = TEST_ROOT / "io/github/opencubicchunks/cubicchunks/network/TestCubeNetworkPayloads.java"

FORBIDDEN_STORAGE = (
    "return false; // TODO (P2) should be dasm'd once IOWorker is done",
    "// TODO (P2) loading - this method should be dasm'd",
    "// TODO (P2) loading/unloading",
)

REQUIRED_STORAGE = (
    "return this.isOldChunkAround(pos.chunkPos(), radius);",
    "Coords.cubeToSection(cubePos.getX(), localX)",
    "return this.read(cloPos.chunkPos());",
    "MixinChunkMap checks CubeStorage before the transformed vanilla load path",
    "this.write(cloPos.chunkPos(), chunkData);",
    "throw new IllegalStateException(\"Cube write bypassed CubeStorage for \" + cloPos);",
)

NETWORK_REQUIREMENTS = {
    PACKET: (
        "CCClientboundCubeLightData lightData",
        "new CCClientboundCubeLightData(cube, lightEngine)",
        "cubeData.validateFor(pos);",
    ),
    PACKET_DATA: (
        "BuiltInRegistries.BLOCK_ENTITY_TYPE.getId",
        "getBlockEntitiesTagsConsumer()",
        "validateFor(CubePos cubePos)",
    ),
    LIGHT_DATA: (
        "LightLayer.BLOCK",
        "LightLayer.SKY",
        "lightEngine.queueSectionData",
        "CubicConstants.SECTION_COUNT",
    ),
    CLIENT_HANDLER: (
        "payload.cubeData().getBlockEntitiesTagsConsumer()",
        "payload.lightData().apply(cubePos, lightEngine)",
        "lightEngine.updateSectionStatus",
        "level.setSectionRangeDirty",
    ),
    SENDER: (
        "new CCClientboundLevelCubeWithLightPacket(cube, level.getLightEngine())",
    ),
    NETWORK_TEST: (
        "cubePacketRoundTripsSectionsBlockEntitiesAndLight",
        "packetRejectsBlockEntitiesOutsideItsCube",
    ),
}

NETWORK_FORBIDDEN = (
    "TODO name is a lie",
    "TODO block entities",
    "TODO heightmaps",
    "blockEntityTagOutput -> {}",
    "blockEntityTagOutput -> { }",
)

GLOBAL_FORBIDDEN = (
    'throw new UnsupportedOperationException("not yet implemented")',
    'throw new UnsupportedOperationException("TODO")',
    "return true; // TODO",
    "return false; // TODO",
)


def main() -> int:
    failures: list[str] = []

    if not STORAGE.is_file():
        failures.append(f"missing required runtime source: {STORAGE}")
    else:
        storage_text = STORAGE.read_text(encoding="utf-8")
        for marker in FORBIDDEN_STORAGE:
            if marker in storage_text:
                failures.append(f"unfinished storage implementation in {STORAGE}: {marker}")
        for marker in REQUIRED_STORAGE:
            if marker not in storage_text:
                failures.append(f"missing completed storage behavior in {STORAGE}: {marker}")

    for path, markers in NETWORK_REQUIREMENTS.items():
        if not path.is_file():
            failures.append(f"missing completed network source/test: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                failures.append(f"missing completed network behavior in {path}: {marker}")
        for marker in NETWORK_FORBIDDEN:
            if marker in text:
                failures.append(f"unfinished network marker in {path}: {marker}")

    for path in ROOT.rglob("*.java"):
        text = path.read_text(encoding="utf-8")
        for marker in GLOBAL_FORBIDDEN:
            if marker in text:
                failures.append(f"unfinished runtime marker in {path}: {marker}")

    if failures:
        print("Fabric 26.2 production audit failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Fabric 26.2 production audit passed: storage, cube networking, light data and block-entity payloads are implemented and tested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
