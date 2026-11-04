#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Candidate Mask Generation for the Semi-Automatic Annotation Pipeline
====================================================================

This script generates aligned reference images and multi-threshold candidate
manipulation masks for the accompanying human-review interface.

For each sample, an original image in ``0_real/`` is paired with its edited
counterpart in ``1_fakesample/`` using the filename stem. File extensions may
differ; for example, ``sample.jpg`` and ``sample.png`` are treated as a matched
pair because both share the stem ``sample``.

Expected model directory:

    MODEL_DIR/
    ├── 0_real/
    ├── 1_fakesample/
    ├── align/              # created automatically if absent
    ├── mask/               # created automatically if absent
    └── indexven.html       # local human-review interface

Generated candidate masks are organized by threshold:

    mask/
    ├── 0/
    ├── 2/
    ├── 4/
    └── ...

The Natural and Text subsets use the same alignment and mask-generation
procedure but different threshold sets. Select the appropriate subset using
``DATA_TYPE`` in the configuration block below.

The generated outputs are candidate masks intended for subsequent human
inspection and selection through ``indexven.html``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import cv2
import numpy as np
from PIL import Image, ImageFile
from tqdm import tqdm


# ============================================================
# Threshold selection
# ============================================================

# Dataset subset. Valid values are "natural" and "text".
# This setting determines which threshold list is used.
DATA_TYPE = "text"

# Path to one complete model directory containing 0_real/ and
# 1_fakesample/. The align/ and mask/ directories are created
# automatically if they do not already exist.
MODEL_DIR = Path(
    "/home/reviewer/MLLM-Edit_Mask_Annotation_Pipeline/dataset/QwenImageEditPlus2511_{}".format(DATA_TYPE)
)

# Directory names relative to MODEL_DIR.
REAL_FOLDER_NAME = "0_real"
FAKE_FOLDER_NAME = "1_fakesample"
ALIGN_FOLDER_NAME = "align"
MASK_FOLDER_NAME = "mask"

# False: retain samples whose aligned image and all candidate masks
# already exist.
# True: regenerate the aligned image and all candidate masks.
OVERWRITE = False

# Maximum number of SIFT features used for image alignment.
MAX_FEATURES = 2000

# Retain connected components whose area is at least this fraction
# of the largest foreground component.
MIN_AREA_RATIO = 0.02

# Maximum fraction of the image that may be replaced when repairing
# dark borders introduced by homography warping.
MAX_BORDER_AREA_RATIO = 0.10

# Candidate thresholds for natural-image samples.
NATURAL_THRESHOLDS = [
    0, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35,
    40, 45, 50, 55, 60, 65, 80, 95, 110, 125,
]

# Candidate thresholds for text-image samples.
TEXT_THRESHOLDS = [
    0, 1, 2, 5, 10, 20, 30, 40, 50, 60, 70,
    80, 90, 100, 110, 120, 130, 140, 160, 180, 200,
]

SUPPORTED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp",
    ".bmp", ".tif", ".tiff",
}

ImageFile.LOAD_TRUNCATED_IMAGES = True


# ============================================================
# Threshold selection
# ============================================================

def get_thresholds() -> list[int]:
    data_type = DATA_TYPE.lower().strip()

    if data_type == "natural":
        return NATURAL_THRESHOLDS

    if data_type == "text":
        return TEXT_THRESHOLDS

    raise ValueError(
        'DATA_TYPE must be either "natural" or "text".'
    )


# ============================================================
# Image-pair discovery and matching
# ============================================================

def collect_images(directory: Path) -> dict[str, Path]:
    """
    Collect supported images and index them by filename stem.

    Example:
        0_real/sample.jpg
        1_fakesample/sample.png

    These two files are matched because both have stem "sample".
    """
    images: dict[str, Path] = {}

    if not directory.exists():
        raise FileNotFoundError(
            f"Directory not found: {directory}"
        )

    for path in sorted(directory.iterdir()):
        if (
            path.is_file()
            and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ):
            stem = path.stem

            if stem in images:
                raise ValueError(
                    f"Duplicate filename stem '{stem}' in {directory}: "
                    f"{images[stem].name} and {path.name}"
                )

            images[stem] = path

    return images


