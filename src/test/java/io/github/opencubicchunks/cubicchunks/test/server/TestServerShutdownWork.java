package io.github.opencubicchunks.cubicchunks.test.server;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.stream.Stream;

import io.github.opencubicchunks.cubicchunks.server.ServerShutdownWork;
import org.junit.jupiter.api.Test;

public class TestServerShutdownWork {
    @Test
    public void reportsWhetherAnyWorkItemMatches() {
        assertTrue(ServerShutdownWork.hasPendingWork(Stream.of("idle", "pending"), "pending"::equals));
        assertFalse(ServerShutdownWork.hasPendingWork(Stream.of("idle", "complete"), "pending"::equals));
    }
}
