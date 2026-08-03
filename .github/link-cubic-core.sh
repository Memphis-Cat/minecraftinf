#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
input_jar="$root_dir/CubicChunksCore/build/libs/CubicChunksCore.jar"
output_jar="$root_dir/build/fabric-header-libs/CubicChunksCore-linked.jar"
headers_config="$root_dir/javaHeaders.json"

if [[ ! -s "$input_jar" ]]; then
    echo "Missing CubicChunksCore jar: $input_jar" >&2
    echo "Build CubicChunksCore before linking its Java headers." >&2
    exit 1
fi

work_dir="$(mktemp -d)"
gradle_home="$(mktemp -d)"
cleanup() {
    rm -rf "$work_dir" "$gradle_home"
}
trap cleanup EXIT

cat > "$work_dir/settings.gradle" <<'SETTINGS'
pluginManagement {
    repositories {
        mavenCentral()
        gradlePluginPortal()
        maven { url = 'https://jitpack.io' }
    }
}
rootProject.name = 'cubicchunks-core-header-linker'
SETTINGS

cat > "$work_dir/build.gradle" <<'BUILD'
plugins {
    id 'java-library'
    id 'io.github.opencubicchunks.javaheaders' version '1.2.8'
}

repositories {
    mavenCentral()
    maven { url = 'https://jitpack.io' }
}

javaHeaders {
    setAcceptedJars('.*CubicChunksCore.*')
    setConfig(file(System.getenv('CC_HEADERS_CONFIG')))
}

configurations {
    linkedCore {
        canBeConsumed = false
        canBeResolved = true
    }
}

dependencies {
    linkedCore files(System.getenv('CC_CORE_INPUT'))
}

def linkedOutput = file(System.getenv('CC_LINK_OUTPUT'))

tasks.register('linkCoreHeaders', Copy) {
    from(configurations.linkedCore)
    into(linkedOutput.parentFile)
    rename { linkedOutput.name }

    doFirst {
        linkedOutput.parentFile.mkdirs()
        linkedOutput.delete()
    }

    doLast {
        if (!linkedOutput.isFile() || linkedOutput.length() == 0L) {
            throw new GradleException("JavaHeaders did not create ${linkedOutput}")
        }
        println "Linked CubicChunksCore headers: ${linkedOutput} (${linkedOutput.length()} bytes)"
    }
}
BUILD

export CC_CORE_INPUT="$input_jar"
export CC_LINK_OUTPUT="$output_jar"
export CC_HEADERS_CONFIG="$headers_config"
export GRADLE_USER_HOME="$gradle_home"

chmod +x "$root_dir/gradlew"
"$root_dir/gradlew" -p "$work_dir" linkCoreHeaders --stacktrace --no-daemon

test -s "$output_jar"
