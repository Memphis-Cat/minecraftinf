#!/usr/bin/env python3
"""Port CubicChunksCore's Minecraft bridge and Java runtime assumptions to Minecraft 26.2/Java 25."""

from pathlib import Path
import re

root = Path("CubicChunksCore")
header = root / "src/main/java/io/github/opencubicchunks/cc_core/minecraft/MCChunkPos.java"
header.write_text(
    """package io.github.opencubicchunks.cc_core.minecraft;

import io.github.opencubicchunks.javaheaders.api.Header;

/** Minecraft 26.2 ChunkPos header used by JavaHeaders. */
@Header
public class MCChunkPos {
    public MCChunkPos(int x, int z) {
        throw new IllegalStateException("Per-version doesn't overwrite method");
    }

    public native int x();
    public native int z();
    public native long pack();

    public native static MCChunkPos unpack(long packedPos);
    public native static long pack(int x, int z);
    public native static int getX(long chunkAsLong);
    public native static int getZ(long chunkAsLong);
}
""",
    encoding="utf-8",
)

# Apply API substitutions throughout Core rather than relying on direct record
# field access, which is private in Minecraft 26.2 bytecode. These substitutions
# deliberately match fields only when no accessor parentheses are already present.
for path in (root / "src").rglob("*.java"):
    source = path.read_text(encoding="utf-8")
    source = source.replace("MCChunkPos.asLong(", "MCChunkPos.pack(")
    source = source.replace("MCChunkPos#toLong", "MCChunkPos#pack")
    source = source.replace("columnPos.x()()", "columnPos.x()")
    source = source.replace("columnPos.z()()", "columnPos.z()")
    source = source.replace("position.x()()", "position.x()")
    source = source.replace("position.z()()", "position.z()")
    source = re.sub(r"\bcolumnPos\.x\b(?!\s*\()", "columnPos.x()", source)
    source = re.sub(r"\bcolumnPos\.z\b(?!\s*\()", "columnPos.z()", source)
    source = re.sub(r"\bposition\.x\b(?!\s*\()", "position.x()", source)
    source = re.sub(r"\bposition\.z\b(?!\s*\()", "position.z()", source)
    source = source.replace("new MCChunkPos(chunkLong)", "MCChunkPos.unpack(chunkLong)")
    source = source.replace("import static org.hamcrest.junit.MatcherAssert.assertThat;", "import static org.hamcrest.MatcherAssert.assertThat;")
    path.write_text(source, encoding="utf-8")

# Preserve the instance packing paths introduced by the earlier migration while
# also accepting the exact 26.2 static pack API.
cube_pos = root / "src/main/java/io/github/opencubicchunks/cc_core/api/CubePos.java"
text = cube_pos.read_text(encoding="utf-8")
text = text.replace(
    "return new MCChunkPos(Coords.cubeToSection(CubePos.extractX(cubePosIn), localX), Coords.cubeToSection(CubePos.extractZ(cubePosIn), localZ)).pack();",
    "return MCChunkPos.pack(Coords.cubeToSection(CubePos.extractX(cubePosIn), localX), Coords.cubeToSection(CubePos.extractZ(cubePosIn), localZ));",
)
cube_pos.write_text(text, encoding="utf-8")

clo_pos = root / "src/main/java/io/github/opencubicchunks/cc_core/world/level/CloPos.java"
text = clo_pos.read_text(encoding="utf-8")
text = text.replace("return new MCChunkPos(x, z).pack();", "return MCChunkPos.pack(x, z);")
text = text.replace("return new MCChunkPos(x, MCChunkPos.getZ(packed)).pack();", "return MCChunkPos.pack(x, MCChunkPos.getZ(packed));")
text = text.replace("return new MCChunkPos(MCChunkPos.getX(packed), z).pack();", "return MCChunkPos.pack(MCChunkPos.getX(packed), z);")
clo_pos.write_text(text, encoding="utf-8")