# ============================================================
# Original-to-edited image alignment
# ============================================================

def sift_homography(
    image_source: np.ndarray,
    image_target: np.ndarray,
    max_features: int = MAX_FEATURES,
) -> Optional[np.ndarray]:
    """
    Align the source image to the target image using SIFT and
    constrained homography estimation.
    """
    target_height, target_width = image_target.shape[:2]

    resized_source = cv2.resize(
        image_source,
        (target_width, target_height),
        interpolation=cv2.INTER_LANCZOS4,
    )

    gray_source = cv2.cvtColor(
        resized_source,
        cv2.COLOR_RGB2GRAY,
    )
    gray_target = cv2.cvtColor(
        image_target,
        cv2.COLOR_RGB2GRAY,
    )

    sift = cv2.SIFT_create(
        nfeatures=max_features
    )

    keypoints_source, descriptors_source = (
        sift.detectAndCompute(gray_source, None)
    )
    keypoints_target, descriptors_target = (
        sift.detectAndCompute(gray_target, None)
    )

    if (
        descriptors_source is None
        or descriptors_target is None
        or len(keypoints_source) < 4
        or len(keypoints_target) < 4
    ):
        return None

    matcher = cv2.FlannBasedMatcher(
        dict(algorithm=1, trees=5),
        dict(checks=50),
    )

    matches = matcher.knnMatch(
        descriptors_source,
        descriptors_target,
        k=2,
    )

    good_matches = []

    for pair in matches:
        if len(pair) < 2:
            continue

        first, second = pair

        if first.distance < 0.75 * second.distance:
            good_matches.append(first)

    if len(good_matches) < 6:
        return None

    source_points = np.float32([
        keypoints_source[match.queryIdx].pt
        for match in good_matches
    ])

    target_points = np.float32([
        keypoints_target[match.trainIdx].pt
        for match in good_matches
    ])

    homography, inliers = cv2.findHomography(
        source_points,
        target_points,
        cv2.RANSAC,
        ransacReprojThreshold=3.0,
    )

    if homography is None:
        return None

    translation_x = homography[0, 2]
    translation_y = homography[1, 2]

    max_shift = max(
        target_width,
        target_height,
    ) * 0.10

    scale_x = np.sqrt(
        homography[0, 0] ** 2
        + homography[1, 0] ** 2
    )

    scale_y = np.sqrt(
        homography[0, 1] ** 2
        + homography[1, 1] ** 2
    )

    if (
        abs(translation_x) > max_shift
        or abs(translation_y) > max_shift
        or not 0.8 < scale_x < 1.2
        or not 0.8 < scale_y < 1.2
    ):
        return None

    if inliers is not None:
        print(
            f"[SIFT] inliers="
            f"{int(inliers.sum())}/{len(good_matches)}"
        )

    return cv2.warpPerspective(
        resized_source,
        homography,
        (target_width, target_height),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )


def fix_border_artifacts(
    aligned: np.ndarray,
    resized_reference: np.ndarray,
    max_area_ratio: float = MAX_BORDER_AREA_RATIO,
) -> np.ndarray:
    """
    Replace small dark border regions introduced by warping
    with pixels from the resized original image.
    """
    height, width = aligned.shape[:2]

    gray = cv2.cvtColor(
        aligned,
        cv2.COLOR_RGB2GRAY,
    )

    _, dark_binary = cv2.threshold(
        gray,
        10,
        255,
        cv2.THRESH_BINARY_INV,
    )

    flood_input = dark_binary.copy()
    seed_points: list[tuple[int, int]] = []

    for x in range(width):
        if dark_binary[0, x]:
            seed_points.append((x, 0))

        if dark_binary[height - 1, x]:
            seed_points.append((x, height - 1))

    for y in range(height):
        if dark_binary[y, 0]:
            seed_points.append((0, y))

        if dark_binary[y, width - 1]:
            seed_points.append((width - 1, y))

    flood_mask = np.zeros(
        (height + 2, width + 2),
        dtype=np.uint8,
    )

    for seed_x, seed_y in seed_points:
        if flood_input[seed_y, seed_x] == 255:
            flood_mask[:] = 0

            cv2.floodFill(
                flood_input,
                flood_mask,
                (seed_x, seed_y),
                128,
            )

    border_region = (
        (flood_input == 128).astype(np.uint8)
        * 255
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (5, 5),
    )

    border_region = cv2.dilate(
        border_region,
        kernel,
        iterations=1,
    )

    area_ratio = (
        np.count_nonzero(border_region)
        / float(height * width)
    )

    if area_ratio > max_area_ratio:
        return aligned

    output = aligned.copy()

    mask_3c = np.repeat(
        border_region[:, :, None] > 0,
        3,
        axis=2,
    )

    output[mask_3c] = resized_reference[mask_3c]

    return output


