#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
input_jar="$root_dir/CubicChunksCore/build/libs/CubicChunksCore.jar"
tests_input_jar="$root_dir/CubicChunksCore/build/libs/CubicChunksCore-tests.jar"
output_jar="$root_dir/build/fabric-header-libs/CubicChunksCore-linked.jar"
tests_output_jar="$root_dir/build/fabric-header-libs/CubicChunksCore-tests-linked.jar"
headers_config="$root_dir/javaHeaders.json"

for required in "$input_jar" "$tests_input_jar"; do
    if [[ ! -s "$required" ]]; then
        echo "Missing CubicChunksCore jar: $required" >&2
        echo "Build CubicChunksCore and testsJar before linking its Java headers." >&2
        exit 1
    fi
done

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
    linkedCoreTests {
        canBeConsumed = false
        canBeResolved = true
    }
}

dependencies {
    linkedCore files(System.getenv('CC_CORE_INPUT'))
    linkedCoreTests files(System.getenv('CC_CORE_TESTS_INPUT'))
}

def linkedOutput = file(System.getenv('CC_LINK_OUTPUT'))
def linkedTestsOutput = file(System.getenv('CC_TESTS_LINK_OUTPUT'))

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

tasks.register('linkCoreTestHeaders', Copy) {
    from(configurations.linkedCoreTests)
    into(linkedTestsOutput.parentFile)
    rename { linkedTestsOutput.name }

    doFirst {
        linkedTestsOutput.parentFile.mkdirs()
        linkedTestsOutput.delete()
    }

    doLast {
        if (!linkedTestsOutput.isFile() || linkedTestsOutput.length() == 0L) {
            throw new GradleException("JavaHeaders did not create ${linkedTestsOutput}")
        }
        println "Linked CubicChunksCore test headers: ${linkedTestsOutput} (${linkedTestsOutput.length()} bytes)"
    }
}
BUILD

export CC_CORE_INPUT="$input_jar"
export CC_CORE_TESTS_INPUT="$tests_input_jar"
export CC_LINK_OUTPUT="$output_jar"
export CC_TESTS_LINK_OUTPUT="$tests_output_jar"
export CC_HEADERS_CONFIG="$headers_config"
export GRADLE_USER_HOME="$gradle_home"

chmod +x "$root_dir/gradlew"
"$root_dir/gradlew" -p "$work_dir" linkCoreHeaders linkCoreTestHeaders --stacktrace --no-daemon

test -s "$output_jar"
test -s "$tests_output_jar"