# Netty 4.2 can no longer expose its Unsafe allocator reliably on Java 25.
# Keep the original bucket/bitset design, but store the open-addressed table in
# ordinary primitive arrays. This remains allocation-efficient, avoids boxed
# coordinate objects, preserves exact int coordinates and no longer risks JVM
# crashes or inaccessible native memory.
int3_hash_set = root / "src/main/java/io/github/opencubicchunks/cc_core/utils/Int3HashSet.java"
int3_hash_set.write_text(
    """package io.github.opencubicchunks.cc_core.utils;

import java.util.Arrays;

/**
 * A compact, open-addressed hash set for 3-dimensional integer positions.
 *
 * <p>Positions are grouped into 4x4x4 buckets. Every occupied hash-table slot
 * stores one bucket coordinate and a 64-bit occupancy mask. This is the same
 * representation used by the original implementation, but the table is held
 * in primitive Java arrays so it is safe on Java 25 and does not depend on
 * Netty's inaccessible Unsafe allocator.</p>
 *
 * <p>Not thread-safe.</p>
 */
public class Int3HashSet implements AutoCloseable {
    protected static final int DEFAULT_TABLE_SIZE = 16;
    protected static final int BUCKET_AXIS_BITS = 2;
    protected static final int BUCKET_AXIS_MASK = (1 << BUCKET_AXIS_BITS) - 1;
    private static final int MAX_TABLE_SIZE = 1 << 30;

    private int[] bucketX;
    private int[] bucketY;
    private int[] bucketZ;
    private long[] bucketValues;
    private int mask;
    private int resizeThreshold;
    private int usedBuckets;
    private long size;
    private boolean closed;

    public Int3HashSet() {
        this(DEFAULT_TABLE_SIZE);
    }

    public Int3HashSet(int initialCapacity) {
        if (initialCapacity < 0) {
            throw new IllegalArgumentException("initialCapacity must be non-negative");
        }
        long requiredBuckets = Math.max(DEFAULT_TABLE_SIZE, (long) Math.ceil(initialCapacity / 0.75d));
        int tableSize = DEFAULT_TABLE_SIZE;
        while (tableSize < requiredBuckets && tableSize < MAX_TABLE_SIZE) {
            tableSize <<= 1;
        }
        if (tableSize < requiredBuckets) {
            throw new IllegalArgumentException("initialCapacity is too large: " + initialCapacity);
        }
        allocate(tableSize);
    }

    protected static long hashPosition(int x, int y, int z) {
        long hash = x * 1403638657883916319L
                + y * 4408464607732138253L
                + z * 2587306874955016303L;
        hash ^= hash >>> 33;
        hash *= 0xff51afd7ed558ccdL;
        hash ^= hash >>> 33;
        return hash;
    }

    protected static long positionFlag(int x, int y, int z) {
        int bit = ((x & BUCKET_AXIS_MASK) << (BUCKET_AXIS_BITS * 2))
                | ((y & BUCKET_AXIS_MASK) << BUCKET_AXIS_BITS)
                | (z & BUCKET_AXIS_MASK);
        return 1L << bit;
    }

    public boolean add(int x, int y, int z) {
        ensureOpen();
        int bucket = findBucket(x >> BUCKET_AXIS_BITS, y >> BUCKET_AXIS_BITS, z >> BUCKET_AXIS_BITS, true);
        long flag = positionFlag(x, y, z);
        long value = this.bucketValues[bucket];
        if ((value & flag) != 0L) {
            return false;
        }
        this.bucketValues[bucket] = value | flag;
        this.size++;
        return true;
    }

    public boolean contains(int x, int y, int z) {
        ensureOpen();
        int bucket = findBucket(x >> BUCKET_AXIS_BITS, y >> BUCKET_AXIS_BITS, z >> BUCKET_AXIS_BITS, false);
        return bucket >= 0 && (this.bucketValues[bucket] & positionFlag(x, y, z)) != 0L;
    }

    public boolean remove(int x, int y, int z) {
        ensureOpen();
        int bucketX = x >> BUCKET_AXIS_BITS;
        int bucketY = y >> BUCKET_AXIS_BITS;
        int bucketZ = z >> BUCKET_AXIS_BITS;
        int bucket = findBucket(bucketX, bucketY, bucketZ, false);
        if (bucket < 0) {
            return false;
        }

        long flag = positionFlag(x, y, z);
        long value = this.bucketValues[bucket];
        if ((value & flag) == 0L) {
            return false;
        }

        this.size--;
        long remaining = value & ~flag;
        if (remaining != 0L) {
            this.bucketValues[bucket] = remaining;
        } else {
            this.usedBuckets--;
            shiftBuckets(bucket);
        }
        return true;
    }

    public void forEach(XYZConsumer action) {
        ensureOpen();
        if (action == null) {
            throw new NullPointerException("action");
        }
        for (int bucket = 0; bucket < this.bucketValues.length; bucket++) {
            long value = this.bucketValues[bucket];
            while (value != 0L) {
                int bit = Long.numberOfTrailingZeros(value);
                value &= value - 1L;
                int dx = bit >> (BUCKET_AXIS_BITS * 2);
                int dy = (bit >> BUCKET_AXIS_BITS) & BUCKET_AXIS_MASK;
                int dz = bit & BUCKET_AXIS_MASK;
                action.accept(
                        (this.bucketX[bucket] << BUCKET_AXIS_BITS) + dx,
                        (this.bucketY[bucket] << BUCKET_AXIS_BITS) + dy,
                        (this.bucketZ[bucket] << BUCKET_AXIS_BITS) + dz
                );
            }
        }
    }

    public void clear() {
        ensureOpen();
        if (this.size == 0L) {
            return;
        }
        Arrays.fill(this.bucketValues, 0L);
        this.usedBuckets = 0;
        this.size = 0L;
    }

    public long size() {
        ensureOpen();
        return this.size;
    }

    public boolean isEmpty() {
        ensureOpen();
        return this.size == 0L;
    }

    private int findBucket(int x, int y, int z, boolean createIfAbsent) {
        int slot = (int) hashPosition(x, y, z) & this.mask;
        while (true) {
            long value = this.bucketValues[slot];
            if (value == 0L) {
                if (!createIfAbsent) {
                    return -1;
                }
                if (this.usedBuckets >= this.resizeThreshold) {
                    resize();
                    return findBucket(x, y, z, true);
                }
                this.bucketX[slot] = x;
                this.bucketY[slot] = y;
                this.bucketZ[slot] = z;
                this.usedBuckets++;
                return slot;
            }
            if (this.bucketX[slot] == x && this.bucketY[slot] == y && this.bucketZ[slot] == z) {
                return slot;
            }
            slot = (slot + 1) & this.mask;
        }
    }

    private void resize() {
        int oldSize = this.bucketValues.length;
        if (oldSize >= MAX_TABLE_SIZE) {
            throw new IllegalStateException("Int3HashSet exceeded maximum table size");
        }
        int[] oldX = this.bucketX;
        int[] oldY = this.bucketY;
        int[] oldZ = this.bucketZ;
        long[] oldValues = this.bucketValues;

        allocate(oldSize << 1);
        for (int oldSlot = 0; oldSlot < oldValues.length; oldSlot++) {
            long value = oldValues[oldSlot];
            if (value == 0L) {
                continue;
            }
            insertBucket(oldX[oldSlot], oldY[oldSlot], oldZ[oldSlot], value);
        }
    }

    private void insertBucket(int x, int y, int z, long value) {
        int slot = (int) hashPosition(x, y, z) & this.mask;
        while (this.bucketValues[slot] != 0L) {
            slot = (slot + 1) & this.mask;
        }
        this.bucketX[slot] = x;
        this.bucketY[slot] = y;
        this.bucketZ[slot] = z;
        this.bucketValues[slot] = value;
        this.usedBuckets++;
    }

    /** Back-shifts a linear-probing cluster after deleting one bucket. */
    private void shiftBuckets(int deletedSlot) {
        int last = deletedSlot;
        int slot = (last + 1) & this.mask;
        while (this.bucketValues[slot] != 0L) {
            int ideal = (int) hashPosition(this.bucketX[slot], this.bucketY[slot], this.bucketZ[slot]) & this.mask;
            boolean move = last <= slot
                    ? last >= ideal || ideal > slot
                    : last >= ideal && ideal > slot;
            if (move) {
                this.bucketX[last] = this.bucketX[slot];
                this.bucketY[last] = this.bucketY[slot];
                this.bucketZ[last] = this.bucketZ[slot];
                this.bucketValues[last] = this.bucketValues[slot];
                last = slot;
            }
            slot = (slot + 1) & this.mask;
        }
        this.bucketValues[last] = 0L;
        this.bucketX[last] = 0;
        this.bucketY[last] = 0;
        this.bucketZ[last] = 0;
    }

    private void allocate(int tableSize) {
        this.bucketX = new int[tableSize];
        this.bucketY = new int[tableSize];
        this.bucketZ = new int[tableSize];
        this.bucketValues = new long[tableSize];
        this.mask = tableSize - 1;
        this.resizeThreshold = tableSize - (tableSize >>> 2);
        this.usedBuckets = 0;
    }

    private void ensureOpen() {
        if (this.closed) {
            throw new IllegalStateException("Int3HashSet is closed");
        }
    }

    @Override public void close() {
        if (this.closed) {
            return;
        }
        this.closed = true;
        this.bucketX = null;
        this.bucketY = null;
        this.bucketZ = null;
        this.bucketValues = null;
        this.mask = 0;
        this.resizeThreshold = 0;
        this.usedBuckets = 0;
        this.size = 0L;
    }

    @FunctionalInterface
    public interface XYZConsumer {
        void accept(int x, int y, int z);
    }
}
""",
    encoding="utf-8",
)