def align_original_to_edited(
    original: np.ndarray,
    edited: np.ndarray,
) -> np.ndarray:
    """
    Resize the original image to the edited-image size and
    apply SIFT alignment when a reliable homography is found.
    """
    target_height, target_width = edited.shape[:2]

    resized_original = cv2.resize(
        original,
        (target_width, target_height),
        interpolation=cv2.INTER_LANCZOS4,
    )

    aligned = sift_homography(
        original,
        edited,
    )

    if aligned is None:
        return resized_original

    return fix_border_artifacts(
        aligned,
        resized_original,
    )


# ============================================================
# Difference-based candidate mask generation
# ============================================================

def build_mask(
    aligned: np.ndarray,
    edited: np.ndarray,
    threshold: int,
    min_area_ratio: float = MIN_AREA_RATIO,
) -> np.ndarray:
    gray_aligned = cv2.cvtColor(
        aligned,
        cv2.COLOR_RGB2GRAY,
    )

    gray_edited = cv2.cvtColor(
        edited,
        cv2.COLOR_RGB2GRAY,
    )

    difference = cv2.absdiff(
        gray_aligned,
        gray_edited,
    )

    enhanced = (
        difference.astype(np.float32) ** 2
        / 255.0
    ).astype(np.uint8)

    minimum = int(enhanced.min())
    maximum = int(enhanced.max())

    if maximum <= minimum:
        return np.zeros(
            aligned.shape[:2],
            dtype=np.uint8,
        )

    stretched = (
        (
            enhanced.astype(np.float32)
            - minimum
        )
        / (maximum - minimum)
        * 255.0
    ).astype(np.uint8)

    _, binary = cv2.threshold(
        stretched,
        threshold,
        255,
        cv2.THRESH_BINARY,
    )

    closing_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (5, 5),
    )

    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        closing_kernel,
    )

    number_of_labels, labels, statistics, _ = (
        cv2.connectedComponentsWithStats(
            binary,
            connectivity=8,
        )
    )

    if number_of_labels > 1:
        largest_area = statistics[
            1:,
            cv2.CC_STAT_AREA,
        ].max()

        cleaned = np.zeros_like(binary)

        for component_index in range(
            1,
            number_of_labels,
        ):
            component_area = statistics[
                component_index,
                cv2.CC_STAT_AREA,
            ]

            if (
                component_area
                >= largest_area * min_area_ratio
            ):
                cleaned[
                    labels == component_index
                ] = 255

        binary = cleaned

    dilation_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (9, 9),
    )

    return cv2.dilate(
        binary,
        dilation_kernel,
        iterations=1,
    )


# ============================================================
# Existing-output validation
# ============================================================

def outputs_are_complete(
    sample_name: str,
    aligned_path: Path,
    mask_root: Path,
    thresholds: Iterable[int],
) -> bool:
    if not aligned_path.exists():
        return False

    return all(
        (
            mask_root
            / str(threshold)
            / f"{sample_name}.png"
        ).exists()
        for threshold in thresholds
    )


# ============================================================
# Processing of one matched image pair
# ============================================================

