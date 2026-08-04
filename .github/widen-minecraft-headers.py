#!/usr/bin/env python3
"""Create a compile-only Minecraft jar with CubicChunks' access widener applied.

Minecraft 26.2 is distributed in its public namespace, but Loom's merged compile
artifact is currently resources-only in this project. The build therefore uses
Mojang's raw client jar for javac. Loom still applies cubicchunks.accesswidener
for runtime/remap output; this script mirrors only the `accessible` changes onto
the raw compile header jar so javac sees the same visibility.
"""

from __future__ import annotations

import argparse
import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path

ACC_PUBLIC = 0x0001
ACC_PRIVATE = 0x0002
ACC_PROTECTED = 0x0004


@dataclass(frozen=True)
class MemberTarget:
    owner: str
    name: str
    descriptor: str


def read_u1(data: bytearray, offset: int) -> tuple[int, int]:
    return data[offset], offset + 1


def read_u2(data: bytearray, offset: int) -> tuple[int, int]:
    return struct.unpack_from(">H", data, offset)[0], offset + 2


def read_u4(data: bytearray, offset: int) -> tuple[int, int]:
    return struct.unpack_from(">I", data, offset)[0], offset + 4


def write_u2(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into(">H", data, offset, value)


def make_public(flags: int) -> int:
    return (flags & ~(ACC_PRIVATE | ACC_PROTECTED)) | ACC_PUBLIC


def parse_access_widener(path: Path) -> tuple[set[str], set[MemberTarget], set[MemberTarget]]:
    classes: set[str] = set()
    methods: set[MemberTarget] = set()
    fields: set[MemberTarget] = set()

    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("accessWidener"):
            continue
        parts = line.split()
        if parts[0] != "accessible":
            continue
        if len(parts) == 3 and parts[1] == "class":
            classes.add(parts[2])
        elif len(parts) == 5 and parts[1] in {"method", "field"}:
            target = MemberTarget(parts[2], parts[3], parts[4])
            (methods if parts[1] == "method" else fields).add(target)
        else:
            raise SystemExit(f"Unsupported access widener line {line_number}: {raw}")
    return classes, methods, fields


def parse_constant_pool(data: bytearray) -> tuple[int, dict[int, str], dict[int, int]]:
    if data[:4] != b"\xca\xfe\xba\xbe":
        raise ValueError("Not a class file")
    cp_count = struct.unpack_from(">H", data, 8)[0]
    offset = 10
    utf8: dict[int, str] = {}
    class_name_indices: dict[int, int] = {}
    index = 1
    while index < cp_count:
        tag, offset = read_u1(data, offset)
        if tag == 1:
            length, offset = read_u2(data, offset)
            utf8[index] = bytes(data[offset:offset + length]).decode("utf-8", errors="replace")
            offset += length
        elif tag in {3, 4}:
            offset += 4
        elif tag in {5, 6}:
            offset += 8
            index += 1
        elif tag in {7, 8, 16, 19, 20}:
            value, offset = read_u2(data, offset)
            if tag == 7:
                class_name_indices[index] = value
        elif tag in {9, 10, 11, 12, 17, 18}:
            offset += 4
        elif tag == 15:
            offset += 3
        else:
            raise ValueError(f"Unsupported constant-pool tag {tag}")
        index += 1
    return offset, utf8, class_name_indices


def skip_attributes(data: bytearray, offset: int) -> int:
    count, offset = read_u2(data, offset)
    for _ in range(count):
        _, offset = read_u2(data, offset)
        length, offset = read_u4(data, offset)
        offset += length
    return offset


def patch_members(
    data: bytearray,
    offset: int,
    count: int,
    owner: str,
    utf8: dict[int, str],
    targets: set[MemberTarget],
    found: set[MemberTarget],
) -> int:
    for _ in range(count):
        access_offset = offset
        flags, offset = read_u2(data, offset)
        name_index, offset = read_u2(data, offset)
        descriptor_index, offset = read_u2(data, offset)
        target = MemberTarget(owner, utf8[name_index], utf8[descriptor_index])
        if target in targets:
            write_u2(data, access_offset, make_public(flags))
            found.add(target)
        offset = skip_attributes(data, offset)
    return offset


def is_invalidated_signature_metadata(filename: str) -> bool:
    """Remove all signing metadata invalidated when class bytes are rewritten."""
    upper = filename.upper()
    if not upper.startswith("META-INF/"):
        return False
    leaf = upper.rsplit("/", 1)[-1]
    return leaf == "MANIFEST.MF" or leaf.endswith((".SF", ".RSA", ".DSA", ".EC")) or leaf.startswith("SIG-")


def patch_class(
    raw: bytes,
    class_targets: set[str],
    method_targets: set[MemberTarget],
    field_targets: set[MemberTarget],
    found_classes: set[str],
    found_methods: set[MemberTarget],
    found_fields: set[MemberTarget],
) -> bytes:
    data = bytearray(raw)
    offset, utf8, class_name_indices = parse_constant_pool(data)

    class_access_offset = offset
    class_flags, offset = read_u2(data, offset)
    this_class_index, offset = read_u2(data, offset)
    _, offset = read_u2(data, offset)
    owner = utf8[class_name_indices[this_class_index]]
    if owner in class_targets:
        write_u2(data, class_access_offset, make_public(class_flags))
        found_classes.add(owner)

    interfaces_count, offset = read_u2(data, offset)
    offset += interfaces_count * 2

    fields_count, offset = read_u2(data, offset)
    offset = patch_members(data, offset, fields_count, owner, utf8, field_targets, found_fields)
    methods_count, offset = read_u2(data, offset)
    offset = patch_members(data, offset, methods_count, owner, utf8, method_targets, found_methods)

    attributes_count, offset = read_u2(data, offset)
    for _ in range(attributes_count):
        name_index, offset = read_u2(data, offset)
        length, offset = read_u4(data, offset)
        info_offset = offset
        if utf8[name_index] == "InnerClasses":
            number, cursor = read_u2(data, info_offset)
            for _ in range(number):
                inner_class_index, cursor = read_u2(data, cursor)
                cursor += 4
                flags_offset = cursor
                flags, cursor = read_u2(data, cursor)
                if inner_class_index != 0:
                    inner_name = utf8[class_name_indices[inner_class_index]]
                    if inner_name in class_targets:
                        write_u2(data, flags_offset, make_public(flags))
                        found_classes.add(inner_name)
        offset += length
    return bytes(data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--access-widener", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    classes, methods, fields = parse_access_widener(args.access_widener)
    found_classes: set[str] = set()
    found_methods: set[MemberTarget] = set()
    found_fields: set[MemberTarget] = set()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    stripped_signature_metadata = 0
    with zipfile.ZipFile(args.input, "r") as source, zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            if is_invalidated_signature_metadata(info.filename):
                stripped_signature_metadata += 1
                continue
            payload = source.read(info.filename)
            if info.filename.endswith(".class"):
                payload = patch_class(payload, classes, methods, fields, found_classes, found_methods, found_fields)
            copied = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            copied.compress_type = zipfile.ZIP_DEFLATED
            copied.external_attr = info.external_attr
            copied.comment = info.comment
            copied.extra = info.extra
            target.writestr(copied, payload)

    missing_classes = sorted(classes - found_classes)
    missing_methods = sorted(methods - found_methods, key=lambda item: (item.owner, item.name, item.descriptor))
    missing_fields = sorted(fields - found_fields, key=lambda item: (item.owner, item.name, item.descriptor))
    print(f"Widened {len(found_classes)} classes, {len(found_methods)} methods, and {len(found_fields)} fields")
    print(f"Removed {stripped_signature_metadata} invalidated JAR signing metadata files")
    if missing_classes:
        print("Access-widener classes absent from Minecraft 26.2 (source migration still required):")
        for value in missing_classes:
            print(f"  {value}")
    if missing_methods:
        print("Access-widener methods absent or changed in Minecraft 26.2:")
        for value in missing_methods:
            print(f"  {value.owner} {value.name} {value.descriptor}")
    if missing_fields:
        print("Access-widener fields absent or changed in Minecraft 26.2:")
        for value in missing_fields:
            print(f"  {value.owner} {value.name} {value.descriptor}")

    if not args.output.is_file() or args.output.stat().st_size < 30_000_000:
        raise SystemExit(f"Widened Minecraft jar is missing or unexpectedly small: {args.output}")


if __name__ == "__main__":
    main()
