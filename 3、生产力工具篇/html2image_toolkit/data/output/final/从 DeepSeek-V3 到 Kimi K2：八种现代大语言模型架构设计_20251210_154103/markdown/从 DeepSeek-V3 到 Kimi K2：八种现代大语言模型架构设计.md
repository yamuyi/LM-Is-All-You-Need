# 从 DeepSeek-V3 到 Kimi K2：八种现代大语言模型架构设计

[toc]

## 一、前言

自原始 GPT 架构开发以来已经过去了七年。乍一看，从 2019 年的 GPT-2 回溯，再到 2024-2025 年的 DeepSeek-V3 和 Llama 4，人们可能会惊讶地发现这些模型在结构上仍然如此相似。

当然，位置嵌入已经从绝对位置嵌入发展到旋转位置嵌入（RoPE），多头注意力（Multi-Head Attention）大多被分组查询注意力（Grouped-Query Attention）所取代，更高效的 SwiGLU 也取代了像 GELU 这样的激活函数。但在这些细微改进之下，我们是否真正看到了突破性的变化，还是我们只是在对相同的架构基础进行打磨？

比较 LLM 以确定其表现良好（或不佳）的关键因素是出了名的具有挑战性：数据集、训练技术和超参数差异很大，且往往没有得到很好的记录。

然而，我认为，检查架构本身的结构变化仍然具有很大的价值，可以了解 2025 年 LLM 开发者们在做什么。（其中一部分如图 1 所示。）

![](images\a30aa27284a3b33dde95439231e3deea.jpg)

因此，在这篇文章中，我将专注于定义当今旗舰开放模型的架构发展，而不是讨论基准性能或训练算法。

## 二、DeepSeek V3/R1 篇

你可能已经不止一次听说过，DeepSeek R1[1] 在 2025 年 1 月发布时产生了巨大影响。DeepSeek R1 是基于 2024 年 12 月推出的 DeepSeek V3[2] 架构构建的推理模型。

虽然我在这里关注的是 2025 年发布的架构，但我认为将 DeepSeek V3 包含进来是合理的，因为它在 2025 年 DeepSeek R1 发布后才获得了广泛关注和采用。

在这一部分中，我将重点介绍 DeepSeek V3 中引入的两项关键架构技术，这些技术提高了其计算效率，并使其与其他许多 LLM 区别开来：

1. Multi-Head Latent Attention (MLA)
2. Mixture-of-Experts (MoE)

### 2.1 Multi-Head Latent Attention (MLA)

在讨论多头潜在注意力（MLA）之前，让我们先简要回顾一些背景，以说明为什么使用它。为此，我们先从分组查询注意力（GQA）开始，近年来，GQA 已经成为多头注意力（MHA）的更高效计算和参数替代方案。

#### 2.1.1 Multi-Head Attention (MHA)

MHA 中的每个头都有自己的键和值。

#### 2.1.2 Grouped-query Attention (GQA)

##### 2.1.2.1 Grouped-query Attention (GQA) 介绍

为了减少内存使用，GQA 将多个头分组以共享相同的键和值投影。

例如，如图 2 所示，如果有 2 个键值组和 4 个注意力头，那么头 1 和头 2 可能共享一组键和值，而头 3 和头 4 共享另一组。这减少了键和值计算的总数，从而降低了内存使用并提高了效率（根据消融研究，这并没有明显影响建模性能）。

![](images\816a05c86797fd4f1e6e049093e32247.jpg)

图 2：MHA 和 GQA 的比较。这里，组大小为 2，一个键值对在 2 个查询之间共享。

##### 2.1.2.2 Grouped-query Attention (GQA) 核心思想

因此， **GQA 的核心思想是通过在多个查询头之间共享键和值头来减少键和值头的数量** 。

##### 2.1.2.3 Grouped-query Attention (GQA) 优点

1. （1）降低了模型的参数数量
2. （2）减少了在推理期间键和值张量的内存带宽使用，因为需要存储和从 KV 缓存中检索的键和值更少。

##### 2.1.2.4 Grouped-query Attention (GQA) 缺点

1. 尽管 GQA 主要是 MHA 的计算效率解决方案，但消融研究（例如原始 GQA 论文[3]和 Llama 2 论文[4]中的研究）表明，它在 LLM 建模性能方面与标准 MHA 相当。

#### 2.1.3 Multi-Head Latent Attention (MLA)

现在， **多头潜在注意力（MLA）提供了一种不同的节省内存的策略，这种策略也特别适合与 KV 缓存搭配使用** 。与 GQA 不同，MLA 在将键和值张量存储到 KV 缓存之前，将其压缩到低维空间。

在推理时，这些压缩的张量会被投影回其原始大小，如图 3 所示。这增加了一次额外的矩阵乘法，但减少了内存使用。

![](images\3d66fa1a2837668e05e9015a66791208.jpg)

图 3：与常规 MHA 相比，MLA（用于 DeepSeek V3 和 R1）的比较。

> 顺便说一下，查询也在训练期间被压缩，但在推理期间不会。

顺便说一下，MLA 并不是 DeepSeek V3 的新发明，因为它的前身 DeepSeek-V2[5] 也使用了（甚至引入了）它。此外，V2 论文还包含了一些有趣的消融研究，这些研究可能解释了为什么 DeepSeek 团队选择了 MLA 而不是 GQA（见图 4）。

![](images\a11b0cc6899fbb7039c61a9980728cc9.jpg)

