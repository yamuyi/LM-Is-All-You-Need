# 手撕MHA

在大模型面试中，“手撕多头注意力（MHA）” 是考察基础原理与工程实现能力的高频题。以下将从**核心原理拆解**、**PyTorch 代码实现（含详细注释）**、**关键细节说明**三部分展开，确保代码可运行且贴合面试场景。

### 一、MHA 核心原理回顾

多头注意力（Multi-Head Attention）是 Transformer 的核心模块，其本质是**将 “单头自注意力” 拆分到多个独立的子空间（Head）并行计算，再拼接结果，以捕捉更丰富的语义关联**（如单头可能只关注语法，多头可同时关注语法、语义、实体关系等）。

核心步骤（以 “自注意力” 为例，输入为`x`）：

1. **线性投影**：将输入`x`通过 3 个独立的线性层，生成`Q`（查询）、`K`（键）、`V`（值）；
2. **拆分多头**：将`Q/K/V`按 “头数（num_heads）” 拆分为多个子向量（每个 Head 的维度为`d_k = d_model / num_heads`，需满足`d_model % num_heads == 0`）；
3. **计算注意力得分**：对每个 Head，计算`Attention(Q, K, V) = Softmax( (Q@K^T) / √d_k ) @ V`（`√d_k`用于防止梯度消失）；
4. **拼接多头**：将所有 Head 的计算结果拼接，通过一个线性层输出最终结果。

### 二、PyTorch 手撕 MHA（可直接运行）

以下实现**通用的 MHA 类**，支持 “自注意力”“交叉注意力”（只需调整`Q/K/V`的输入来源），并包含 “掩码（Mask）” 支持（用于 Decoder 的遮挡未来位置）。

```python
import torch
import torch.nn as nn
import torch.nn.functional as F


class MultiHeadAttention(nn.Module):
    def __init__(self, d_model: int, num_heads: int, dropout: float = 0.1):
        """
        初始化多头注意力模块
        Args:
            d_model: 输入/输出的特征维度（需满足 d_model % num_heads == 0）
            num_heads: 注意力头的数量
            dropout:  dropout概率（防止过拟合）
        """
        super().__init__()
        assert d_model % num_heads == 0, "d_model必须能被num_heads整除"
        
        # 1. 核心参数定义
        self.d_model = d_model          # 整体特征维度
        self.num_heads = num_heads      # 头数
        self.d_k = d_model // num_heads # 每个头的特征维度（子空间维度）
        
        # 2. 线性投影层（Q、K、V共享输入，但用独立权重）
        self.w_q = nn.Linear(d_model, d_model)  # Q的线性层：d_model → d_model
        self.w_k = nn.Linear(d_model, d_model)  # K的线性层：d_model → d_model
        self.w_v = nn.Linear(d_model, d_model)  # V的线性层：d_model → d_model
        
        # 3. 输出线性层（拼接多头后映射回d_model）
        self.w_o = nn.Linear(d_model, d_model)
        
        # 4. Dropout层（可选，用于正则化）
        self.dropout = nn.Dropout(dropout)

    def forward(
        self, 
        q: torch.Tensor, 
        k: torch.Tensor, 
        v: torch.Tensor, 
        mask: torch.Tensor = None
    ) -> torch.Tensor:
        """
        MHA前向传播（支持自注意力和交叉注意力）
        Args:
            q: 查询向量，形状 [batch_size, seq_len_q, d_model]
            k: 键向量，形状 [batch_size, seq_len_k, d_model]
            v: 值向量，形状 [batch_size, seq_len_v, d_model]（自注意力中seq_len_k == seq_len_v）
            mask: 掩码向量，形状 [batch_size, 1, seq_len_q, seq_len_k]（可选，遮挡无效位置）
        Returns:
            output: MHA输出，形状 [batch_size, seq_len_q, d_model]
        """
        # -------------------------- Step 1: 线性投影生成Q、K、V --------------------------
        q_proj = self.w_q(q)  # [batch_size, seq_len_q, d_model]
        k_proj = self.w_k(k)  # [batch_size, seq_len_k, d_model]
        v_proj = self.w_v(v)  # [batch_size, seq_len_v, d_model]

        # -------------------------- Step 2: 拆分多头（调整维度以并行计算） --------------------------
        # 维度变换逻辑：[batch, seq_len, d_model] → [batch, num_heads, seq_len, d_k]
        # 原因：让每个头独立计算注意力，且保持batch和seq_len的对应关系
        q_split = q_proj.view(q_proj.size(0), -1, self.num_heads, self.d_k).transpose(1, 2)
        k_split = k_proj.view(k_proj.size(0), -1, self.num_heads, self.d_k).transpose(1, 2)
        v_split = v_proj.view(v_proj.size(0), -1, self.num_heads, self.d_k).transpose(1, 2)
        # 变换后形状：
        # q_split: [batch_size, num_heads, seq_len_q, d_k]
        # k_split: [batch_size, num_heads, seq_len_k, d_k]
        # v_split: [batch_size, num_heads, seq_len_v, d_k]

        # -------------------------- Step 3: 计算注意力得分与权重 --------------------------
        # 1. 计算Q与K的相似度：Q @ K^T（每个头独立计算）
        attn_scores = torch.matmul(q_split, k_split.transpose(-2, -1))  # [batch, num_heads, seq_len_q, seq_len_k]
        # 2. 缩放（除以√d_k）：防止seq_len_k过大导致得分溢出，softmax后梯度消失
        attn_scores = attn_scores / torch.sqrt(torch.tensor(self.d_k, dtype=torch.float32, device=attn_scores.device))
        
        # 3. 应用掩码（如Decoder的Masked MHA，遮挡未来位置）
        if mask is not None:
            # 掩码值设为-1e9（softmax后接近0，相当于“不关注”该位置）
            attn_scores = attn_scores.masked_fill(mask == 0, -1e9)
        
        # 4. Softmax归一化：得到注意力权重（每个位置的权重和为1）
        attn_weights = F.softmax(attn_scores, dim=-1)  # [batch, num_heads, seq_len_q, seq_len_k]
        # 5. Dropout（可选，正则化权重）
        attn_weights = self.dropout(attn_weights)

        # -------------------------- Step 4: 计算注意力输出（权重 × V） --------------------------
        attn_output = torch.matmul(attn_weights, v_split)  # [batch, num_heads, seq_len_q, d_k]

        # -------------------------- Step 5: 拼接多头（恢复原维度） --------------------------
        # 维度逆变换：[batch, num_heads, seq_len_q, d_k] → [batch, seq_len_q, d_model]
        # 1. 先转置回 [batch, seq_len_q, num_heads, d_k]
        attn_output = attn_output.transpose(1, 2)
        # 2. 拼接：将num_heads个d_k维度合并为d_model（num_heads × d_k = d_model）
        attn_output = attn_output.contiguous().view(attn_output.size(0), -1, self.d_model)
        # 注：contiguous()确保内存连续，避免view()报错

        # -------------------------- Step 6: 输出线性层（映射回d_model） --------------------------
        final_output = self.w_o(attn_output)  # [batch_size, seq_len_q, d_model]

        return final_output
```

