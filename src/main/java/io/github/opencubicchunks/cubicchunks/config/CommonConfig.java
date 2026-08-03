package io.github.opencubicchunks.cubicchunks.config;

import java.io.File;

import com.electronwill.nightconfig.core.CommentedConfig;
import com.electronwill.nightconfig.core.Config;
import io.github.opencubicchunks.cubicchunks.CubicChunks;
import net.fabricmc.loader.api.FabricLoader;

public class CommonConfig extends BaseConfig {
    private static final String FILE_NAME = "cubicchunks_common.toml";
    // Note that this relies on IS_IN_TEST being set before this class is loaded.
    private static final File FILE_PATH = CubicChunks.IS_IN_TEST ? null : FabricLoader.getInstance().getConfigDir().resolve(FILE_NAME).toFile();

    private static final String KEY_GENERAL = "general";
    private static final String KEY_VERTICAL_VIEW_DISTANCE = KEY_GENERAL + ".verticalViewDistance";
    private static final int DEFAULT_VERTICAL_VIEW_DISTANCE = 8;
    private static final String KEY_GENERATE_NEW_WORLDS_AS_CC = KEY_GENERAL + ".generateNewWorldsAsCC";

    private final CommentedConfig config;

    private CommonConfig(CommentedConfig config) {
        this.config = config;
    }

    private static CommentedConfig createDefaultConfig() {
        Config.setInsertionOrderPreserved(true);
        var config = CommentedConfig.inMemory();
        config.set(KEY_VERTICAL_VIEW_DISTANCE, DEFAULT_VERTICAL_VIEW_DISTANCE);
        config.setComment(KEY_VERTICAL_VIEW_DISTANCE, """
                 The vertical view distance for players in Cubic Chunks dimensions (similar to vanilla render distance for the horizontal axes).\
                """);
        config.set(KEY_GENERATE_NEW_WORLDS_AS_CC, true);
        config.setComment(KEY_GENERATE_NEW_WORLDS_AS_CC,
                """
                         Whether or not newly-created worlds generate using Cubic Chunks. (On the client, this is toggled by the button in the world creation GUI.)\
                        """);
        return config;
    }

    public void markDirty() {
        write(FILE_PATH, config);
    }

    public int getVerticalViewDistance() {
        return config.getInt(KEY_VERTICAL_VIEW_DISTANCE);
    }

    public boolean shouldGenerateNewWorldsAsCC() {
        return config.get(KEY_GENERATE_NEW_WORLDS_AS_CC);
    }

    public void setVerticalViewDistance(int verticalViewDistance) {
        config.set(KEY_VERTICAL_VIEW_DISTANCE, verticalViewDistance);
    }

    public void setGenerateNewWorldsAsCC(boolean generateNewWorldsAsCC) {
        config.set(KEY_GENERATE_NEW_WORLDS_AS_CC, generateNewWorldsAsCC);
    }

    public static CommonConfig getConfig() {
        var config = createDefaultConfig();
        if (CubicChunks.IS_IN_TEST) {
            return new CommonConfig(config);
        }
        if (FILE_PATH.exists()) {
            read(FILE_PATH, config);
        }
        var commonConfig = new CommonConfig(config);
        write(FILE_PATH, config);
        return commonConfig;
    }
}