图 4：来自 DeepSeek-V2 论文的注释表格， [ https://arxiv.org/abs/2405.04434 ](https://arxiv.org/abs/2405.04434)

如图 4 所示，GQA 的表现似乎不如 MHA，而 MLA 在建模性能方面优于 MHA，这可能是 DeepSeek 团队选择 MLA 而不是 GQA 的原因。（如果能看到 MLA 和 GQA 之间的“每个标记的 KV 缓存”节省比较，那将很有趣！）

在我们继续下一个架构组件之前，总结一下这一部分， **MLA 是一种巧妙的技巧，可以在降低 KV 缓存内存使用的同时，甚至在建模性能方面略微优于 MHA** 。

### 2.2 Mixture-of-Experts (MoE)

**DeepSeek 值得强调的另一个主要架构组件是其使用了专家混合（MoE）层** 。虽然 DeepSeek 并没有发明 MoE，但今年它又重新流行起来，我们稍后将讨论的许多架构也采用了它。

你可能已经对 MoE 很熟悉了，但简要回顾一下可能有帮助。

#### 2.2.1 Mixture-of-Experts (MoE) 核心思想 是什么？

MoE 的核心思想是 **用多个专家层替换 Transformer 块中的每个 FeedForward 模块，其中每个专家层也是一个 FeedForward 模块** 。这意味着我们将一个 FeedForward 块替换为多个 FeedForward 块，如图 5 所示。

![](images\71dc8b4cebd9ac48641c872c1316fc9b.jpg)

图 5：DeepSeek V3/R1 中的专家混合（MoE）模块（右）与具有标准 FeedForward 块的 LLM（左）的比较。

Transformer 块中的 FeedForward 块（在上图中显示为深灰色块）通常包含模型总参数的大部分。（请注意，Transformer 块，因此 FeedForward 块，在 LLM 中会重复多次；在 DeepSeek-V3 的情况下，重复了 61 次。）

因此，用多个 FeedForward 块替换一个 FeedForward 块（如 MoE 设置中所做的那样）会显著增加模型的总参数数量。然而，关键的技巧是我们并不使用（“激活”）每个标记的所有专家。相反，路由器只为每个标记选择一小部分专家。（由于时间关系，或者更确切地说是为了节省文章篇幅，我将在以后详细介绍路由器。）

因为每次只激活少数专家，所以 MoE 模块通常被称为_稀疏_模块，与总是使用完整参数集的_密集_模块相对。然而，通过 MoE 的大量总参数增加了 LLM 的容量，这意味着它可以在训练期间吸收更多的知识。尽管如此，稀疏性保持了推理的高效性，因为我们并不是同时使用所有的参数。

例如，DeepSeek-V3 每个 MoE 模块有 256 个专家，总共有 6710 亿个参数。但在推理期间，每次只激活 9 个专家（1 个共享专家加上路由器选择的 8 个）。这意味着每次推理步骤只使用 370 亿个参数，而不是全部 6710 亿个。

DeepSeek-V3 的 MoE 设计的一个显著特点是使用了共享专家。这是一个始终为每个标记激活的专家。这个想法并不新鲜，早在 2024 年的DeepSeek MoE[6] 和 2022 年的 DeepSpeedMoE 论文[7]中就已经引入了。

![](images\b986aef33e1410a7ca54e346046c8156.jpg)

图 6：来自 “DeepSeekMoE：迈向专家混合语言模型的终极专家专业化” 的注释图， [ https://arxiv.org/abs/2401.06066 ](https://arxiv.org/abs/2401.06066)

#### 2.2.2 Mixture-of-Experts (MoE) 优点 是什么？

共享专家的好处 **最初在 DeepSpeedMoE 论文中被注意到，他们发现与没有共享专家相比，它提高了整体建模性能** 。这可能是因为常见的或重复的模式不需要被多个单独的专家学习，这为它们留下了更多空间来学习更专门的模式。

### 2.3 DeepSeek Summary

#### 2.3.1 为什么 6710B DeepSeek-V3 推理效率 优于 405B Llama 3?

总之，DeepSeek-V3 是一个拥有 6710 亿个参数的巨大模型，在发布时，它超过了其他开放权重模型，包括 405B Llama 3。尽管规模更大，但它在推理时间上效率更高，这 **得益于其专家混合（MoE）架构，该架构每次标记只激活一小部分（仅 37B）参数** 。

#### 2.3.2 DeepSeek-V3 和 Llama 3 有什么区别?

DeepSeek-V3 和 Llama 3 的 一个关键区别是 **DeepSeek-V3 使用了多头潜在注意力（MLA）而不是分组查询注意力（GQA）** 。MLA 和 GQA 都是标准多头注意力（MHA）的推理高效替代方案，特别是在使用 KV 缓存时。虽然 MLA 实现起来更复杂，但 DeepSeek-V2 论文中的一项研究表明，它在建模性能方面优于 GQA。

## 三、OLMo 2

非营利机构艾伦人工智能研究所的OLMo系列模型值得关注，因为它在训练数据和代码方面非常透明，并且技术报告也相对详细。

虽然你可能不会在任何基准测试或排行榜的顶部找到 OLMo 模型，但它们非常干净，更重要的是，由于它们的透明度，它们是开发 LLM 的绝佳蓝图。

尽管 OLMo 模型因其透明度而受欢迎，但它们的表现也不差。事实上，在 1 月份发布时（在 Llama 4、Gemma 3 和 Qwen 3 之前），OLMo 2[8] 模型位于计算与性能的帕累托前沿，如图 7 所示。

![](images\cbcc584ab65b74b5b2a5e06e2b567df6.jpg)

图 7：不同 LLM 的建模基准性能（越高越好）与预训练成本（FLOPs；越低越好）的比较。这是来自 OLMo 2 论文的注释图， [ https://arxiv.org/abs/2501.00656 ](https://arxiv.org/abs/2501.00656)

### 3.1 Normalization Layer Placement

总的来说，OLMo 2 在很大程度上遵循了原始 GPT 模型的架构，与其他当代 LLM 相似。然而，也有一些值得注意的偏差。让我们从归一化层开始。

与 Llama、Gemma 和大多数其他 LLM 类似，OLMo 2 从 LayerNorm 切换到 RMSNorm。

但既然 RMSNorm 已经司空见惯（它基本上是 LayerNorm 的简化版本，可训练参数更少），我将跳过 RMSNorm 与 LayerNorm 的讨论。

然而，讨论 RMSNorm 层的位置是值得的。

1. **Post-LN 或 Post-Norm** : 原始 Transformer（来自“Attention is all you need”论文）将两个归一化层放置在 Transformer 块中注意力模块和 FeedForward 模块之后。
2. **Pre-LN 或 Pre-Norm** ：GPT 和之后的大多数其他 LLM 将归一化层放置在注意力和 FeedForward 模块之前

Post-LN 和 Pre-Norm 的比较如下图所示。

![](images\aef605282595ca4628296157c26d8c6b.jpg)

图 8：Post-Norm、Pre-Norm 和 OLMo 2 的 Post-Norm 风格的比较。

2020 年，Xiong[9] 等人表明，Pre-LN 在初始化时产生更良好行为的梯度。此外，研究人员提到，Pre-LN 甚至在没有仔细的学习率预热的情况下也能很好地工作，而这对 Post-LN 来说是一个至关重要的工具。

现在，我提到这一点的原因是，OLMo 2 采用了 Post-LN 的一种形式（但使用 RMSNorm 而不是 LayerNorm，所以我称之为_Post-Norm_）。

在 OLMo 2 中，他们没有将归一化层放置在注意力和 FeedForward 层之前，而是将其放置在之后，如上图所示。然而，请注意，与原始 Transformer 架构相比，归一化层仍然在残差层（跳跃连接）内部。

那么，他们为什么移动了归一化层的位置呢？原因是这有助于训练稳定性，如下图所示。

![](images\bb6239463960a9667f67a875ae3037f9.jpg)

图 9：显示 Pre-Norm（如 GPT-2、Llama 3 和许多其他模型中）与 OLMo 2 的 Post-Norm 风格的训练稳定性图。

不幸的是，这张图显示了与 QK-Norm 重新排序的结果，这是一个单独的概念。因此，很难判断归一化层重新排序本身贡献了多少。

### 3.2 QK-Norm

由于上一节已经提到了 QK-norm，并且我们稍后讨论的其他 LLM（如 Gemma 2 和 Gemma 3）也使用了 QK-norm，让我们简要讨论一下这是什么。

QK-Norm 本质上是另一个 RMSNorm 层。它位于多头注意力（MHA）模块内部，并在应用 RoPE 之前应用于查询（q）和键（k）。为了说明这一点，以下是我为 Qwen3 从零开始实现[10]所写的 Grouped-Query Attention（GQA）层的一个片段（GQA 中 QK-norm 的应用与 OLMo 中的 MHA 类似）：

```
import torch
from torch import nn

class GroupQueryAttention(torch.nn.Module):
    def __init__(self, hidden_size, num_heads, group_num):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads
        self.group_num = group_num  # 组的数量
      
        # 初始化 Q、K、V 投影矩阵，注意这里的 K V 做了折衷
        self.q_linear = nn.Linear(hidden_size, hidden_size)  # (hidden_size, hidden_size)
        self.k_linear = nn.Linear(hidden_size, self.group_num * self.head_dim)  # (hidden_size, group_num * head_dim)
        self.v_linear = nn.Linear(hidden_size, self.group_num * self.head_dim)  # (hidden_size, group_num * head_dim)
      
        self.o_linear = nn.Linear(hidden_size, hidden_size)  # (hidden_size, hidden_size)
      
    def forward(self, hidden_state, causal_mask=None, padding_mask=None):
        batch_size = hidden_state.size(0)
      
        query = self.q_linear(hidden_state)  # (batch_size, seq_len, hidden_size)
        key = self.k_linear(hidden_state)    # (batch_size, seq_len, group_num * head_dim)
        value = self.v_linear(hidden_state)  # (batch_size, seq_len, group_num * head_dim)
      
        # 分割头部，将每个头的维度拆分出来
        query = self.split_head(query)  # (batch_size, num_heads, seq_len, head_dim)
        key = self.split_head(key, self.group_num)  # (batch_size, num_heads, seq_len, head_dim)
        value = self.split_head(value, self.group_num)  # (batch_size, num_heads, seq_len, head_dim)
      
        # 计算注意力分数，自动广播，(batch_size, num_heads, seq_len, seq_len)
        attention_scores = torch.matmul(query, key.transpose(-1, -2)) / torch.sqrt(torch.tensor(self.head_dim, dtype=torch.float32))
      
        if causal_mask is not None:
            attention_scores += causal_mask * -1e9  

        if padding_mask is not None:
            padding_mask = padding_mask.unsqueeze(1).unsqueeze(1)
            attention_scores += padding_mask * -1e9
      
        attention_probs = torch.softmax(attention_scores, dim=-1)  # (batch_size, num_heads, seq_len, seq_len)
      
        output = torch.matmul(attention_probs, value)  # (batch_size, num_heads, seq_len, head_dim)
      
        # 对注意力输出进行拼接，形状: (batch_size, seq_len, hidden_size)
        output = output.transpose(1, 2).view(batch_size, -1, self.head_dim * self.num_heads)
      
        # 通过线性层将拼接后的输出变换为所需的输出维度
        output = self.o_linear(output)  # (batch_size, seq_len, hidden_size)
      
        return output

    def split_head(self, x, group_num=None):
        batch_size, seq_len = x.size()[:2]  # 获取批量大小和序列长度
      
        if group_num is None:
            return x.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        else:
            # 将 hidden_size 分割为 group_num 和 head_dim
            x = x.view(batch_size, -1, group_num, self.head_dim).transpose(1, 2)
            # 再将其手动 expand 到相同大小
            x = x[:, :, None, :, :].expand(batch_size, group_num, self.num_heads // group_num, seq_len, self.head_dim).view(batch_size, self.num_heads, seq_len, self.head_dim)
```

如前所述，QK-Norm 与 Post-Norm 一起稳定了训练。请注意，QK-Norm 并非由 OLMo 2 发明，而是可以追溯到 2023 年的 Scaling Vision Transformers 论文[11]。

### 3.3 OLMo 2 Summary

简而言之，值得注意的 OLMo 2 架构设计决策主要是 RMSNorm 的位置：在注意力和 FeedForward 模块之后而不是之前（Post-Norm 的一种风格），以及在注意力机制中为查询和键添加 RMSNorm（QK-Norm），这两者共同帮助稳定了训练损失。

下图进一步比较了 OLMo 2 与 Llama 3；可以看出，除了 OLMo 2 仍然使用传统的 MHA 而不是 GQA 之外，架构在其他方面相对相似。（然而，OLMo 2 团队在 3 个月后发布了一个使用 GQA 的 32B 变体[12]。）

![](images\fefcb95d1221f6516da78b5267ac27c6.jpg)

图 10：Llama 3 和 OLMo 2 的架构比较。

## 四、Gemma 3

### 4.1 介绍 Gemma 3

谷歌的 Gemma 模型一直都很出色，我认为与其他流行模型（如 Llama 系列）相比，它们总是被低估了。

**Gemma 的一个显著特点是其相当大的词汇量（为了更好地支持多种语言），以及对 27B 尺寸的更强关注（而不是 8B 或 70B）。但请注意，Gemma 2 也有更小的尺寸：1B、4B 和 12B** 。

27B 的尺寸确实是一个非常好的平衡点：它比 8B 模型强大得多，但不像 70B 模型那样资源密集，而且在我的 Mac Mini 上运行得很好。

### 4.2 Gemma 3 还有什么有趣的地方呢？

如前所述，像 Deepseek-V3/R1 这样的其他模型使用专家混合（MoE）架构来减少推理时的内存需求，给定固定的模型大小。（MoE 方法也用于我们稍后讨论的其他几个模型。）

Gemma 3 使用了一种不同的“技巧”来降低计算成本，即滑动窗口注意力。

### 4.3 Sliding Window Attention

#### 4.3.1 什么是滑动窗口注意力呢？

通过滑动窗口注意力（最初在 2020 年的 LongFormer 论文[14]中引入，并且也被 Gemma 2[15] 使用），Gemma 3 团队能够大幅减少 KV 缓存中的内存需求，如下图所示。

![](images\627b0173b2b4820d4d456eff01e1bd7e.jpg)

图 11：来自 Gemma 3 论文（ [ https://arxiv.org/abs/2503.19786）的注释图，显示了通过滑动窗口注意力实现的 ](https://arxiv.org/abs/2503.19786%EF%BC%89%E7%9A%84%E6%B3%A8%E9%87%8A%E5%9B%BE%EF%BC%8C%E6%98%BE%E7%A4%BA%E4%BA%86%E9%80%9A%E8%BF%87%E6%BB%91%E5%8A%A8%E7%AA%97%E5%8F%A3%E6%B3%A8%E6%84%8F%E5%8A%9B%E5%AE%9E%E7%8E%B0%E7%9A%84) KV 缓存内存节省。

**如果我们把常规自注意力看作是一种_全局_注意力机制，因为每个序列元素都可以访问其他所有序列元素，那么我们可以把滑动窗口注意力看作是一种_局部_注意力，因为这里我们限制了当前查询位置周围的上下文大小** 。如下图所示。

![](images\fd9cab0aceaba5c413aad9249f90dae2.jpg)

图 12：常规注意力（左）和滑动窗口注意力（右）的比较。

请注意，滑动窗口注意力可以与多头注意力和分组查询注意力一起使用；Gemma 3 使用分组查询注意力。

如上所述，滑动窗口注意力也被称为_局部_注意力，因为局部窗口围绕并随当前查询位置移动。相比之下，常规注意力是_全局_的，因为每个标记都可以访问所有其他标记。

现在，如前所述，Gemma 2 的前身架构也使用了滑动窗口注意力。Gemma 3 的不同之处在于它们调整了全局（常规）和局部（滑动）注意力之间的比例。

> 举个栗子，Gemma 2 使用混合注意力机制，以 1:1 的比例结合了滑动窗口（局部）和全局注意力。每个标记可以参与附近上下文的 4k 标记窗口。

Gemma 2 在其他层中使用滑动窗口注意力，而 Gemma 3 现在有 5:1 的比例，这意味着每 5 个滑动窗口（局部）注意力层中只有 1 个完整注意力层；此外，滑动窗口大小从 4096（Gemma 2）减少到仅 1024（Gemma 3）。这将模型的重点转移到更高效的局部计算上。

根据他们的消融研究，滑动窗口注意力的使用对建模性能的影响很小，如下图所示。

![](images\094a5547a3c5cdde5f9acb451eb8f7ca.jpg)

图 13：来自 Gemma 3 论文（ [ https://arxiv.org/abs/2503.19786）的注释图，显示滑动窗口注意力对 ](https://arxiv.org/abs/2503.19786%EF%BC%89%E7%9A%84%E6%B3%A8%E9%87%8A%E5%9B%BE%EF%BC%8C%E6%98%BE%E7%A4%BA%E6%BB%91%E5%8A%A8%E7%AA%97%E5%8F%A3%E6%B3%A8%E6%84%8F%E5%8A%9B%E5%AF%B9) LLM 生成的输出困惑度的影响很小或没有影响。

虽然滑动窗口注意力是 Gemma 3 最值得注意的架构方面，但我也想简要回顾一下归一化层的位置，作为前一节 OLMo 2 的后续。

#### 4.3.2 Normalization Layer Placement in Gemma 3

一个虽小但有趣的细节是，Gemma 3 在 Pre-Norm 和 Post-Norm 设置中都使用了 RMSNorm，围绕其分组查询注意力模块。

这与 Gemma 2 类似，但仍然值得强调，因为它不同于（1）原始 Transformer（“Attention is all you need”）中使用的 Post-Norm，（2）由 GPT-2 推广的 Pre-Norm，之后在许多其他架构中使用，以及（3）我们之前看到的 OLMo 2 的 Post-Norm 风格。

![](images\83f25c22344bde1a0141e298aac00e0b.jpg)

图 14：OLMo2 和 Gemma 3 的架构比较；请注意 Gemma 3 中的额外归一化层。

我认为这种归一化层的位置是一种相对直观的方法，因为它结合了 Pre-Norm 和 Post-Norm 的优点。在我看来，多做一些归一化并没有坏处。在最坏的情况下，如果额外的归一化是多余的，这会带来一点冗余的低效。实际上，由于 RMSNorm 在整体方案中相对便宜，这不应该有任何明显的影响。

#### 4.3.3 Gemma 3 Summary

Gemma 3 是一个表现良好的开放权重 LLM，在我看来，它在开源圈子中有点被低估了。最有趣的部分是使用滑动窗口注意力来提高效率（未来将其与 MoE 结合将很有趣）。

此外，Gemma 3 还具有独特的归一化层位置，在注意力和 FeedForward 模块之前和之后都放置了 RMSNorm 层。

#### 4.3.4 Bonus: Gemma 3n

在 Gemma 3 发布几个月后，谷歌分享了 Gemma 3n[16]，这是一个针对小型设备效率优化的 Gemma 3 模型，目标是在手机上运行。

Gemma 3n 为实现更好的效率所做的更改之一是所谓的每层嵌入（PLE）参数层。关键思想是只将模型参数的一个子集保留在 GPU 内存中。然后，根据需要从 CPU 或 SSD 流式传输特定于标记层的嵌入，例如文本、音频和视觉模态的嵌入。

下图说明了 PLE 的内存节省，列出了标准 Gemma 3 模型的 54.4 亿个参数。这可能指的是 Gemma 3 的 40 亿变体。

![](images\e5d103278672b270b6c4b88d480ef8f6.jpg)

图 15：来自 Google 的 Gemma 3n 博客（ [ https://developers.googleblog.com/en/introducing-gemma-3n/）的注释图，说明了 ](https://developers.googleblog.com/en/introducing-gemma-3n/%EF%BC%89%E7%9A%84%E6%B3%A8%E9%87%8A%E5%9B%BE%EF%BC%8C%E8%AF%B4%E6%98%8E%E4%BA%86) PLE 的内存节省。

54.4 亿与 40 亿参数的差异是因为谷歌有一种有趣的报告 LLM 参数数量的方法。他们通常排除嵌入参数以使模型看起来更小，除非在这种情况下，包含它们以使模型看起来更大很方便。这并不是谷歌独有的，因为这种方法在该领域已经很普遍。

另一个有趣的技巧是 MatFormer[17] 概念（Matryoshka Transformer 的缩写）。例如，Gemma 3n 使用一个共享的 LLM（Transformer）架构，可以将其切片为更小、独立可用的模型。每个切片都经过训练，可以独立运行，因此在推理时，我们可以只运行你需要的部分（而不是大型模型）。

## 五、Mistral Small 3.1

Mistral Small 3.1 24B[18] 于 3 月在 Gemma 3 之后不久发布，值得注意，它在几个基准测试中优于 Gemma 3 27B（除了数学），同时速度更快。

Mistral Small 3.1 比 Gemma 3 更低的推理延迟的原因可能是他们的自定义分词器，以及缩小 KV 缓存和层数。否则，它是一个标准架构，如下图所示。

![](images\043f7dc05611d38c66eab9bb343493b3.jpg)

图 16：Gemma 3 27B 和 Mistral 3.1 Small 24B 的架构比较。

有趣的是，早期的 Mistral 模型使用了滑动窗口注意力，但他们在 Mistral Small 3.1 中似乎放弃了它。因此，由于 Mistral 使用常规分组查询注意力，而不是像 Gemma 3 中那样使用滑动窗口的分组查询注意力，也许由于能够使用更优化的代码（即 FlashAttention），还有额外的推理计算节省。例如，我推测虽然滑动窗口注意力减少了内存使用，但它不一定减少推理延迟，而 Mistral Small 3.1 正专注于这一点。

## 六、Llama 4

### 6.1 介绍一下 Llama 4？

本文前面关于专家混合（MoE）的广泛讨论再次得到了回报。Llama 4 [19]也采用了 MoE 方法，并且总体上遵循了一个相对标准的架构，与 DeepSeek-V3 非常相似，如下图所示。（Llama 4 包括原生多模态支持，类似于 Gemma 和 Mistral 等模型。然而，由于本文专注于语言建模，我们只专注于文本模型。）

![](images\3d3debaa17317b0a61c671cc5efecf62.jpg)

图 17：DeepSeek V3（6710 亿参数）和 Llama 4 Maverick（4000 亿参数）的架构比较。

### 6.2 介绍一下 Llama 4 和 DeepSeek-V3 区别？

虽然 Llama 4 Maverick 架构总体上看起来与 DeepSeek-V3 非常相似，但有一些有趣的差异值得强调。

1. 首先， **Llama 4 使用了与其前身类似的分组查询注意力** ，而 **DeepSeek-V3 使用了多头潜在注意力** ，我们在本文开头讨论过。
2. 现在，DeepSeek-V3 和 Llama 4 Maverick 都是非常大的架构， **DeepSeek-V3 的总参数数量大约大 68%** 。然而， **DeepSeek-V3 拥有 370 亿个活跃参数，比 Llama 4 Maverick（170 亿）多出一倍多** 。
3. **Llama 4 Maverick 使用了更经典的 MoE 设置，专家更少但更大** （2 个活跃专家，每个隐藏大小为 8192），相比之下， **DeepSeek-V3（9 个活跃专家，每个隐藏大小为 2048）** 。
4. 此外， **DeepSeek 在每个 Transformer 块（除了前 3 个）中使用 MoE 层** ，而 **Llama 4 在每个其他 Transformer 块中交替使用 MoE 和密集模块** 。

鉴于架构之间的许多小差异，很难确定它们对最终模型性能的确切影响。然而，主要的收获是，MoE 架构在 2025 年得到了显著普及。

## 七、Qwen3

### 7.1 Qwen3

#### 7.1.1 介绍一下 Qwen3？

Qwen 团队持续提供高质量的开放权重 LLM。当我共同建议 2023 年 NeurIPS 的 LLM 效率挑战时，我记得所有获胜解决方案都是基于 Qwen2 的。

现在，Qwen3 是另一个在其尺寸类别中排名靠前的模型系列。有 7 个密集模型：0.6B、1.7B、4B、8B、14B 和 32B。还有两个 MoE 模型：30B-A3B 和 235B-A22B。

让我们先讨论密集模型架构。在撰写本文时，0.6B 模型可能是目前可用的最小当前一代开放权重模型。根据我的个人经验，鉴于其小巧的尺寸，它的表现确实非常好。如果你打算本地运行，它具有出色的每秒标记吞吐量和低内存占用。更重要的是，由于其小巧的尺寸，它也很容易在本地进行训练（用于教育目的）。

#### 7.1.2 介绍一下 Qwen3 0.6B 和 Llama 3 1B 区别？

因此，Qwen3 0.6B 在大多数情况下已经取代了 Llama 3 1B。下图显示了这两个架构的比较。

![](images\1a5475444b437f3ca0aeb10835c92b5f.jpg)

图 18：Qwen3 0.6B 和 Llama 3 1B 的架构比较；请注意，Qwen3 是一个更深的架构，具有更多层，而 Llama 3 是一个更宽的架构，具有更多注意力头。

#### 7.1.3 介绍一下 Qwen3 0.6B 优点？

如果你对一个没有外部第三方 LLM 库依赖的可读 Qwen3 实现感兴趣，我最近从零开始实现了 Qwen3（使用纯 PyTorch）[20]。

上图中的计算性能数据基于我在 A100 GPU 上从零开始的 PyTorch 实现。可以看出，Qwen3 的内存占用更小，因为它总体上是一个更小的架构，但也使用了更小的隐藏层和更少的注意力头。

#### 7.1.4 介绍一下 Qwen3 0.6B 存在问题？

然而，它使用了比 Llama 3 更多的 Transformer 块，这导致运行时间更慢（每秒标记生成速度更低）。

### 7.2 Qwen3 (MoE)

#### 7.2.1 Qwen3 (MoE) 包含哪些版本？

如前所述，Qwen3 也有两种 MoE 风格：30B-A3B 和 235B-A22B。

#### 7.2.2 为什么像 Qwen3 这样的架构既有常规（密集）又有 MoE（稀疏）变体？

正如本文开头提到的， **MoE 变体有助于降低大型基础模型的推理成本** 。提供密集和 MoE 版本让用户可以根据他们的目标和约束灵活选择。

**密集模型通常更容易在各种硬件上进行微调、部署和优化** 。

另一方面， **MoE 模型针对扩展推理进行了优化** 。

> 举个栗子，在固定的推理预算下，它们可以实现更高的整体模型容量（即，由于在训练中更大，因此知识吸收量更大），而不会成比例地增加推理成本。

#### 7.2.3 Qwen3 常规（密集）又有 MoE（稀疏）变体 都适用哪些场景？

通过发布这两种类型，Qwen3 系列可以支持更广泛的使用案例：

1. **密集模型用于稳健性、简单性和微调**
2. **MoE 模型用于大规模高效服务** 。

#### 7.2.4 DeepSeek-V3 和 Qwen3 235B-A22B 的架构比较？

为了总结这一部分，让我们看看 Qwen3 235B-A22B（请注意，A22B 代表“220 亿活跃参数”）与 DeepSeek-V3 的比较，后者拥有近两倍多的活跃参数（370 亿）。

![](images\e2175f01d61199dfbfbac19f90c03310.jpg)

图 19：DeepSeek-V3 和 Qwen3 235B-A22B 的架构比较。

如上图所示，DeepSeek-V3 和 Qwen3 235B-A22B 的架构非常相似。然而，值得注意的是，Qwen3 模型不再使用共享专家（早期的 Qwen 模型，如 Qwen2.5-MoE[21] 使用了共享专家）。

不幸的是，Qwen3 团队没有透露他们放弃共享专家的原因。如果我不得不猜测， **也许是因为在他们的设置中，当他们将专家从 2（在 Qwen2.5-MoE 中）增加到 8（在 Qwen3 中）时，共享专家对训练稳定性不再必要。然后，他们能够通过仅使用 8 个而不是 8+1 个专家来节省额外的计算/内存成本** 。（然而，这并不能解释为什么 DeepSeek-V3 仍然保留其共享专家。）

## 八、SmolLM3

### 8.1 介绍一下 SmolLM3？

SmolLM3[22] 可能不像本文涵盖的其他 LLM 那样受欢迎，但我认为它仍然是一个有趣的模型，因为它在相对较小且方便的 30 亿参数模型大小上提供了非常好的建模性能，位于 Qwen3 的 1.7B 和 4B 模型之间，如下图所示。

此外，它还分享了很多训练细节，类似于 OLMo，这很少见，而且总是受欢迎的！

![](images\02bdced56853d72a71616bca5e8d619d.jpg)

图 20：来自 SmolLM3 公告帖子的注释图， [ https://huggingface.co/blog/smollm3，比较 ](https://huggingface.co/blog/smollm3%EF%BC%8C%E6%AF%94%E8%BE%83) SmolLM3 的胜率与 Qwen3 1.7B 和 4B 以及 Llama 3 3B 和 Gemma 3 4B

如下图所示的架构比较图所示，SmolLM3 架构看起来相当标准。也许最有趣的方面是它对 NoPE（无位置嵌入）的使用。

![](images\f37d8dfe95689d53077088f8528b94cf.jpg)

图 21：Qwen3 4B 和 SmolLM3 3B 的并排架构比较。

### 8.2 No Positional Embeddings (NoPE)

NoPE 在 LLM 语境中是一个旧想法，可以追溯到 2023 年的一篇论文（The Impact of Positional Encoding on Length Generalization in Transformers[23]），以移除显式的位置信息注入（如早期 GPT 架构中的经典绝对位置嵌入层或如今的 RoPE）。

在基于 Transformer 的 LLM 中，通常需要位置编码，因为自注意力独立于顺序对待标记。绝对位置嵌入通过添加一个额外的嵌入层来解决这个问题，该层向标记嵌入添加信息。

![](images\c9830ed0b431729935ea97a7e4aa7a81.jpg)

图 22：来自我的《从零构建大型语言模型》一书（ [ https://www.amazon.com/Build-Large-Language-Model-Scratch/dp/1633437167）的修改图，说明了绝对位置嵌入。 ](https://www.amazon.com/Build-Large-Language-Model-Scratch/dp/1633437167%EF%BC%89%E7%9A%84%E4%BF%AE%E6%94%B9%E5%9B%BE%EF%BC%8C%E8%AF%B4%E6%98%8E%E4%BA%86%E7%BB%9D%E5%AF%B9%E4%BD%8D%E7%BD%AE%E5%B5%8C%E5%85%A5%E3%80%82)

另一方面，RoPE 通过相对于其标记位置旋转查询和键向量来解决这个问题。

然而，在 NoPE 层中，根本没有添加这样的位置信号：不是固定的，不是学习的，不是相对的。什么都没有。

尽管没有位置嵌入，但由于因果注意力掩码，模型仍然知道哪些标记在前面。该掩码防止每个标记关注未来的标记。因此，位于位置 t 的标记只能看到位于位置 ≤ t 的标记，这保留了自回归排序。

因此，虽然没有显式添加位置信息，但模型结构中仍然隐含了一种方向感，并且 LLM 在常规的基于梯度的训练中，如果发现它有利于优化目标，就可以学会利用它。（查看 NoPE 论文的定理以获取更多信息。）

因此，总的来说，NoPE 论文[24]不仅发现没有必要注入位置信息，而且还发现 NoPE 具有更好的长度泛化性，这意味着随着序列长度的增加，LLM 的回答性能下降较少，如下图所示。

![](images\69423381a3f1bf7aebe1149de55b4018.jpg)

图 23：来自 NoPE 论文（ [ https://arxiv.org/abs/2305.19466）的注释图，显示 ](https://arxiv.org/abs/2305.19466%EF%BC%89%E7%9A%84%E6%B3%A8%E9%87%8A%E5%9B%BE%EF%BC%8C%E6%98%BE%E7%A4%BA) NoPE 具有更好的长度泛化性。

请注意，上面显示的实验是使用一个相对较小的 GPT 风格模型进行的，大约有 1 亿个参数，并且相对较小的上下文大小。目前尚不清楚这些发现如何推广到更大的当代 LLM。

出于这个原因，SmolLM3 团队可能只在每 4 层中“应用”了 NoPE（或者更准确地说，省略了 RoPE）。

## 九、Kimi 2

Kimi 2 [25]最近在 AI 社区引起了巨大轰动，因为它是一个具有令人难以置信的性能的开放权重模型。根据基准测试，它与谷歌的 Gemini、Anthropic 的 Claude 和 OpenAI 的 ChatGPT 模型等最佳专有模型不相上下。

一个显著的方面是它使用了相对较新的 Muon[26] 优化器而不是 AdamW。据我所知，这是 Muon 首次用于这种规模的生产模型（以前[27]，它只被证明可以扩展到 16B）。这导致了非常漂亮的训练损失曲线，这可能有助于将这个模型推到上述基准测试的顶端。

虽然人们评论说损失异常平滑（由于缺乏尖峰），但我认为它并没有异常平滑（例如，见下图中的 OLMo 2 损失曲线；此外，梯度的 L2 范数可能是跟踪训练稳定性的更好指标）。然而，令人惊讶的是损失曲线的衰减效果如此之好。

然而，正如本文引言中提到的，训练方法是另一个主题。

![](images\f9662500f7c406d8ea847230bbeaa091.jpg)

![](images\55f0aeeb72d30bc6642b4de07d036142.jpg)

模型本身有 1 万亿个参数，这确实令人印象深刻。

它可能是这一代最大的 LLM（鉴于 Llama 4 Behemoth 尚未发布，专有 LLM 不算在内，谷歌的 1.6 万亿 Switch Transformer[28] 是来自不同代的编码器-解码器架构）。

它也圆满了，因为 Kimi 2 使用了我们在本文开头介绍的 DeepSeek-V3 架构，只是他们将其做得更大，如下图所示。

![](images\d9744af6ce28400b93feefe24fd8e8c7.jpg)

图 25：DeepSeek V3 和 Kimi K2 的架构比较。

如上图所示，Kimi 2.5 基本上与 DeepSeek V3 相同，只是它在 MoE 模块中使用了更多专家，在多头潜在注意力（MLA）模块中使用了更少头。

Kimi 2 并非凭空而来。早期的 Kimi 1.5 模型在 Kimi k1.5: Scaling Reinforcement Learning with LLMs paper[29]中也有讨论，同样令人印象深刻。然而，它很不幸，DeepSeek R1 模型论文恰好于 1 月 22 日同一天发表。此外，据我所知，Kimi 1.5 权重从未公开分享。

因此，Kimi K2 团队很可能吸取了这些教训，并在 DeepSeek R2 发布之前将 Kimi K2 作为开放权重模型分享。在撰写本文时，Kimi K2 是最令人印象深刻的开放权重模型。

## 引用链接

- [1] DeepSeek R1: [ https://arxiv.org/abs/2501.12948 ](https://arxiv.org/abs/2501.12948)
- [2]DeepSeek V3: [ https://arxiv.org/abs/2412.19437 ](https://arxiv.org/abs/2412.19437)
- [3]原始 GQA 论文: [ https://arxiv.org/abs/2305.13245 ](https://arxiv.org/abs/2305.13245)
- [4]Llama 2 论文: [ https://arxiv.org/abs/2307.09288 ](https://arxiv.org/abs/2307.09288)
- [5]DeepSeek-V2: [ https://arxiv.org/abs/2405.04434 ](https://arxiv.org/abs/2405.04434)
- [6]2024 年的DeepSeek MoE: [ https://arxiv.org/abs/2401.06066 ](https://arxiv.org/abs/2401.06066)
- [7]2022 年的 DeepSpeedMoE 论文: [ https://arxiv.org/abs/2201.05596 ](https://arxiv.org/abs/2201.05596)
- [8]OLMo 2: [ https://arxiv.org/abs/2501.00656 ](https://arxiv.org/abs/2501.00656)
- [9]2020 年，Xiong: [ https://arxiv.org/abs/2002.04745 ](https://arxiv.org/abs/2002.04745)
- [10]Qwen3 从零开始实现: [ https://github.com/rasbt/LLMs-from-scratch/tree/main/ch05/11_qwen3 ](https://github.com/rasbt/LLMs-from-scratch/tree/main/ch05/11_qwen3)
- [11]Scaling Vision Transformers 论文: [ https://arxiv.org/abs/2302.05442 ](https://arxiv.org/abs/2302.05442)
- [12]OLMo 2 团队在 3 个月后发布了一个使用 GQA 的 32B 变体: [ https://huggingface.co/allenai/OLMo-2-0325-32B-Instruct ](https://huggingface.co/allenai/OLMo-2-0325-32B-Instruct)
- [13]Gemma 3: [ https://arxiv.org/abs/2503.19786 ](https://arxiv.org/abs/2503.19786)
- [14]2020 年的 LongFormer 论文: [ https://arxiv.org/abs/2004.05150 ](https://arxiv.org/abs/2004.05150)
- [15]Gemma 2: [ http://arxiv.org/abs/2408.00118 ](http://arxiv.org/abs/2408.00118)
- [16]Gemma 3n: [ https://developers.googleblog.com/en/introducing-gemma-3n/ ](https://developers.googleblog.com/en/introducing-gemma-3n/)
- [17]MatFormer: [ https://arxiv.org/abs/2310.07707 ](https://arxiv.org/abs/2310.07707)
- [18]Mistral Small 3.1 24B: [ https://mistral.ai/news/mistral-small-3-1 ](https://mistral.ai/news/mistral-small-3-1)
- [19]Llama 4 : [ https://ai.meta.com/blog/llama-4-multimodal-intelligence/ ](https://ai.meta.com/blog/llama-4-multimodal-intelligence/)
- [20]我最近从零开始实现了 Qwen3（使用纯 PyTorch）: [ https://github.com/rasbt/LLMs-from-scratch/tree/main/ch05/11_qwen3 ](https://github.com/rasbt/LLMs-from-scratch/tree/main/ch05/11_qwen3)
- [21]Qwen2.5-MoE: [ https://qwenlm.github.io/blog/qwen2.5-max/ ](https://qwenlm.github.io/blog/qwen2.5-max/)
- [22]SmolLM3: [ https://huggingface.co/blog/smollm3 ](https://huggingface.co/blog/smollm3)
- [23]The Impact of Positional Encoding on Length Generalization in Transformers: [ https://arxiv.org/abs/2305.19466 ](https://arxiv.org/abs/2305.19466)
- [24]NoPE 论文: [ https://arxiv.org/abs/2305.19466 ](https://arxiv.org/abs/2305.19466)
- [25]Kimi 2 : [ https://moonshotai.github.io/Kimi-K2/ ](https://moonshotai.github.io/Kimi-K2/)
- [26]Muon: [ https://github.com/KellerJordan/Muon ](https://github.com/KellerJordan/Muon)
- [27]以前: [ https://arxiv.org/abs/2502.16982 ](https://arxiv.org/abs/2502.16982)
- [28]Switch Transformer: [ https://arxiv.org/abs/2101.03961 ](https://arxiv.org/abs/2101.03961)
- [29]Kimi k1.5: Scaling Reinforcement Learning with LLMs paper: [ https://arxiv.org/abs/2501.12599 ](https://arxiv.org/abs/2501.12599)