### 三、面试高频追问与关键细节

1. **为什么`d_model`必须能被`num_heads`整除？**
   因为每个头的维度`d_k = d_model / num_heads`，若不能整除，拆分后无法均匀分配特征，导致部分头的维度不一致，无法并行计算和拼接。
2. **掩码（Mask）的作用与形状？**
   - 作用：遮挡 “无效位置”（如自注意力中遮挡 padding 位置，Decoder 的 Masked MHA 中遮挡 “未来位置”，避免模型提前看到答案）；
   - 形状：`[batch_size, 1, seq_len_q, seq_len_k]`，其中 “1” 是为了与`num_heads`维度广播（无需为每个头单独做掩码）。
3. **为什么要缩放（除以√d_k）？**
   假设`Q`和`K`的元素服从均值 0、方差 1 的分布，则`Q@K^T`的元素均值为 0、方差为`d_k`（因`Q`的每行有`d_k`个元素，每个元素与`K^T`的列元素相乘求和）。当`d_k`较大时（如`d_model=512, num_heads=8 → d_k=64`），得分会过大，导致`softmax`后值接近 0 或 1，梯度消失。除以√d_k 可将方差归一化为 1，避免该问题。
4. **如何验证 MHA 实现正确？**
   - 自注意力场景：输入`q=k=v`，输出维度应与输入一致；
   - 掩码验证：对`seq_len_q=3`的输入，用`mask`遮挡`(0,1)`（第 0 个位置不能关注第 1 个位置），则`attn_weights[0, :, 0, 1]`应接近 0；
   - 梯度验证：反向传播时，权重梯度应无异常（如 NaN/Inf）。

### 四、测试代码（验证正确性）

```python
# 1. 初始化参数
batch_size = 2
seq_len = 5
d_model = 512
num_heads = 8

# 2. 构造输入（随机 tensor）
x = torch.randn(batch_size, seq_len, d_model)  # 自注意力输入：q=k=v=x

# 3. 初始化MHA
mha = MultiHeadAttention(d_model=d_model, num_heads=num_heads)

# 4. 前向传播（无掩码）
output = mha(q=x, k=x, v=x)

# 5. 验证输出形状（应与输入一致）
print(f"输入形状: {x.shape}")       # torch.Size([2, 5, 512])
print(f"输出形状: {output.shape}")  # torch.Size([2, 5, 512])
print("MHA实现验证通过！")
```