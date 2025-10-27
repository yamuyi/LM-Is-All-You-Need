# 国产化离线部署适配篇：国产化环境开源框架适配

## 目录说明

本篇专注于 **纯国产化软硬件环境**（华为910B ARM架构处理器 + OpenEuler 操作系统）下，主流大模型开源框架的离线适配与部署实战。核心覆盖dify、ragflow、llamafactory、MinerU等框架的环境适配、依赖构建、功能验证及性能优化，解决国产化场景下框架部署的兼容性难题。

## 学习目标

1. 掌握910B+OpenEuler+ARM架构的国产化环境核心特性及部署约束
2. 能独立完成dify/ragflow等框架的离线依赖构建与环境配置
3. 实现框架与910B硬件的适配（算子兼容、算力调用、内存优化）
4. 完成框架端到端部署（含模型集成、服务启动、功能测试）
5. 定位并解决国产化环境下框架部署的典型问题（依赖冲突、硬件调用失败等）

## 核心内容

| 子目录/文件                | 说明                                                        |
| -------------------------- | ----------------------------------------------------------- |
| 01_Env_Overview            | 国产化环境总览（910B特性、OpenEuler配置、ARM架构适配要点）  |
| 02_Offline_Dep_Build       | 离线依赖构建通用方案（OpenEuler ARM依赖包下载、本地源搭建） |
| 03_Dify_Adaptation         | Dify框架适配实战（离线部署、910B算力适配、模型集成）        |
| 04_Ragflow_Adaptation      | Ragflow框架适配实战（向量数据库国产化适配、ARM编译优化）    |
| 05_Llamafactory_Adaptation | Llamafactory适配实战（910B训练/推理适配、LoRA微调兼容）     |
| 06_MinerU_Adaptation       | MinerU框架适配实战（离线安装、文档解析模块兼容、服务部署）  |
| 07_Common_Issues           | 典型问题解决方案（依赖冲突、算子不兼容、算力调用失败等）    |
| 08_Deployment_Template     | 部署模板库（各框架离线部署脚本、配置文件模板）              |

## 国产化环境核心适配要点

### 1. 基础环境前置配置（OpenEuler+910B）

- **系统优化**：关闭防火墙冗余服务、配置910B算力驱动（Ascend Driver）离线安装包
- **依赖源搭建**：基于OpenEuler官方离线源，补充Python第三方库ARM架构离线包（通过 `pip download`提前下载）
- **编译器配置**：安装ARM架构GCC编译器（`gcc-aarch64-linux-gnu`），解决框架编译兼容性问题

### 2. 重点框架适配核心方案

| 框架         | 核心适配难点                       | 关键解决方案                                                                                 |
| ------------ | ---------------------------------- | -------------------------------------------------------------------------------------------- |
| Dify         | 前端资源离线加载、后端算力调用适配 | 1. 提前下载前端静态资源并本地化；2. 替换算力调用接口为910B适配版；3. 离线安装Celery等依赖    |
| Ragflow      | 向量数据库ARM兼容、检索引擎编译    | 1. 选用国产化向量数据库（如Huawei Cloud VectorDB离线版）；2. 源码编译时指定ARM架构参数       |
| Llamafactory | 训练/推理算子兼容、混合精度适配    | 1. 集成MindSpore/PyTorch 910B适配版；2. 调整训练脚本启用ARM架构混合精度；3. 优化数据加载逻辑 |
| MinerU       | 文档解析模块依赖、服务进程调度     | 1. 替换离线不兼容的解析依赖库；2. 配置OpenEuler进程调度策略适配ARM架构                       |

### 3. 离线部署通用流程

1. **环境预制**：在联网环境下载所有依赖包（框架源码、系统依赖、Python库），制作离线部署包
2. **基础配置**：在910B服务器安装OpenEuler系统，部署Ascend驱动及深度学习框架（MindSpore/PyTorch）
3. **框架部署**：上传离线包，执行编译/安装脚本，修改配置文件适配910B硬件
4. **模型集成**：导入适配ARM架构的开源模型（如Qwen-7B-ARM版），配置框架模型路径
5. **验证优化**：启动服务并执行功能测试，通过昇腾AI Profiler优化性能

## 资源推荐

- **硬件/系统资源**：
  - 910B驱动：华为昇腾社区离线驱动包（Ascend Driver 23.0+）
  - 系统镜像：OpenEuler 22.03 LTS ARM架构离线镜像
- **框架适配资源**：
  - Dify：[Dify 国产化适配分支](https://github.com/langgenius/dify/tree/domestic-adapt)
  - Ragflow：[Ragflow ARM适配文档](https://github.com/infiniflow/ragflow/blob/main/docs/arm_adaptation.md)
  - Llamafactory：[Llamafactory 昇腾适配教程](https://github.com/hiyouga/LLaMA-Factory/blob/main/docs/ascend.md)
- **工具推荐**：
  - 离线依赖管理：yum-utils（制作系统离线源）、pip2pi（Python本地源）
  - 性能优化：昇腾AI Profiler（910B算力分析）、nmon（系统监控）
  - 问题排查：gdb-aarch64（ARM架构调试）、Ascend Debug Toolkit

## 学习建议

1. 先完成基础环境搭建（OpenEuler+910B驱动），通过 `npu-smi info`验证硬件识别成功
2. 从简单框架（如MinerU）入手实践，熟悉国产化环境部署流程后再攻坚复杂框架
3. 所有依赖优先选用离线包安装，避免源码编译（ARM架构编译耗时且易出兼容问题）
4. 部署后重点测试框架核心功能（如Dify的对话、Ragflow的检索），再进行性能优化
5. 建立问题台账，记录适配过程中的依赖版本、配置修改及报错解决方案