def process_pair(
    real_path: Path,
    fake_path: Path,
    aligned_path: Path,
    mask_root: Path,
    thresholds: list[int],
) -> None:
    original = np.array(
        Image.open(real_path).convert("RGB")
    )

    edited = np.array(
        Image.open(fake_path).convert("RGB")
    )

    aligned = align_original_to_edited(
        original,
        edited,
    )

    Image.fromarray(aligned).save(
        aligned_path
    )

    for threshold in thresholds:
        threshold_directory = (
            mask_root / str(threshold)
        )

        threshold_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        mask = build_mask(
            aligned,
            edited,
            threshold,
        )

        mask_path = (
            threshold_directory
            / f"{fake_path.stem}.png"
        )

        Image.fromarray(mask).save(
            mask_path
        )


# ============================================================
# Dataset-level processing
# ============================================================

def main() -> None:
    thresholds = get_thresholds()

    real_directory = (
        MODEL_DIR / REAL_FOLDER_NAME
    )
    fake_directory = (
        MODEL_DIR / FAKE_FOLDER_NAME
    )
    aligned_directory = (
        MODEL_DIR / ALIGN_FOLDER_NAME
    )
    mask_root = (
        MODEL_DIR / MASK_FOLDER_NAME
    )

    aligned_directory.mkdir(
        parents=True,
        exist_ok=True,
    )
    mask_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    real_images = collect_images(
        real_directory
    )
    fake_images = collect_images(
        fake_directory
    )

    common_stems = sorted(
        set(real_images)
        & set(fake_images)
    )

    only_real = sorted(
        set(real_images)
        - set(fake_images)
    )
    only_fake = sorted(
        set(fake_images)
        - set(real_images)
    )

    if not common_stems:
        raise RuntimeError(
            "No matching image pairs were found between "
            f"{real_directory} and {fake_directory}. "
            "Files are matched by filename stem."
        )

    print(f"DATA_TYPE: {DATA_TYPE}")
    print(f"MODEL_DIR: {MODEL_DIR}")
    print(f"REAL images: {len(real_images)}")
    print(f"FAKE images: {len(fake_images)}")
    print(f"Matched pairs: {len(common_stems)}")
    print(f"Thresholds: {thresholds}")

    if only_real:
        print(
            f"[WARN] {len(only_real)} files exist only in "
            f"{REAL_FOLDER_NAME}."
        )

    if only_fake:
        print(
            f"[WARN] {len(only_fake)} files exist only in "
            f"{FAKE_FOLDER_NAME}."
        )

    success_count = 0
    skipped_count = 0
    failed_count = 0
    failed_samples: list[tuple[str, str]] = []

    for sample_name in tqdm(
        common_stems,
        desc="Generating masks",
        ncols=100,
    ):
        real_path = real_images[sample_name]
        fake_path = fake_images[sample_name]

        aligned_path = (
            aligned_directory
            / f"{sample_name}.png"
        )

        if (
            not OVERWRITE
            and outputs_are_complete(
                sample_name,
                aligned_path,
                mask_root,
                thresholds,
            )
        ):
            skipped_count += 1
            continue

        try:
            process_pair(
                real_path,
                fake_path,
                aligned_path,
                mask_root,
                thresholds,
            )

            success_count += 1

        except Exception as error:
            failed_count += 1
            failed_samples.append(
                (sample_name, str(error))
            )

            print(
                f"[ERROR] {sample_name}: {error}"
            )

    print("\n==============================")
    print(f"success: {success_count}")
    print(f"existing: {skipped_count}")
    print(f"failed: {failed_count}")
    print("==============================")

    if only_real:
        print("\nFiles only in 0_real:")
        for stem in only_real:
            print(stem)

    if only_fake:
        print("\nFiles only in 1_fakesample:")
        for stem in only_fake:
            print(stem)

    if failed_samples:
        print("\nFailed samples:")
        for sample_name, error_message in failed_samples:
            print(
                f"{sample_name}: {error_message}"
            )


if __name__ == "__main__":
    main()
