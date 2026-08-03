from pathlib import Path

for relative in (
    "buildSrc/src/main/java/io/github/opencubicchunks/gradle/MixinGenExtension.java",
    "buildSrc/src/main/java/io/github/opencubicchunks/gradle/DasmGenExtension.java",
):
    path = Path(relative)
    text = path.read_text(encoding="utf-8")
    if "JavaPluginConvention" in text:
        path.write_text(text.replace("JavaPluginConvention", "JavaPluginExtension"), encoding="utf-8")
    elif "JavaPluginExtension" not in text:
        raise SystemExit(f"Expected Gradle Java plugin API use was not found in {relative}")

core_build = Path("CubicChunksCore/build.gradle")
core_text = core_build.read_text(encoding="utf-8")
if "jcenter()" in core_text:
    core_text = core_text.replace("jcenter()", "mavenCentral()")
elif "mavenCentral()" not in core_text:
    raise SystemExit("Expected a Maven repository declaration in CubicChunksCore/build.gradle")

core_text = core_text.replace("import io.github.opencubicchunks.gradle.GeneratePackageInfo\n\n", "", 1)
package_info_task = """task generatePackageInfo {
    setGroup('filegen')
    doFirst {
        GeneratePackageInfo.generateFiles(sourceSets.main)
        GeneratePackageInfo.generateFiles(sourceSets.test)
    }
}
"""
if package_info_task in core_text:
    core_text = core_text.replace(
        package_info_task,
        """task generatePackageInfo {
    setGroup('filegen')
}
""",
        1,
    )
elif "GeneratePackageInfo.generateFiles" in core_text:
    raise SystemExit("Could not isolate CubicChunksCore's package-info generator")
core_build.write_text(core_text, encoding="utf-8")

core_buildsrc = Path("CubicChunksCore/buildSrc/build.gradle")
core_buildsrc_text = core_buildsrc.read_text(encoding="utf-8")
core_buildsrc_text = core_buildsrc_text.replace("jcenter()", "mavenCentral()")
core_buildsrc_text = core_buildsrc_text.replace(
    'org.ajoberstar.grgit:grgit-core:3.1.1',
    'org.ajoberstar.grgit:grgit-core:5.3.0',
)
core_buildsrc_text = core_buildsrc_text.replace(
    "name: 'gson', version: '2.8.5'",
    "name: 'gson', version: '2.14.0'",
)
if "grgit-core:3.1.1" in core_buildsrc_text or "jcenter()" in core_buildsrc_text:
    raise SystemExit("CubicChunksCore buildSrc dependency migration was incomplete")
core_buildsrc.write_text(core_buildsrc_text, encoding="utf-8")

# CubicChunksCore is a submodule without its own settings file. Give it an
# isolated build root so its Gradle 7.6 wrapper does not load the parent
# Fabric/Loom build or the parent buildSrc project.
Path("CubicChunksCore/settings.gradle").write_text(
    "rootProject.name = 'CubicChunksCore'\n", encoding="utf-8"
)
