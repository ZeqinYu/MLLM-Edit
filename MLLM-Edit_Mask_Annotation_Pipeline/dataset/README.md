# Dataset Structure

This directory contains the Natural and Text subsets used by the candidate-mask generation and review pipeline.

## Directory Layout

```text
dataset/
├── README.md
├── QwenImageEditPlus2511_natural/
│   ├── 0_real/
│   ├── 1_fakesample/
│   ├── align/
│   ├── mask/
│   └── prompt.csv
└── QwenImageEditPlus2511_text/
    ├── 0_real/
    ├── 1_fakesample/
    ├── align/
    ├── mask/
    └── prompt.csv
```

## Folder Description

- `0_real/`: original images.
- `1_fakesample/`: edited images.
- `align/`: aligned original images.
- `mask/`: candidate masks organized by threshold.
- `prompt.csv`: prompt and sample metadata used by the review interface.

Images in `0_real/` and `1_fakesample/` are paired by filename stem. File extensions may differ.
