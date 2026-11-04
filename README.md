# MLLM-Edit
[![Hugging Face](https://img.shields.io/badge/🤗%20Hugging%20Face-Dataset-FFD21E)](https://huggingface.co/datasets/Zegkim/MLLM-Edit) [![GitHub](https://img.shields.io/badge/GitHub-Code-181717?logo=github&logoColor=white)](https://github.com/ZeqinYu/MLLM-Edit) [![Paper](https://img.shields.io/badge/Paper-NeurIPS%202026-0078D4?logo=readthedocs&logoColor=white)]()  
Official implementation of MLLM-Edit from our NeurIPS 2026 paper “MLLM-Edit: Benchmarking Image Forgery Detection and Localization under MLLM-based Editing”. <br>
Zeqin Yu, Ye Tian, Jian Zhang, Jiangqun Ni, Lanyun Zhu, Alex Kot, Xudong Jiang  

## Overview

![MLLM-Edit Pipeline](./assets/pipeline.svg)

MLLM-Edit is a large-scale benchmark for image forgery detection and localization (IFDL) under MLLM-based editing, comprising over 240k tampered images from diverse natural and text image sources. It covers 18 MLLM-based editors (8 open-source and 10 closed-source) and three tampering types: insertion, removal, and replacement.

MLLM-Edit is constructed through three stages: real image–prompt preparation, tampered image generation, and semi-automatic tampering mask annotation.

## Dataset

MLLM-Edit consists of two complementary versions covering natural and text images. Each tampered image is paired with its corresponding original image and editing prompt. Pixel-level tampering masks are provided for samples with valid annotations.

| Version | Model Source | MLLM-based Editors | Images |
|---|---|---|---:|
| **MLLM-Edit-v1** | Open-source (8) | Qwen-IEPlus, OmniGen-v2, BAGEL, FLUX.2 [klein] Base 9B, Step1X-Edit v1.2, LongCat-Image, GLM-Image, JoyAI-Image-Edit | 20,026 |
| **MLLM-Edit-v1** | Closed-source (10) | HunyuanImage 3.0, Kling Image 3.0, Wan 2.6 Image, Vidu Q2, Seedream 4.5, Jimeng 4.6, GPT Image 2/1.5, Grok Imagine, Reve V1, Nano Banana Pro (Gemini 3 Pro) | 24,260 |
| **MLLM-Edit-v2** | Open-source (5) | Qwen-IEPlus, FLUX.2 [klein] Base 9B, Step1X-Edit v1.2, LongCat-Image, JoyAI-Image-Edit | 197,927 |


**Download:** 🤗 [Hugging Face Dataset](https://huggingface.co/datasets/Zegkim/MLLM-Edit)

## Code

- **[Mask Annotation Pipeline](./MLLM-Edit_Mask_Annotation_Pipeline):** Semi-automatic tampering mask annotation with geometric alignment, multi-threshold refinement, and human verification.

## ✍️ Citation

If you find MLLM-Edit useful for your research, please consider citing our paper:

```bibtex
@inproceedings{yu2026mllmedit,
  title={MLLM-Edit: Benchmarking Image Forgery Detection and Localization under MLLM-based Editing},
  author={Yu, Zeqin and Tian, Ye and Zhang, Jian and Ni, Jiangqun and Zhu, Lanyun and Kot, Alex and Jiang, Xudong},
  booktitle={Advances in Neural Information Processing Systems},
  year={2026}
}
```