# Keep test expectations on the public 26.2 API.
for path in (root / "src/test/java").rglob("*.java"):
    source = path.read_text(encoding="utf-8")
    source = source.replace("new MCChunkPos(x, z).pack()", "MCChunkPos.pack(x, z)")
    source = source.replace("new MCChunkPos(root.getScale(), root.getScaledY()).pack()", "MCChunkPos.pack(root.getScale(), root.getScaledY())")
    source = source.replace("new MCChunkPos(node.getScale(), node.getScaledY()).pack()", "MCChunkPos.pack(node.getScale(), node.getScaledY())")
    source = source.replace("new MCChunkPos(child.getScale(), child.getScaledY()).pack()", "MCChunkPos.pack(child.getScale(), child.getScaledY())")
    path.write_text(source, encoding="utf-8")

remaining = []
for path in (root / "src").rglob("*.java"):
    source = path.read_text(encoding="utf-8")
    forbidden = (
        "MCChunkPos.asLong",
        "MCChunkPos#toLong",
        "columnPos.x;",
        "columnPos.z;",
        "position.x)",
        "position.z)",
        "new MCChunkPos(chunkLong)",
        "org.hamcrest.junit.MatcherAssert",
        "x()()",
        "z()()",
        "PlatformDependent.allocateMemory",
        "PlatformDependent.freeMemory",
    )
    if any(marker in source for marker in forbidden):
        remaining.append(str(path))
if remaining:
    raise SystemExit("Unmigrated Minecraft 26.2/Core Java 25 calls remain: " + ", ".join(remaining))

print("Migrated CubicChunksCore to Minecraft 26.2 and a Java 25-safe Int3HashSet")
