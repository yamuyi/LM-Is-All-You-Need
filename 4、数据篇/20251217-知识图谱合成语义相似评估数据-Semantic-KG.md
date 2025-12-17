---
title: 多智能体数据合成框架Matrix及知识图谱合成语义相似评估数据思路
url: https://mp.weixin.qq.com/s/yd9HnvTVGXt0kTodE7x6Jw
publishedTime: undefined
---

今天是2025年11月29日，星期六，北京，天气晴

继续看技术，看数据合成的方向。

看两个点。

**一个是基于知识图谱生成语义相似评估数据集。这也是一个很显示的需求，即LLM输出评估需求，在RAG、LLM-as-a-judge等场景中需准确理解文本语义，\*\***但现有评估依赖语义相似度测量，而传统方法（如ROUGE、BLEU）存在缺陷，也就是仅捕获表面句法/词汇相似，忽略语义内容\*\*，且对改变语义的文本微小扰动不敏感。

但是要改善的话，靠人工弄又很费时费力，那就使用知识图谱进行生成，因此，可以看一个工作。**知识图谱合成语义相似评估数据思路-Semantic-KG**

另一个，涉及到大模型多智能体的数据合成思路，怎么提升吞吐量，有很多思路，比如**P2P去中心化、行级调度等**，看一个meta的工作-**多智能体数据合成提速框架-Matrix**

多总结，多归纳，**多从底层实现分析逻辑，**会有收获。

## 一、知识图谱合成语义相似评估数据-Semantic-KG

知识图谱用于合成大模型语义相似度评估数据很简单。

**可以把KG想象成“乐高积木模型”—原始模型是“猫->喜欢->鱼”，扰动就是“换积木”（把“鱼”换成“老鼠”）或“拆积木”（去掉“喜欢”关系），再让LLM把积木模型描述成自然语言，就得到了“猫喜欢鱼”和“猫喜欢老鼠”（相似句）、“猫鱼”（相异句），不用人工编句子。**

因此，可以看一个思路《**Semantic-KG: Using Knowledge Graphs to Construct Benchmarks for Measuring Semantic Similarity**》，https://arxiv.org/pdf/2511.19925，代码在https://github.com/QiyaoWei/semantic-kg

看下几个点。

**1、核心实现流程**

实现流程很简单，如下四步：

