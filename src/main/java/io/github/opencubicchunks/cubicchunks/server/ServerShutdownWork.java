package io.github.opencubicchunks.cubicchunks.server;

import java.util.function.Predicate;
import java.util.stream.Stream;

/** Restores vanilla pending-work checks during server shutdown. */
public final class ServerShutdownWork {
    private ServerShutdownWork() {}

    public static <T> boolean hasPendingWork(Stream<T> workItems, Predicate<? super T> predicate) {
        return workItems.anyMatch(predicate);
    }
}
