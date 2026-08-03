#!/usr/bin/env bash
set -euo pipefail

probe_dir="$(mktemp -d)"
cp gradlew "$probe_dir/gradlew"
cp -R gradle "$probe_dir/gradle"
chmod +x "$probe_dir/gradlew"

cat > "$probe_dir/settings.gradle" <<'SETTINGS'
pluginManagement {
    repositories {
        maven { url = 'https://maven.fabricmc.net/' }
        gradlePluginPortal()
    }
}
rootProject.name = 'fabric-26.2-loom-probe'
SETTINGS

cat > "$probe_dir/gradle.properties" <<'PROPERTIES'
org.gradle.jvmargs=-Xmx2G
org.gradle.daemon=false
org.gradle.configuration-cache=false
minecraft_version=26.2
loader_version=0.19.3
loom_version=1.17-SNAPSHOT
fabric_api_version=0.156.0+26.2
PROPERTIES

cat > "$probe_dir/build.gradle" <<'BUILD'
plugins {
    id 'net.fabricmc.fabric-loom' version "${loom_version}"
}

repositories {
    mavenCentral()
}

dependencies {
    minecraft "com.mojang:minecraft:${minecraft_version}"
    implementation "net.fabricmc:fabric-loader:${loader_version}"
    implementation "net.fabricmc.fabric-api:fabric-api:${fabric_api_version}"
}

java {
    sourceCompatibility = JavaVersion.VERSION_25
    targetCompatibility = JavaVersion.VERSION_25
}

tasks.register('inspectMinecraft') {
    doLast {
        println "loom.disableObfuscation=${loom.disableObfuscation()}"
        sourceSets.main.compileClasspath.files.findAll { it.name.contains('minecraft') }.each {
            println "MINECRAFT_ARTIFACT ${it.length()} ${it.absolutePath}"
        }
    }
}
BUILD

"$probe_dir/gradlew" -p "$probe_dir" inspectMinecraft --refresh-dependencies --stacktrace --no-daemon 2>&1 | tee fabric-standalone-loom-probe.log

: > fabric-standalone-loom-jars.log
find "$probe_dir/.gradle/loom-cache" -type f -name '*.jar' -print0 2>/dev/null |
while IFS= read -r -d '' jar_path; do
    size="$(stat -c '%s' "$jar_path")"
    entries="$(unzip -Z1 "$jar_path" 2>/dev/null | wc -l || true)"
    classes="$(unzip -Z1 "$jar_path" 2>/dev/null | grep -c '\.class$' || true)"
    printf '%s entries=%s classes=%s %s\n' "$size" "$entries" "$classes" "$jar_path"
    if [[ "$jar_path" == *minecraft-merged*.jar ]]; then
        echo "--- representative classes: $jar_path ---"
        unzip -Z1 "$jar_path" | grep -E '(^|/)(BlockPos|Identifier|ResourceLocation|Level|ChunkAccess|StreamCodec|FriendlyByteBuf|CustomPacketPayload|SharedConstants)\.class$' | sort | head -n 300 || true
    fi
done | tee -a fabric-standalone-loom-jars.log