![图片](https://mmbiz.qpic.cn/sz_mmbiz_png/fUBU1yiaEmJgaNib1qGXS0I4Gg7W3913W6TCygZEFSx4uo9rxltgslwfgTyYy6B94icHBiaMLTibKr8FX8axibg8rbIg/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=0)

**step1.子图采样**：从KG中通过广度优先搜索（BFS）采样包含5-20个节点的子图，保证节点多样性；

但是，不同领域子图节点/边数不同，如CodexEdgeDeletion类子图平均3.11个节点、12.11条边。

**–>step2.子图扰动**：对采样子图施加四种扰动（**节点删除/替换、边删除/替换**），制造语义变异；

**节点删除（NodeRemoval）**。随机删除1个节点及所有关联边，被删节点的邻居至少有2个其他邻居，避免孤立节点。

**例如，删除“苯地平”节点，关联的“增加效应-心动过缓”边同时删除。**

**节点替换（NodeReplacement）**。随机替换/1个节点为同类型节点，更新所有关联边。仅替换为相同类型节点（如“Person”→“Person”）。

**例如，“伊丽莎白一世”（子类型：Person）替换为“玛丽一世”。**

**边删除（EdgeRemoval**）。随机删除2个节点间的1条边，两边节点至少有2条其他边，避免孤立节点。

例如，**删除“挪威-成员国-禁止化学武器组织”的“成员国”边。**

**边替换（EdgeReplacement）**。随机替换边的关系值为反向/冲突值，基于领域自定义映射（如“增加效应”→“降低效应”）。

例如，**“苯地平-增加效应-心动过缓”替换为“苯地平-降低效应-心动过缓”**

**–>step3.语句生成**：利用LLM将原始子图与扰动子图转化为自然语言语句，也就是**转换triples：将采样子图和扰动子图转为“源节点-关系-目标节点”的triple格式（边数=triple数）。形成相似/相异语句对**。

给LLM的提示包含“子图三元组列表+生成规则”，比如：**“根据以下关系描述一个自然句子，不要遗漏实体和关系：(苹果,属于,水果),(苹果,口感,甜)”；**

**–>step4.语句验证**：通过LLM重构KG，验证生成语句是否准确反映原始子图结构。

其实就是：**把生成的自然句子喂给LLM，让LLM从句子中提取三元组（重构KG），对比重构后的KG与原始子图**。

这个又涉及到对应的实体抽取和关系抽取了，如下prompt:

![图片](https://mmbiz.qpic.cn/sz_mmbiz_png/fUBU1yiaEmJgaNib1qGXS0I4Gg7W3913W6ibERlOCjWcPFqImzD4E5oWPH0baJTEYFK16nUgvIuSQHB79nupJzk1Q/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=1)

最后，**计算重合率（F1分数）**，只保留F1≥0.9的语句对。

**2、应用点**

所以，这其实也是**基于KG来做幻觉检测例子**。

![图片](https://mmbiz.qpic.cn/sz_mmbiz_png/fUBU1yiaEmJgaNib1qGXS0I4Gg7W3913W6iadzC5YkX9aGTiafYoaVoiaF1bwSKQU4HdVNsHpOx5YMiaUlRvGKvDPWyg/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=2)

**高风险领域“LLM质检工具”**，例如验证诊断报告生成的准确性（比如模型输出“药物A治疗高血压”，是否与原始病历中的“药物A缓解高血压”语义一致）；

**检测智能投顾的话术合规性**（比如“股票A会上涨”和“股票A可能上涨”的语义差异，避免夸大宣传）；

**评估RAG系统的回答质量**（比如用户问“产品B的功能”，RAG输出是否与知识库中“产品B的核心功能”语义匹配）。

## 二、多智能体数据合成提速框架-Matrix

来看一个工作，故事是“**多智能体协作干活的高效工具**”，专门用来批量生成AI训练需要的“模拟数据”，解决之前工具“**慢、撑不起大规模、只能干单一活**”的问题。

《**Matrix: Peer-to-Peer Multi-Agent Synthetic Data Generation Framework**》(https://arxiv.org/pdf/2511.21686，https://github.com/facebookresearch/matrix?tab=readme-ov-file)，核心就是实现吞吐量提升。

从方式上，有如下几个：

**一个是P2P去中心化智能体**：智能体独立扩展，无集中式瓶颈，支持数万并发；

**一个是行级调度**：避免批处理中“慢任务阻塞”，提升GPU利用率（如NaturalReasoning场景中，行级调度比RayData批处理快2.1×）；

**一个是分布式服务卸载**：LLM推理（vLLM/SGLang）、容器执行（Apptainer）等计算密集操作由**专用分布式服务处理**，轻量智能体专注任务流转，减少资源竞争；

**一个是多维度并行策略**：数据并行（拆分数据集）、任务并行（asyncio异步）、智能体并行（多RayActor）协同，最大化集群资源利用（如NaturalReasoning中20个数据分区+700任务并发，吞吐量提升1.61×）。

项目开源了，在：**https://github.com/facebookresearch/matrix**

来看几个问题，**包括方案设计以及验证方式**。

核心就是“去中心化+分工明确+不浪费资源”。

![图片](https://mmbiz.qpic.cn/sz_mmbiz_png/fUBU1yiaEmJgaNib1qGXS0I4Gg7W3913W638aXEntDGQLhqZU04XDNs6gejmCqphTpvTazxZN2ibDicNMM8jFJib2mA/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=3)

**1、Collaborative Reasoner (Coral)推理数据合成-去中心化**

例如，让两个AI互相对话讨论，生成“推理题+解题思路”（比如数学题、常识题的思考过程）；

![图片](https://mmbiz.qpic.cn/sz_mmbiz_png/fUBU1yiaEmJgaNib1qGXS0I4Gg7W3913W6TbQd2iaX4abR5r0hD2ricZFkkE6chezMWvgRuhWic0ibyVfvo7TqRYWK3g/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=4)

形式化可以为**双智能体（教师+学生）通过多轮对话讨论、达成共识，生成MMLU-Pro问题的推理数据，用于LLM微调**。

基线上，使用官方Coral实现，单集中式协调器管理并发任务，模型使用Llama-3.1-8B-Instruct；

![图片](https://mmbiz.qpic.cn/sz_mmbiz_png/fUBU1yiaEmJgaNib1qGXS0I4Gg7W3913W6vzQHrTwLXPy8pSXao1URCLdLEuaREOp964X7aYJEGVn1UqxEoJSjmA/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=5)

这种传统集中式框架（如Coral、Tau2-agent基线）**依赖单一协调器管理所有任务的控制流、数据流及生命周期，当并发任务达数万级时，协调器的调度、消息转发能力会成为瓶颈**，导致吞吐量饱和（如Coral基线在并发5000时即plateau）；

Matrix将**每个任务的状态（协调逻辑、中间结果、对话历史）序列化为可传递的消息**，智能体无状态且可弹性扩展，任务通过分布式队列在智能体间异步流转，无需集中式节点统一调度。

然后，硬件使用最高31个A100节点（共248GPU），并发数=50×GPU数量（每GPU50并发查询）。

**结论是：Matrix吞吐量是基线的6.8×**

大白话解释就是：**没有统一的总指挥**，每个任务都带着自己的“干活流程”（比如“先筛选网页→再评分→最后出题”），像“接力棒”一样在小助手之间传。小助手各自独立干活。

**2、NaturalReasoning数据合成-行级调度**

又如，从网页里筛选有用内容，自动出难题+标准答案+推理步骤；

![图片](https://mmbiz.qpic.cn/sz_mmbiz_png/fUBU1yiaEmJgaNib1qGXS0I4Gg7W3913W6UT2gSKt27ibG6FjeqL5uX6Y7IH7v4y4oicyMJvEz0lMuWJqrTGMvJvwg/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=6)

从实现思路上，**从DCLMWeb文档中提取高质量推理问题，流程为“过滤（英文+推理内容）→评分（多维度质量）→问题生成”**。

在**智能体配置**上，过滤智能体使用微调Llama-3.1-3B-Instruct（判断是否含推理内容）；

评分/问题智能体使用Llama-3.3-70B-Instruct。

基线对比的是\*\* Ray Data（批级调度）**，批级调度中慢任务会阻塞整批处理，导致GPU空闲，其思想就是**以前是“一批活一起干”，比如100个任务凑成一批，只要有1个任务慢，剩下99个都得等，机器就闲着；

所以，改一下，改成**行级调度（每个任务独立推进）**，区别于集中式框架常依赖的现在是“单个任务独立干”，不管别的任务快不快，一个任务干完马上启动下一个，GPU、CPU一直忙着，利用率拉满。

得到的对比结果如下：

![图片](https://mmbiz.qpic.cn/sz_mmbiz_png/fUBU1yiaEmJgaNib1qGXS0I4Gg7W3913W6U9ANlSpiajOicxMDQYBqFp83VTS8n7OUw2USIt9ib4o98mYESibY9icX7Ww/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=7)

结论是M**atrix行级调度吞吐量是批级调度的2.1×，因避免了“慢任务阻塞整批”的空闲问题**

**3、Tau2-bench任务-分布式服务卸载及多智能体并行**

模拟客服场景。一个AI扮用户（说“网络断了”），**一个AI扮客服（查问题、给方案**），生成真实的服务对话轨迹，用来训练AI客服。

![图片](https://mmbiz.qpic.cn/sz_mmbiz_png/fUBU1yiaEmJgaNib1qGXS0I4Gg7W3913W6ibymhzaRlYmm06Hl29aQjJU3emGlQ5edKSV4uSA7tXkt7s5dFNicDhxQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=8)

建模方面，**生成电信领域客服/故障排除的任务轨迹，涉及4个智能体（用户模拟器、助手、工具执行器、奖励计算器），轨迹用于LLM工具使用能力微调**。

对比实验上，**官方Tau2-agent实现，单节点Python线程运行，工具逻辑本地执行**，无法利用分布式资源；

Matrix将**用户模拟器、助手、工具执行器等拆分为分布式智能**体，13个H100节点部署1500容器+56个LLM副本，充分利用集群算力，模型使用gpt-oss-120b（OpenAI2025）。

![图片](https://mmbiz.qpic.cn/sz_mmbiz_png/fUBU1yiaEmJgaNib1qGXS0I4Gg7W3913W68gSPje46C2IN8hPLY3SQibHxZGkibRvDkBpz7UncicPtqwc6heABeNHXQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=9)

结论上，**Matrix吞吐量是基线的15.4×，且奖励值（轨迹质量）一致**。

## 参考文献

1、https://arxiv.org/pdf/2511.19925

2、https://arxiv.org/pdf/2511.21686

## 关于我们

老刘，NLP开源爱好者与践行者，主页：https://liuhuanyong.github.io。

**对大模型&知识图谱&RAG&文档理解感兴趣，并对每日早报、老刘说NLP历史线上分享、心得交流等感兴趣的，欢迎加入社区，社区持续纳新。**

加入社区方式：关注公众号，在后台菜单栏中点击会员社区加入。