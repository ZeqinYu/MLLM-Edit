# MLLM-Edit
Official implementation of MLLM-Edit from our NeurIPS 2026 paper “MLLM-Edit: Benchmarking Image Forgery Detection and Localization under MLLM-based Editing”. <br>
Zeqin Yu, Ye Tian, Jian Zhang, Jiangqun Ni, Lanyun Zhu, Alex Kot, Xudong Jiang  

## Dataset

- **MLLM-Edit-v1:** Evaluation benchmark covering 18 MLLM-based editors.
- **MLLM-Edit-v2:** Training dataset covering five open-source editors.

[![Hugging Face](https://img.shields.io/badge/🤗%20Hugging%20Face-Dataset-FFD21E)](https://huggingface.co/datasets/Zegkim/MLLM-Edit)

## Code

- **[Mask Annotation Pipeline](./MLLM-Edit_Mask_Annotation_Pipeline):** Semi-automatic tampering mask annotation with geometric alignment, multi-threshold refinement, and human verification.

## Citation

If you find MLLM-Edit useful for your research, please consider citing our paper:

```bibtex
@inproceedings{yu2026mllmedit,
  title={MLLM-Edit: Benchmarking Image Forgery Detection and Localization under MLLM-based Editing},
  author={Yu, Zeqin and Tian, Ye and Zhang, Jian and Ni, Jiangqun and Zhu, Lanyun and Kot, Alex and Jiang, Xudong},
  booktitle={Advances in Neural Information Processing Systems},
  year={2026}
}
```
