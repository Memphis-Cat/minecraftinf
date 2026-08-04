#!/usr/bin/env python3
"""Wire CubicChunksCore's published test jar into the Fabric parent test runtime."""

from pathlib import Path
import runpy

# Port Core before its jar and test archive are built.
runpy.run_path(".github/fabric-core26-migrate.py", run_name="__fabric_core26_migrate__")

path = Path("build.gradle")
text = path.read_text(encoding="utf-8")

hamcrest = "    testImplementation 'org.hamcrest:hamcrest:2.2'\n"
if hamcrest not in text:
    anchor = "    testImplementation 'org.assertj:assertj-core:3.27.4'\n"
    if anchor not in text:
        raise SystemExit("Unable to locate the Fabric test dependency block")
    text = text.replace(anchor, anchor + hamcrest, 1)

# Loom's merged 26.2 artifact is resources-only in this project. Production
# compilation already uses the widened Mojang distribution; tests must use the
# same classes at runtime or JUnit cannot load Minecraft's public classes.
test_minecraft_runtime = "    testRuntimeOnly files(widenedMinecraftClientJar)\n"
if test_minecraft_runtime not in text:
    anchor = "    compileOnly files(widenedMinecraftClientJar)\n"
    if anchor not in text:
        raise SystemExit("Unable to locate the widened Minecraft 26.2 compile dependency")
    text = text.replace(anchor, anchor + test_minecraft_runtime, 1)

snippet = r'''// CubicChunksCore disables its own Test task because its standalone jar only has
// compile-time Minecraft headers. It publishes compiled tests separately so the
// parent mod can execute them against the linked, Minecraft-backed Core jar.
def coreTestsJar = file("${rootDir}/CubicChunksCore/build/libs/CubicChunksCore-tests.jar")
def coreTestsClassesDir = layout.buildDirectory.dir('generated/core-tests/classes')

def unpackCoreTests = tasks.register('unpackCoreTests', Sync) {
    group = 'verification'
    description = 'Unpacks CubicChunksCore tests without its untransformed Minecraft header classes.'
    inputs.file(coreTestsJar)
    outputs.dir(coreTestsClassesDir)
    from({ zipTree(coreTestsJar) }) {
        exclude 'META-INF/**'
        exclude 'io/github/opencubicchunks/cc_core/minecraft/**'
    }
    into coreTestsClassesDir
    doFirst {
        if (!coreTestsJar.isFile() || coreTestsJar.length() == 0L) {
            throw new GradleException("Missing ${coreTestsJar}; run CubicChunksCore:testsJar first")
        }
    }
}

tasks.named('test') {
    enabled = true
    dependsOn prepareMinecraftCompileHeaders
}

def coreTest = tasks.register('coreTest', Test) {
    enabled = true
    group = 'verification'
    description = 'Runs CubicChunksCore tests against the linked Fabric/Minecraft classpath.'
    dependsOn unpackCoreTests, testClasses, prepareMinecraftCompileHeaders
    testClassesDirs = files(coreTestsClassesDir)
    classpath = sourceSets.test.runtimeClasspath + files(coreTestsClassesDir)
    useJUnitPlatform()
    shouldRunAfter tasks.named('test')

    // Int3HashSet intentionally uses Netty's off-heap allocator. Java 25 no
    // longer permits Netty to acquire Unsafe reflectively without these opens.
    systemProperty 'io.netty.tryReflectionSetAccessible', 'true'
    jvmArgs '--add-opens=java.base/java.nio=ALL-UNNAMED',
            '--add-opens=jdk.unsupported/sun.misc=ALL-UNNAMED'

    testLogging {
        events 'passed', 'skipped', 'failed'
        exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
    }
    doFirst {
        def discovered = fileTree(coreTestsClassesDir).matching { include '**/*Test.class' }.files.size()
        if (discovered == 0) {
            throw new GradleException("No CubicChunksCore test classes were unpacked from ${coreTestsJar}")
        }
        println "Running ${discovered} CubicChunksCore test classes"
    }
}

tasks.named('check') {
    dependsOn coreTest
}

'''

if "def coreTestsJar = file(" not in text:
    marker = "spotless {\n"
    if marker not in text:
        raise SystemExit("Unable to locate insertion point for CubicChunksCore tests")
    text = text.replace(marker, snippet + marker, 1)

path.write_text(text, encoding="utf-8")
runpy.run_path(".github/fabric-runtime-fixes.py", run_name="__fabric_runtime_fixes__")
runpy.run_path(".github/fabric-test26-migrate.py", run_name="__fabric_test26_migrate__")
runpy.run_path(".github/fabric-test26-finalize.py", run_name="__fabric_test26_finalize__")
runpy.run_path(".github/fabric-test-runtime26.py", run_name="__fabric_test_runtime26__")
runpy.run_path(".github/fabric-packaging26.py", run_name="__fabric_packaging26__")
runpy.run_path(".github/fabric-run-classpath26.py", run_name="__fabric_run_classpath26__")
runpy.run_path(".github/fabric-level26-runtime.py", run_name="__fabric_level26_runtime__")
runpy.run_path(".github/fabric-accesswidener26.py", run_name="__fabric_accesswidener26__")
storage_source = Path("src/main/java/io/github/opencubicchunks/cubicchunks/world/storage/CubeStorage.java")
if "void save(CloAccess cube)" not in storage_source.read_text(encoding="utf-8"):
    runpy.run_path(".github/fabric-persistence26-migrate.py", run_name="__fabric_persistence26_migrate__")
print("Configured migrated Core, Fabric-compatible 26.2 tests and complete cube persistence")
