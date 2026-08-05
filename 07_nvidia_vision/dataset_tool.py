"""Deterministic FC01 dataset manifest, split and evaluation utilities.

The utilities operate only on supplied files.  They do not create production
images, infer labels or claim model performance.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable


MANIFEST_COLUMNS = (
    "image_id", "uri", "sha256", "provenance", "split", "production_lot",
    "acquisition_session", "recipe_id", "bottle_sku", "annotation_uri",
    "annotation_sha256", "review_status", "synthetic_or_real", "camera_id",
    "lens_id", "lighting_id", "width_px", "height_px",
)
ALLOWED_SPLITS = {"", "train", "validation", "test", "challenge"}
ALLOWED_ORIGINS = {"real", "synthetic"}
ALLOWED_REVIEW = {"UNREVIEWED", "SINGLE_REVIEW", "DOUBLE_REVIEWED", "ADJUDICATED"}


class DatasetError(ValueError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != MANIFEST_COLUMNS:
            raise DatasetError("dataset manifest columns or order differ from the controlled schema")
        return list(reader)


def validate_manifest(path: Path, dataset_root: Path, *, require_reviewed: bool = False) -> dict:
    root = dataset_root.resolve()
    rows = load_manifest(path)
    errors: list[str] = []
    image_ids: set[str] = set()
    content_hashes: dict[str, str] = {}
    groups: dict[tuple[str, str], set[str]] = {}
    for number, row in enumerate(rows, start=2):
        prefix = f"row {number}"
        image_id = row["image_id"]
        if not image_id or image_id in image_ids:
            errors.append(f"{prefix}: image_id is empty or duplicated")
        image_ids.add(image_id)
        if row["split"] not in ALLOWED_SPLITS:
            errors.append(f"{prefix}: split is invalid")
        if row["synthetic_or_real"] not in ALLOWED_ORIGINS:
            errors.append(f"{prefix}: synthetic_or_real is invalid")
        if row["review_status"] not in ALLOWED_REVIEW:
            errors.append(f"{prefix}: review status is invalid")
        if require_reviewed and row["review_status"] not in {"DOUBLE_REVIEWED", "ADJUDICATED"}:
            errors.append(f"{prefix}: sample is not independently reviewed")
        if not row["production_lot"] or not row["acquisition_session"]:
            errors.append(f"{prefix}: leakage-control group is absent")
        group = (row["production_lot"], row["acquisition_session"])
        groups.setdefault(group, set()).add(row["split"])
        for uri_column, hash_column in (("uri", "sha256"), ("annotation_uri", "annotation_sha256")):
            target = (root / row[uri_column]).resolve()
            if root not in target.parents:
                errors.append(f"{prefix}: {uri_column} escapes dataset root")
                continue
            if not target.is_file():
                errors.append(f"{prefix}: {uri_column} is missing")
                continue
            observed = _sha256(target)
            if observed != row[hash_column].lower():
                errors.append(f"{prefix}: {hash_column} mismatch")
            if uri_column == "uri":
                other = content_hashes.setdefault(observed, image_id)
                if other != image_id:
                    errors.append(f"{prefix}: exact duplicate content also appears as {other}")
        try:
            if int(row["width_px"]) <= 0 or int(row["height_px"]) <= 0:
                raise ValueError
        except ValueError:
            errors.append(f"{prefix}: image dimensions are not positive integers")
    leakage = {group: sorted(splits) for group, splits in groups.items() if len(splits - {""}) > 1}
    if leakage:
        errors.append(f"production lot/session leakage across splits: {leakage}")
    return {
        "schema": "FC01.dataset-manifest.v2",
        "rows": len(rows),
        "groups": len(groups),
        "exact_duplicate_hashes": len(rows) - len(content_hashes),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
        "scope": "manifest integrity only; not model-performance evidence",
    }


def assign_grouped_splits(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Assign stable 70/15/15-ish splits by production lot/session group."""
    groups = sorted({(row["production_lot"], row["acquisition_session"]) for row in rows})
    assignments: dict[tuple[str, str], str] = {}
    for group in groups:
        bucket = int.from_bytes(hashlib.sha256("\x1f".join(group).encode()).digest()[:8], "big") % 100
        assignments[group] = "train" if bucket < 70 else "validation" if bucket < 85 else "test"
    result: list[dict[str, str]] = []
    for row in rows:
        copy = dict(row)
        copy["split"] = assignments[(row["production_lot"], row["acquisition_session"])]
        result.append(copy)
    return result


