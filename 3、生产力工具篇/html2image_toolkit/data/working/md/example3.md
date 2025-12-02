![cover_image](D:\LM-Is-All-You-Need\3、生产力工具篇\html2image_toolkit\data\output\images\60f131590af18001574b2c3f769bf300.jpg)

#  技术动态 | 知识图谱用于复杂推理数据合成DeepDive、GDR清洗敏感信息及领域知识注入实现思路 

开放知识图谱 

_2025年12月1日 19:40_ _ 浙江  _

在小说阅读器中沉浸阅读 

转载公众号 | 老刘说NLP    

* * *

看几个问题，与知识相关。分别是知  ** 识图谱用于Agent强化学习数据合成方案DeepDive、大模型训练数据清洗方案-GDR、领域知识注入方案总结  ** 。 

多总结，多归纳，  ** 多从底层实现分析逻辑，  ** 会有收获。 

##  一、知识图谱用于Agent强化学习数据合成方案DeepDive 

继续看一个思路《  ** DeepDive: Advancing Deep Search Agents with Knowledge Graphs and Multi-Turn RL  ** 》，https://arxiv.org/pdf/2509.10446， https://github.com/THUDM/DeepDive，核心思路还是解决复杂推理监督数据【现有QA数据集（如HotpotQA、2WikiMultiHopQA）问题简单，仅需少量明确实体搜索，模拟真实场景中“多模糊实体+多跳推理”的深度搜索需求差，且人工标注高难度数据成本高、难规模化】。 

所以，搞了个  ** DeepDive框架，首先通过开放知识图谱自动合成含“模糊实体”的复杂问题，构建深度搜索问答数据集，然后采用端到端多轮强化学习（GRPO算法）训练，增强其长程推理与深度搜索工具使用能力  ** 。 

![图片](D:\LM-Is-All-You-Need\3、生产力工具篇\html2image_toolkit\data\output\images\69eb42123dd1ac20331f6600d1d52d15.jpg)

核心借鉴点看几个。 

** 1、数据合成  ** ，以KILT和AMinerKG为基础，通过三步生成高难度深度搜索QA对。 

** step1  ** :多跳路径提取,随机游走生成路径（长度k∈[5,9]），筛选节点（出度d_min=4，d_max=8），LLM(Claude-4-Sonnet)选逻辑一致的下一跳 

** ->step2  ** :实体属性模糊化，使用Gemini-2.5-Pro模糊具体属性（如“1948年”转“20世纪40年代末”），这个模糊思路在medresearch-r1中也使用过。 

![图片](D:\LM-Is-All-You-Need\3、生产力工具篇\html2image_toolkit\data\output\images\d13e1144a16491ed2c6e3e5d8641c1c1.jpg)

** ->step3:高难度问题筛选  ** ，GPT-4o四轮尝试解答，仅保留全部失败的问题，确保难度 

** 2、训练阶段，很常规的分SFT  ** （冷启动数据：Claude-4-Sonnet生成858条高质量工具调用轨迹）与RL（采用GRPO算法，奖励函数很常规，包括当“每步格式正确（推理链c_i+工具调用a_i）且最终答案匹配”时得1，否则0）两阶段训练，模型使用GLM-Z1-9B-0414、QwQ-32B。 

![图片](D:\LM-Is-All-You-Need\3、生产力工具篇\html2image_toolkit\data\output\images\789736901e89a1443c0a8c62b9ac5c3b.jpg)

总结起来，  ** 核心的核心就是基于知识图谱作多跳数据合成  ** ：初始化【基于KILT/AMinerKG，先随机游走（路径长度k∈[5,9]）提取多跳路径，筛选出度d∈[4,8]的节点（避免过易/过难扩展）】+  ** 数据增强  ** 【通过LLM（Gemini-2.5-Pro）模糊实体属性（如具体日期转范围）、混淆关键线索，构  ** 建“模糊实体+多跳逻辑”的QA对  ** 】+难度筛选【采用GPT-4o（前沿模型）对合成问题进行四轮尝试解答，仅保留其四次均无法正确解答的问题，确保问题需复杂推理与深度搜索才能解决】。 

但是，  ** 这都是通用域，是无针对性的，垂直领域的这个无感。在这里不带来知识，而是带来跳转，模拟多跳，跳那个玩意是啥，它不关心，只关系复杂度跟难度  ** ；比如  ** 航空维修，医疗等。到头来，还是需要业务来控制  ** ，怎么跳。因为这些工作的目标是为了给模型能力【推理能力】，而不是模型解决特定业务问题。 

##  二、大模型训练数据清洗方案-GDR 

利用预训练生成模型优化训练数据的框架，《Generative Data Refinement（GDR），Generative Data Refinement: Just Ask for Better Data》，https://arxiv.org/pdf/2509.08653 。 

![图片](D:\LM-Is-All-You-Need\3、生产力工具篇\html2image_toolkit\data\output\images\98c0cf945394c8e32bcc3c472d529924.jpg)

主要应对的问题是，  ** 大量用户生成内容、专有信息等未公开索引数据，因存在隐私泄露（如个人身份信息 PII）、有毒内容、版权问题等风险，无法直接用于训练  ** 。 

之前的解决策略是直接洗掉。现在GDR的策略是利用预训练大模型对原始数据进行“重写”，对含不良内容的原始数据集进行修改。 

在移除PII、有毒内容等不良信息的同时，保留原始数据中的有用信息，而非简单丢弃敏感或有害内容。结果是GDR对4chan/pol/板块10万条信息进行净化后，整体毒性评分显著下降。 

