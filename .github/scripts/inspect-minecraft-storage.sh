#!/usr/bin/env bash
set -euo pipefail

readonly OUTPUT_DIR="build/minecraft-storage-inspection"
readonly NEEDLE="net/minecraft/world/level/chunk/storage/SerializableChunkData.class"

mkdir -p "${OUTPUT_DIR}"

minecraft_jar=""
while IFS= read -r candidate; do
    if unzip -Z1 "${candidate}" "${NEEDLE}" 2>/dev/null | grep -qx "${NEEDLE}"; then
        minecraft_jar="${candidate}"
        break
    fi
done < <(find "${HOME}/.gradle/caches" .gradle build -type f -name '*.jar' 2>/dev/null | sort)

if [[ -z "${minecraft_jar}" ]]; then
    echo "Could not find the transformed Minecraft jar containing ${NEEDLE}." >&2
    find "${HOME}/.gradle/caches" .gradle build -type f -name '*.jar' 2>/dev/null | sort > "${OUTPUT_DIR}/searched-jars.txt"
    exit 1
fi

printf '%s\n' "${minecraft_jar}" > "${OUTPUT_DIR}/minecraft-jar.txt"

classes=(
    net.minecraft.client.color.block.BlockTintCache
    net.minecraft.client.multiplayer.ClientChunkCache
    net.minecraft.client.multiplayer.ClientLevel
    net.minecraft.server.level.ChunkMap
    net.minecraft.server.level.DistanceManager
    net.minecraft.server.level.ServerChunkCache
    net.minecraft.server.level.ServerLevel
    net.minecraft.util.StaticCache2D
    net.minecraft.world.level.chunk.ChunkAccess
    net.minecraft.world.level.chunk.ChunkGenerator
    net.minecraft.world.level.chunk.LevelChunk
    net.minecraft.world.level.chunk.LevelChunkSection
    net.minecraft.world.level.chunk.PalettedContainer
    net.minecraft.world.level.chunk.status.ChunkStatusTasks
    net.minecraft.world.level.chunk.status.WorldGenContext
    net.minecraft.world.level.chunk.storage.ChunkStorage
    net.minecraft.world.level.chunk.storage.IOWorker
    net.minecraft.world.level.chunk.storage.RegionFileStorage
    net.minecraft.world.level.chunk.storage.RegionStorageInfo
    net.minecraft.world.level.chunk.storage.SerializableChunkData
    net.minecraft.world.level.entity.TransientEntitySectionManager
    net.minecraft.world.level.levelgen.Heightmap
    net.minecraft.world.level.levelgen.NoiseBasedChunkGenerator
    net.minecraft.world.level.lighting.ChunkSkyLightSources
    net.minecraft.world.level.lighting.LevelLightEngine
    net.minecraft.world.level.lighting.LightEngine
    net.minecraft.world.level.lighting.ThreadedLevelLightEngine
    net.minecraft.world.ticks.LevelChunkTicks
    net.minecraft.world.ticks.LevelTicks
    net.minecraft.world.entity.ai.village.poi.PoiManager
    net.minecraft.nbt.NbtIo
)

for class_name in "${classes[@]}"; do
    output_name="${class_name//./_}.txt"
    if ! javap -classpath "${minecraft_jar}" -p -s -c -constants "${class_name}" > "${OUTPUT_DIR}/${output_name}" 2>&1; then
        echo "javap failed for ${class_name}" >> "${OUTPUT_DIR}/failures.txt"
    fi
done

jar tf "${minecraft_jar}" \
    | grep -E '(^net/minecraft/client/multiplayer/Client(Level|ChunkCache)|^net/minecraft/server/level/(ChunkMap|DistanceManager|ServerChunkCache|ServerLevel)|^net/minecraft/world/level/(chunk/|entity/TransientEntitySectionManager|levelgen/(Heightmap|NoiseBasedChunkGenerator)|lighting/|ticks/)|^net/minecraft/nbt/NbtIo)' \
    | sort > "${OUTPUT_DIR}/relevant-classes.txt"

echo "Minecraft API inspection written to ${OUTPUT_DIR}."
