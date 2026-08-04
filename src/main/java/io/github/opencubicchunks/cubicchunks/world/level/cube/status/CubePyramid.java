package io.github.opencubicchunks.cubicchunks.world.level.cube.status;

import java.util.ArrayList;
import java.util.List;
import java.util.function.UnaryOperator;

import com.google.common.collect.ImmutableList;
import io.github.notstirred.dasm.api.annotations.Dasm;
import io.github.notstirred.dasm.api.annotations.redirect.redirects.AddFieldToSets;
import io.github.opencubicchunks.cubicchunks.mixin.dasmsets.ChunkToCubeSet;
import io.github.opencubicchunks.cubicchunks.mixin.dasmsets.GlobalSet;
import net.minecraft.world.level.chunk.status.ChunkPyramid;
import net.minecraft.world.level.chunk.status.ChunkStatus;
import net.minecraft.world.level.chunk.status.ChunkStep;

/**
 * {@link ChunkPyramid} equivalent for cubes. The chains are defined directly so
 * startup does not depend on cloning Minecraft's static initializer at runtime.
 */
@Dasm(GlobalSet.class)
public record CubePyramid(ImmutableList<CubeStep> steps) {
    @AddFieldToSets(containers = ChunkToCubeSet.ChunkPyramid_to_CubePyramid_redirects.class,
            field = "GENERATION_PYRAMID:Lnet/minecraft/world/level/chunk/status/ChunkPyramid;")
    public static final CubePyramid CC_GENERATION_PYRAMID_CUBES = new Builder()
            .step(ChunkStatus.EMPTY, step -> step)
            .step(ChunkStatus.STRUCTURE_STARTS, step -> step.setTask(CubeStatusTasks::generateStructureStarts))
            .step(ChunkStatus.STRUCTURE_REFERENCES,
                    step -> step.addRequirement(ChunkStatus.STRUCTURE_STARTS, 8)
                            .setTask(CubeStatusTasks::generateStructureReferences))
            .step(ChunkStatus.BIOMES,
                    step -> step.addRequirement(ChunkStatus.STRUCTURE_STARTS, 8)
                            .setTask(CubeStatusTasks::generateBiomes))
            .step(ChunkStatus.NOISE,
                    step -> step.addRequirement(ChunkStatus.STRUCTURE_STARTS, 8)
                            .addRequirement(ChunkStatus.BIOMES, 1)
                            .blockStateWriteRadius(0)
                            .setTask(CubeStatusTasks::generateNoise))
            .step(ChunkStatus.SURFACE,
                    step -> step.addRequirement(ChunkStatus.STRUCTURE_STARTS, 8)
                            .addRequirement(ChunkStatus.BIOMES, 1)
                            .blockStateWriteRadius(0)
                            .setTask(CubeStatusTasks::generateSurface))
            .step(ChunkStatus.CARVERS,
                    step -> step.addRequirement(ChunkStatus.STRUCTURE_STARTS, 8)
                            .blockStateWriteRadius(0)
                            .setTask(CubeStatusTasks::generateCarvers))
            .step(ChunkStatus.FEATURES,
                    step -> step.addRequirement(ChunkStatus.STRUCTURE_STARTS, 8)
                            .addRequirement(ChunkStatus.CARVERS, 1)
                            .blockStateWriteRadius(1)
                            .setTask(CubeStatusTasks::generateFeatures))
            .step(ChunkStatus.INITIALIZE_LIGHT, step -> step.setTask(CubeStatusTasks::initializeLight))
            .step(ChunkStatus.LIGHT,
                    step -> step.addRequirement(ChunkStatus.INITIALIZE_LIGHT, 1)
                            .setTask(CubeStatusTasks::light))
            .step(ChunkStatus.SPAWN,
                    step -> step.addRequirement(ChunkStatus.BIOMES, 1)
                            .setTask(CubeStatusTasks::generateSpawn))
            .step(ChunkStatus.FULL, step -> step.setTask(CubeStatusTasks::full))
            .build();

    @AddFieldToSets(containers = ChunkToCubeSet.ChunkPyramid_to_CubePyramid_redirects.class,
            field = "LOADING_PYRAMID:Lnet/minecraft/world/level/chunk/status/ChunkPyramid;")
    public static final CubePyramid CC_LOADING_PYRAMID_CUBES = new Builder()
            .step(ChunkStatus.EMPTY, step -> step)
            .step(ChunkStatus.STRUCTURE_STARTS, step -> step.setTask(CubeStatusTasks::loadStructureStarts))
            .step(ChunkStatus.STRUCTURE_REFERENCES, step -> step)
            .step(ChunkStatus.BIOMES, step -> step)
            .step(ChunkStatus.NOISE, step -> step)
            .step(ChunkStatus.SURFACE, step -> step)
            .step(ChunkStatus.CARVERS, step -> step)
            .step(ChunkStatus.FEATURES, step -> step)
            .step(ChunkStatus.INITIALIZE_LIGHT, step -> step.setTask(CubeStatusTasks::initializeLight))
            .step(ChunkStatus.LIGHT,
                    step -> step.addRequirement(ChunkStatus.INITIALIZE_LIGHT, 1)
                            .setTask(CubeStatusTasks::light))
            .step(ChunkStatus.SPAWN, step -> step)
            .step(ChunkStatus.FULL, step -> step.setTask(CubeStatusTasks::full))
            .build();

    public CubeStep getStepTo(ChunkStatus status) {
        return this.steps.get(status.getIndex());
    }

    @Dasm(ChunkToCubeSet.class)
    public static class Builder {
        private final List<CubeStep> steps = new ArrayList<>();

        public CubePyramid build() {
            return new CubePyramid(ImmutableList.copyOf(this.steps));
        }

        public Builder step(ChunkStatus status, UnaryOperator<CubeStep.Builder> operator) {
            CubeStep.Builder stepBuilder;
            if (this.steps.isEmpty()) {
                stepBuilder = new CubeStep.Builder(status);
            } else {
                stepBuilder = new CubeStep.Builder(status, this.steps.getLast());
            }
            this.steps.add(operator.apply(stepBuilder).build());
            return this;
        }
    }
}
