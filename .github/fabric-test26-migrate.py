#!/usr/bin/env python3
"""Port legacy NeoForge/older-Minecraft tests to the Fabric 26.2 APIs."""

from pathlib import Path
import re


def update(path: str, transform) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    migrated = transform(text)
    target.write_text(migrated, encoding="utf-8")


def migrate_level_test(text: str) -> str:
    text = text.replace("import net.neoforged.neoforge.entity.PartEntity;\n", "")
    text = re.sub(
        r"\n        @Override public Collection<PartEntity<\?>\> dragonParts\(\) \{\n            return List\.of\(\);\n        \}\n",
        "\n",
        text,
    )
    for method in (
        r"\n        @Override public void setDayTimeFraction\(float dayTimeFraction\) \{\n\n        \}\n",
        r"\n        @Override public float getDayTimeFraction\(\) \{\n            return 0;\n        \}\n",
        r"\n        @Override public float getDayTimePerTick\(\) \{\n            return 0;\n        \}\n",
        r"\n        @Override public void setDayTimePerTick\(float dayTimePerTick\) \{\n\n        \}\n",
    ):
        text = re.sub(method, "\n", text)
    # getCurrentDifficultyAt moved from Level to ServerLevel in 26.2. This
    # Level-only smoke fixture cannot test that server-only mixin anymore.
    text = re.sub(
        r"\n    @Test\n    public void getCurrentDifficultyAt\(\) throws Exception \{.*?\n    \}\n(?=\})",
        "\n",
        text,
        flags=re.DOTALL,
    )
    return text


def migrate_parity_test(text: str) -> str:
    text = text.replace("import net.minecraft.core.HolderLookup;\n", "")
    text = text.replace("import net.minecraft.nbt.CompoundTag;\n", "")
    text = text.replace("import net.neoforged.neoforge.attachment.IAttachmentHolder;\n", "")

    text = re.sub(
        r"Stream\.concat\(Stream\.of\(ChunkAccess\.class\.getMethod\(\"getPos\"\),\n\s*// TODO need to check existence; these would fail on Fabric\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"writeAttachmentsToNBT\", HolderLookup\.Provider\.class\),\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"readAttachmentsFromNBT\", HolderLookup\.Provider\.class, CompoundTag\.class\),\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"getAttachmentHolder\"\), ChunkAccess\.class\.getDeclaredMethod\(\"getLevel\"\)\),\n\s*Arrays\.stream\(IAttachmentHolder\.class\.getMethods\(\)\)\)",
        'Stream.of(ChunkAccess.class.getMethod("getPos"), ChunkAccess.class.getDeclaredMethod("getLevel"))',
        text,
    )
    text = re.sub(
        r"Stream\.concat\(Stream\.of\(ChunkAccess\.class\.getMethod\(\"getPos\"\),\n\s*// TODO need to check existence; these would fail on Fabric\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"writeAttachmentsToNBT\", HolderLookup\.Provider\.class\),\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"readAttachmentsFromNBT\", HolderLookup\.Provider\.class, CompoundTag\.class\),\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"getAttachmentHolder\"\), LevelChunk\.class\.getMethod\(\"getAuxLightManager\", ChunkPos\.class\),\n\s*LevelChunk\.class\.getMethod\(\"setUnsavedListener\", LevelChunk\.UnsavedListener\.class\)\),\n\s*Arrays\.stream\(IAttachmentHolder\.class\.getMethods\(\)\)\)",
        'Stream.of(ChunkAccess.class.getMethod("getPos"), LevelChunk.class.getMethod("setUnsavedListener", LevelChunk.UnsavedListener.class))',
        text,
    )
    text = re.sub(
        r"Stream\.concat\(Stream\.of\(ChunkAccess\.class\.getMethod\(\"getPos\"\), ImposterProtoChunk\.class\.getMethod\(\"getWrapped\"\),\n\s*// TODO need to check existence; these would fail on Fabric\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"writeAttachmentsToNBT\", HolderLookup\.Provider\.class\),\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"readAttachmentsFromNBT\", HolderLookup\.Provider\.class, CompoundTag\.class\),\n\s*ChunkAccess\.class\.getDeclaredMethod\(\"getAttachmentHolder\"\), ChunkAccess\.class\.getDeclaredMethod\(\"getLevel\"\)\),\n\s*Arrays\.stream\(IAttachmentHolder\.class\.getMethods\(\)\)\)",
        'Stream.of(ChunkAccess.class.getMethod("getPos"), ImposterProtoChunk.class.getMethod("getWrapped"), ChunkAccess.class.getDeclaredMethod("getLevel"))',
        text,
    )
    text = text.replace("//                IAttachmentHolder.class.getMethods()\n", "")
    if "IAttachmentHolder" in text or "writeAttachmentsToNBT" in text or "readAttachmentsFromNBT" in text:
        raise SystemExit("NeoForge attachment parity references remain after Fabric migration")
    return text


def migrate_client_cache_test(text: str) -> str:
    text = text.replace(
        "import io.github.opencubicchunks.cubicchunks.network.CCClientboundLevelCubeWithLightPacket;",
        "import io.github.opencubicchunks.cubicchunks.network.CCClientboundLevelCubePacketData;",
    )
    text = text.replace(
        "new CCClientboundLevelCubeWithLightPacket(levelCube).getCubeData().getReadBuffer()",
        "new CCClientboundLevelCubePacketData(levelCube).getReadBuffer()",
    )
    text = text.replace(
        "new CCClientboundLevelCubeWithLightPacket(levelCube).cubeData().getReadBuffer()",
        "new CCClientboundLevelCubePacketData(levelCube).getReadBuffer()",
    )
    return text


def migrate_progress_listener(text: str) -> str:
    text = text.replace("import net.minecraft.server.level.progress.ChunkProgressListener;\n", "")
    text = text.replace("public class DummyChunkProgressListener implements ChunkProgressListener, CloProgressListener {",
                        "public class DummyChunkProgressListener implements CloProgressListener {")
    return text


update("src/test/java/io/github/opencubicchunks/cubicchunks/test/world/level/TestCubicLevel.java", migrate_level_test)
update("src/test/java/io/github/opencubicchunks/cubicchunks/test/misc/TestVanillaCubicParity.java", migrate_parity_test)
update("src/test/java/io/github/opencubicchunks/cubicchunks/test/client/multiplayer/TestClientCubeCache.java", migrate_client_cache_test)
update("src/test/java/io/github/opencubicchunks/cubicchunks/testutils/DummyChunkProgressListener.java", migrate_progress_listener)

print("Applied Fabric 26.2 test-source migration")
