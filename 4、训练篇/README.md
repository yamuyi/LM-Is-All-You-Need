# 微调与训练篇：大模型微调与训练实战
![训练篇封面图（可选）](https://via.placeholder.com/800x400?text=LLM+Fine-tuning+%26+Training)

## 目录说明
本文件夹涵盖大模型微调（有监督微调/SFT、RLHF 等）及全量训练的核心技术与实践方案。

## 学习目标
1.  理解不同微调方法（SFT/RLHF/LoRA/QLoRA）的适用场景
2.  能独立完成开源模型的 LoRA 微调（如基于自定义数据微调 LLaMA 3）
3.  掌握微调过程中的超参数调优及训练监控技巧
4.  了解大模型全量训练的工程化要点

## 核心内容
| 子目录/文件         | 说明                                  |
|---------------------|---------------------------------------|
| 01_Fine-tuning_Methods | 主流微调技术原理（SFT/RLHF/LoRA 等）|
| 02_LLoRA_Fine-tuning | QLoRA 微调实战（含数据准备/代码实现）|
| 03_RLHF_Pipeline    | RLHF 全流程实践（奖励模型训练/强化学习）|
| 04_Hyperparameter_Tuning | 超参数调优（学习率/批次大小等）经验 |
| 05_Training_Monitor | 训练过程监控（损失曲线/性能指标）工具 |

## 资源推荐
- **框架**：PEFT（参数高效微调）、TRL（RLHF 框架）、LoRAX（高效 LoRA 部署）
- **教程**：[Hugging Face PEFT 官方教程](https://huggingface.co/docs/peft/index)、[QLoRA 论文实现](https://github.com/artidoro/qlora)
- **论文**：[LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)、[RLHF 原始论文](https://arxiv.org/abs/1909.08593)

---
*最后更新：2025-10-27*