def write_manifest(path: Path, rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


@dataclass(frozen=True)
class BinaryMetrics:
    true_positive: int
    true_negative: int
    false_positive: int
    false_negative: int

    def as_dict(self) -> dict:
        total_positive = self.true_positive + self.false_negative
        total_negative = self.true_negative + self.false_positive
        precision_denominator = self.true_positive + self.false_positive
        return {
            "tp": self.true_positive,
            "tn": self.true_negative,
            "fp": self.false_positive,
            "fn": self.false_negative,
            "precision": self.true_positive / precision_denominator if precision_denominator else None,
            "recall": self.true_positive / total_positive if total_positive else None,
            "false_accept_rate": self.false_positive / total_negative if total_negative else None,
            "false_reject_rate": self.false_negative / total_positive if total_positive else None,
        }


def evaluate_binary(rows: Iterable[dict[str, str]], threshold: float) -> BinaryMetrics:
    if not 0.0 <= threshold <= 1.0:
        raise DatasetError("threshold must be within [0, 1]")
    tp = tn = fp = fn = 0
    for row in rows:
        truth = row["truth_pass"].strip().lower()
        if truth not in {"true", "false"}:
            raise DatasetError("truth_pass must be true or false")
        score = float(row["pass_score"])
        if not 0.0 <= score <= 1.0:
            raise DatasetError("pass_score must be within [0, 1]")
        predicted = score >= threshold
        actual = truth == "true"
        tp += predicted and actual
        tn += not predicted and not actual
        fp += predicted and not actual
        fn += not predicted and actual
    return BinaryMetrics(tp, tn, fp, fn)


def perceptual_hash(path: Path, hash_size: int = 8) -> int:
    """Return an average hash when Pillow is available.

    This is a candidate-generation framework, not proof of semantic duplication;
    every flagged pair still requires dataset-review disposition.
    """
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise DatasetError("near-duplicate scan requires the optional Pillow dependency") from exc
    if hash_size < 4 or hash_size > 32:
        raise DatasetError("perceptual hash size is outside the controlled range")
    with Image.open(path) as image:
        pixels = list(image.convert("L").resize((hash_size, hash_size)).getdata())
    mean = sum(pixels) / len(pixels)
    value = 0
    for pixel in pixels:
        value = (value << 1) | int(pixel >= mean)
    return value


def near_duplicate_pairs(paths: Iterable[Path], *, maximum_hamming_distance: int = 4) -> list[tuple[Path, Path, int]]:
    if maximum_hamming_distance < 0:
        raise DatasetError("Hamming-distance threshold cannot be negative")
    fingerprints = [(path, perceptual_hash(path)) for path in paths]
    pairs = []
    for index, (left_path, left_hash) in enumerate(fingerprints):
        for right_path, right_hash in fingerprints[index + 1:]:
            distance = (left_hash ^ right_hash).bit_count()
            if distance <= maximum_hamming_distance:
                pairs.append((left_path, right_path, distance))
    return pairs


def main() -> None:
    parser = argparse.ArgumentParser(description="FC01 controlled dataset utilities")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("manifest", type=Path)
    validate.add_argument("dataset_root", type=Path)
    validate.add_argument("--require-reviewed", action="store_true")
    split = sub.add_parser("split")
    split.add_argument("manifest", type=Path)
    split.add_argument("output", type=Path)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("predictions", type=Path)
    evaluate.add_argument("--threshold", type=float, required=True)
    args = parser.parse_args()
    if args.command == "validate":
        report = validate_manifest(args.manifest, args.dataset_root,
                                   require_reviewed=args.require_reviewed)
        print(json.dumps(report, indent=2, sort_keys=True))
        raise SystemExit(0 if report["status"] == "PASS" else 1)
    if args.command == "split":
        write_manifest(args.output, assign_grouped_splits(load_manifest(args.manifest)))
        return
    with args.predictions.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    print(json.dumps(evaluate_binary(rows, args.threshold).as_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
