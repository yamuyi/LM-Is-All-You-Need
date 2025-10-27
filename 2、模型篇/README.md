# 模型篇：主流大模型解析与实践

## 目录说明

本篇聚焦主流大模型的架构解析、源码学习及实战调优，覆盖基座模型、开源模型及商用 API 调用。

## 学习目标

1. 掌握主流基座模型（GPT/LLaMA/ERNIE 等）的架构差异与核心创新
2. 能独立部署开源大模型（如 LLaMA 3）并完成基础调优
3. 熟练使用商用大模型 API（OpenAI/阿里云通义千问等）
4. 理解模型量化、蒸馏等工程优化技术的原理与应用

## 核心内容

| 子目录/文件           | 说明                                          |
| --------------------- | --------------------------------------------- |
| 01_Foundation_Models  | 主流基座模型（GPT/LLaMA/ERNIE/BLOOM）架构解析 |
| 02_Open_Source_Models | 开源模型部署实践（LLaMA 3/Qwen/Phi 等）       |
| 03_Commercial_APIs    | 商用大模型 API 调用教程（含鉴权/参数调优）    |
| 04_Model_Optimization | 模型量化（INT4/INT8）、蒸馏、剪枝实战         |
| 05_Source_Code_Study  | 核心源码片段解析（如 Transformer 层实现）     |

## 资源推荐

- **开源模型**：[LLaMA 3](https://ai.meta.com/resources/models-and-libraries/llama-downloads/)、[Qwen](https://github.com/QwenLM/Qwen)
- **API 文档**：[OpenAI API](https://platform.openai.com/docs)、[阿里云通义千问 API](https://help.aliyun.com/document_detail/2711464.html)
- **工具**：Transformers（Hugging Face）、LLaMA.cpp（轻量部署）、AutoGPTQ（量化工具）
- **论文**：[LLaMA 3 Technical Report](https://arxiv.org/abs/2407.21783)、[GPT-4 Technical Report](https://arxiv.org/abs/2303.08774)

## 学习建议

1. 先从开源小模型（如 Phi-3）入手实践，降低部署门槛
2. 对比不同模型的 API 调用差异，总结通用调用范式
3. 重点关注模型优化技术在实际场景的性能提升效果