总结的看，一句话就是：【  ** 就是识别有害信息之后再改写，但是也是依赖于llm做合成，很费token  ** 】 

##  三、领域知识注入方案总结 

关于领域知识注入，一直也是一个研究点。看一个技术总结，《Injecting Domain-Specific Knowledge into Large Language Models:A Comprehensive Survey》，https://arxiv.org/pdf/2502.10708。核心点几个。 

![图片](D:\LM-Is-All-You-Need\3、生产力工具篇\html2image_toolkit\data\output\images\c3b52bc109af1a94a73046387746847a.jpg)

** 1、领域特定知识的界定  ** ，特定领域的专业信息，区别于通用知识，是解决专业任务的关键，如医疗领域的医学术语、诊疗方案等。知识表示形式包括知识图谱（结构化）、文本（非结构化）、向量嵌入（如软提示调优）及内部推理知识（如思维链提示），这是定义。 

** 2、注入方式，有四大知识注入范式  **

四种方式就是如下： 

![图片](D:\LM-Is-All-You-Need\3、生产力工具篇\html2image_toolkit\data\output\images\f291f37d3bc9a960465dfb0a63365cda.jpg)

** 1)动态知识注入  ** ，推理时从外部知识库/知识图谱检索相关信息，与输入结合输入模型，模型参数不变，优势在于更新便捷，无需重新训练，可整合新知识。局限在于依赖知识库质量与检索功能，受LLM输入长度限制，推理速度因检索延迟变慢。 

** 2)静态知识嵌入  ** ，通过全量或部分微调，将知识嵌入模型参数，训练获取编码领域知识的参数，推理时无需外部调用，优势在于推理速度快，无额外成本，性能较强。不足在于限知识固定，更新需重新微调，成本高，存在灾难性遗忘风险； 

** 3)模块化适配器  ** ，引入小型可训练模块存储领域知识，冻结LLM原始参数，仅训练适配器参数，优势在于参数高效，无需修改原始权重，保留通用能力，训练成本低，推理速度基本不受影响。局限在于需设计专用架构组件与超参数，性能受训练数据质量影响大； 

** 4)提示优化  ** ，设计含领域线索的文本提示引导模型，依赖内部知识，无需外部知识库或微调，优势在于部署轻量，无训练开销，跨域适应性强，推理速度快。不足在于提示设计难度大，长提示受上下文长度限制，仅能激活既有知识，无法整合新知识。 

其实，这都是技术纯研究问题，实际落地，其实是采用1)动态注入以及4)提示优化。 

##  参考文献 

1、https://arxiv.org/pdf/2502.10708 

2、https://arxiv.org/pdf/2509.08653 

3、https://arxiv.org/pdf/2509.10446 

** OpenKG  **   

OpenKG（中文开放知识图谱）旨在推动以中文为核心的知识图谱数据的开放、互联及众包，并促进知识图谱算法、工具及平台的开源开放。 

![图片](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate\(-249.000000, -126.000000\)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

点击  ** 阅读原文  ** ，进入 OpenKG 网站。    

预览时标签不可点 

关闭 __

****

更多 __

__

名称已清空 

**微信扫一扫赞赏作者**

喜欢作者  其它金额 

赞赏后展示我的头像 

文章 

暂无文章 

喜欢作者 

其它金额 

¥ 

最低赞赏 ¥0 

确定 

返回 __

**其它金额**

赞赏金额 

1 

2 

3 

4 

5 

6 

7 

8 

9 

0 

. 

# 

搜索「」网络结果 

​ 

留言 

暂无留言 

1条留言 

已无更多数据 

发消息 

写留言: 

微信扫一扫   
关注该公众号 

继续滑动看下一个 

轻触阅读原文 

![](D:\LM-Is-All-You-Need\3、生产力工具篇\html2image_toolkit\data\output\images\803547967fd9cf9df371302b0a896d0e.jpg)

向上滑动看下一个 

当前内容可能存在未经审核的第三方商业营销信息，请确认是否继续访问。 

继续访问  取消 

[ 微信公众平台广告规范指引 ](javacript:;)

知道了 

使用小程序 

取消  允许 

×  分析 

![跳转二维码](D:\LM-Is-All-You-Need\3、生产力工具篇\html2image_toolkit\data\output\images\99232feb6d9154cc540572b1dcede8d7.jpg)

![作者头像](D:\LM-Is-All-You-Need\3、生产力工具篇\html2image_toolkit\data\output\images\803547967fd9cf9df371302b0a896d0e.jpg)

微信扫一扫可打开此内容，   
使用完整服务 

![](D:\LM-Is-All-You-Need\3、生产力工具篇\html2image_toolkit\data\output\images\ba018c7153ef8193dbe4ab584a014b27.jpg)

已关注 

赞 

分享 

推荐 

写留言 

：  ，  ，  ，  ，  ，  ，  ，  ，  ，  ，  ，  ，  。  视频  小程序  赞  ，轻点两下取消赞  在看  ，轻点两下取消在看  分享  留言  收藏  听过 

可在「公众号 > 右上角 __ > 划线」找到划线过的内容 

![划线引导图](D:\LM-Is-All-You-Need\3、生产力工具篇\html2image_toolkit\data\output\images\132cc1505560857109badcb8c906aa5a.jpg)

我知道了 

, 

选择留言身份 

**

##  确认提交投诉 

你可以补充投诉原因（选填） 
