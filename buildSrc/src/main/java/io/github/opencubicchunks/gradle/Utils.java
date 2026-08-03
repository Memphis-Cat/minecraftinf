package io.github.opencubicchunks.gradle;

import javax.annotation.Nonnull;

import org.gradle.api.Project;
import org.gradle.api.plugins.JavaPluginExtension;

public final class Utils {
    private Utils() {}

    @Nonnull
    public static JavaPluginExtension getJavaPluginExtension(@Nonnull Project target) {
        return target.getExtensions().getByType(JavaPluginExtension.class);
    }
}
