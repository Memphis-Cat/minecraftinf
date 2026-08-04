package io.github.opencubicchunks.cubicchunks.world.level.cube.status;

import java.util.Arrays;
import java.util.concurrent.CompletableFuture;

import javax.annotation.Nullable;

import com.google.common.collect.ImmutableList;
import io.github.notstirred.dasm.api.annotations.Dasm;
import io.github.notstirred.dasm.api.annotations.redirect.redirects.AddFieldToSets;
import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cubicchunks.mixin.dasmsets.ChunkToCubeSet;
import io.github.opencubicchunks.cubicchunks.util.StaticCache3D;
import io.github.opencubicchunks.cubicchunks.world.level.cube.CubeAccess;
import io.github.opencubicchunks.cubicchunks.world.level.cube.ProtoCube;
import net.minecraft.server.level.GenerationChunkHolder;
import net.minecraft.world.level.chunk.status.ChunkDependencies;
import net.minecraft.world.level.chunk.status.ChunkStatus;
import net.minecraft.world.level.chunk.status.ChunkStatusTask;
import net.minecraft.world.level.chunk.status.ChunkStep;
import net.minecraft.world.level.chunk.status.WorldGenContext;

/**
 * {@link ChunkStep} equivalent for a cube. It stores a {@link CubeStatusTask}
 * and expresses dependency radii in cubes rather than sections.
 */
@Dasm(ChunkToCubeSet.class)
public record CubeStep(
        ChunkStatus targetStatus, ChunkDependencies directDependencies, ChunkDependencies accumulatedDependencies, int blockStateWriteRadius,
        CubeStatusTask task
) {
    public int getAccumulatedRadiusOf(ChunkStatus status) {
        return status == this.targetStatus ? 0 : this.accumulatedDependencies.getRadiusOf(status);
    }

    public CompletableFuture<CubeAccess> apply(
            WorldGenContext worldGenContext, StaticCache3D<GenerationChunkHolder> cache, CubeAccess cube
    ) {
        CompletableFuture<CubeAccess> result = this.task.doWork(worldGenContext, this, cache, cube);
        if (!cube.getPersistedStatus().isBefore(this.targetStatus)) {
            return result;
        }
        return result.thenApply(generatedCube -> {
            if (generatedCube instanceof ProtoCube protoCube && protoCube.getPersistedStatus().isBefore(this.targetStatus)) {
                protoCube.setPersistedStatus(this.targetStatus);
            }
            return generatedCube;
        });
    }

    @Dasm(ChunkToCubeSet.class)
    public static class Builder {
        private final ChunkStatus status;
        @AddFieldToSets(containers = ChunkToCubeSet.ChunkStep$Builder_to_CubeStep$Builder_redirects.class,
                field = "parent:Lnet/minecraft/world/level/chunk/status/ChunkStep;")
        private final @Nullable CubeStep parent;
        private ChunkStatus[] directDependenciesByRadius;
        private int blockStateWriteRadius = -1;
        @AddFieldToSets(containers = ChunkToCubeSet.ChunkStep$Builder_to_CubeStep$Builder_redirects.class,
                field = "task:Lnet/minecraft/world/level/chunk/status/ChunkStatusTask;")
        private CubeStatusTask task = CubeStatusTasks::passThrough;

        protected Builder(ChunkStatus status) {
            if (status.getParent() != status) {
                throw new IllegalArgumentException("Not starting with the first status: " + status);
            }
            this.status = status;
            this.parent = null;
            this.directDependenciesByRadius = new ChunkStatus[0];
        }

        protected Builder(ChunkStatus status, CubeStep parent) {
            if (parent.targetStatus().getIndex() != status.getIndex() - 1) {
                throw new IllegalArgumentException("Out of order status: " + status);
            }
            this.status = status;
            this.parent = parent;
            this.directDependenciesByRadius = new ChunkStatus[]{parent.targetStatus()};
        }

        public CubeStep.Builder addRequirement(ChunkStatus requiredStatus, int radiusInSections) {
            if (requiredStatus.isOrAfter(this.status)) {
                throw new IllegalArgumentException("Status " + requiredStatus + " can not be required by " + this.status);
            }

            ChunkStatus[] previous = this.directDependenciesByRadius;
            int newLength = Coords.sectionToCubeCeil(radiusInSections) + 1;
            if (newLength > previous.length) {
                this.directDependenciesByRadius = new ChunkStatus[newLength];
                Arrays.fill(this.directDependenciesByRadius, requiredStatus);
            }
            for (int i = 0; i < Math.min(newLength, previous.length); i++) {
                this.directDependenciesByRadius[i] = ChunkStatus.max(previous[i], requiredStatus);
            }
            return this;
        }

        public CubeStep.Builder blockStateWriteRadius(int radiusInSections) {
            this.blockStateWriteRadius = Coords.sectionToCubeCeil(radiusInSections);
            return this;
        }

        public CubeStep.Builder setTask(CubeStatusTask task) {
            this.task = task;
            return this;
        }

        public CubeStep build() {
            return new CubeStep(
                    this.status,
                    new ChunkDependencies(ImmutableList.copyOf(this.directDependenciesByRadius)),
                    new ChunkDependencies(ImmutableList.copyOf(this.buildAccumulatedDependencies())),
                    this.blockStateWriteRadius,
                    this.task
            );
        }

        private ChunkStatus[] buildAccumulatedDependencies() {
            if (this.parent == null) {
                return this.directDependenciesByRadius;
            }

            int radiusOfParent = this.getRadiusOfParent(this.parent.targetStatus());
            ChunkDependencies parentDependencies = this.parent.accumulatedDependencies();
            ChunkStatus[] accumulatedDependencies = new ChunkStatus[
                    Math.max(radiusOfParent + parentDependencies.size(), this.directDependenciesByRadius.length)
            ];
            for (int distance = 0; distance < accumulatedDependencies.length; distance++) {
                int distanceInParent = distance - radiusOfParent;
                if (distanceInParent < 0 || distanceInParent >= parentDependencies.size()) {
                    accumulatedDependencies[distance] = this.directDependenciesByRadius[distance];
                } else if (distance >= this.directDependenciesByRadius.length) {
                    accumulatedDependencies[distance] = parentDependencies.get(distanceInParent);
                } else {
                    accumulatedDependencies[distance] = ChunkStatus.max(
                            this.directDependenciesByRadius[distance], parentDependencies.get(distanceInParent)
                    );
                }
            }
            return accumulatedDependencies;
        }

        private int getRadiusOfParent(ChunkStatus parentStatus) {
            for (int i = this.directDependenciesByRadius.length - 1; i >= 0; i--) {
                if (this.directDependenciesByRadius[i].isOrAfter(parentStatus)) {
                    return i;
                }
            }
            return 0;
        }
    }
}
