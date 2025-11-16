"""Compress large JSONL files to reduce repository size.

Purpose:
    Compress JSONL files exceeding 500KB using gzip compression.
    Preserves original files and creates .jsonl.gz compressed versions.

Args:
    input_file: Path to JSONL file to compress.
    --keep-original: Keep original file after compression (default: True).
    --compress-level: Gzip compression level 1-9 (default: 9).

Returns:
    Exit code 0 on success, 1 on error.

Example:
    python scripts/tools/compress_jsonl.py results_stage20.jsonl
    python scripts/tools/compress_jsonl.py results_with_labels.jsonl --keep-original=False
"""

from __future__ import annotations

import argparse
import gzip
from pathlib import Path
import sys


def compress_jsonl(
    input_file: Path,
    keep_original: bool = True,
    compress_level: int = 9,
) -> int:
    """Compress a JSONL file using gzip.

    Purpose:
        Compress JSONL file to reduce size while preserving readability.

    Args:
        input_file: Path to JSONL file.
        keep_original: Whether to keep original file after compression.
        compress_level: Gzip compression level (1-9, higher = smaller).

    Returns:
        Exit code 0 on success, 1 on error.
    """
    if not input_file.exists():
        print(f"Error: File {input_file} does not exist", file=sys.stderr)
        return 1

    original_size = input_file.stat().st_size
    output_file = Path(f"{input_file}.gz")

    try:
        # Read original file
        with input_file.open("rb") as f_in:
            data = f_in.read()

        # Compress and write
        with gzip.open(output_file, "wb", compresslevel=compress_level) as f_out:
            f_out.write(data)

        compressed_size = output_file.stat().st_size
        ratio = compressed_size / original_size * 100

        print(
            f"Compressed {input_file.name}: "
            f"{original_size:,} bytes -> {compressed_size:,} bytes ({ratio:.1f}%)"
        )

        if not keep_original:
            input_file.unlink()
            print(f"Removed original file: {input_file}")

        return 0
    except Exception as exc:
        print(f"Error compressing {input_file}: {exc}", file=sys.stderr)
        if output_file.exists():
            output_file.unlink()
        return 1


def main() -> int:
    """Entry point for compression script."""
    parser = argparse.ArgumentParser(
        description="Compress large JSONL files using gzip.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to JSONL file to compress.",
    )
    parser.add_argument(
        "--keep-original",
        action="store_true",
        default=True,
        help="Keep original file after compression (default: True).",
    )
    parser.add_argument(
        "--remove-original",
        action="store_true",
        help="Remove original file after compression.",
    )
    parser.add_argument(
        "--compress-level",
        type=int,
        default=9,
        choices=range(1, 10),
        metavar="1-9",
        help="Gzip compression level (default: 9).",
    )

    args = parser.parse_args()

    keep_original = args.keep_original and not args.remove_original

    return compress_jsonl(
        args.input_file,
        keep_original=keep_original,
        compress_level=args.compress_level,
    )


if __name__ == "__main__":
    sys.exit(main())

