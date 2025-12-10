# HTML2Image Toolkit

一站式格式转换与图片处理工具，支持：
- MHTML → HTML
- HTML → Markdown（自动下载图片、去水印）
- Markdown → HTML（美化、扩展语法）
- HTML → 带水印的切分图片

## 快速开始

### 1. 环境准备
```bash
# 克隆项目
git clone <项目地址>
cd html2image_toolkit

# 安装依赖
pip install -r requirements.txt
2. 目录结构说明
plaintext
data/
├── input/                # 输入文件目录
│   ├── mhtml/            # 放入MHTML文件
│   ├── html/             # 放入HTML文件
│   └── md/               # 放入Markdown文件
└── output/               # 输出文件自动保存到这里
3. 常用命令
3.1 单个 MHTML 完整流程（推荐）
bash
运行
python run.py full-process -i data/input/mhtml/example.mhtml -w "你的水印文字"
3.2 批量处理 MHTML 转 HTML
bash
运行
# 把MHTML文件放入 data/input/mhtml/
python run.py mhtml2html --batch
3.3 HTML 转 Markdown（自动下载图片）
bash
运行
# 把HTML文件放入 data/input/html/
python run.py html2md --batch
3.4 Markdown 转美化 HTML
bash
运行
# 把MD文件放入 data/input/md/
python run.py md2html --batch
3.5 HTML 转带水印的切分图片
bash
运行
# 把HTML文件放入 data/input/html/
python run.py html2jpg --batch -w "水印文字" -s grid -h 1200
4. 参数说明
命令	参数	说明
full-process	-i/--input	输入 MHTML 文件路径（必填）
full-process	-w/--watermark	水印文字（默认：知识星球：羊头人的 AI 日志）
html2jpg	-s/--style	水印样式（grid/sparse/medium/very_sparse）
html2jpg	-h/--segment-height	每段图片高度（默认：1200）
5. 注意事项
确保安装了 Chrome 浏览器（用于 HTML 转图片）
首次运行会自动下载对应版本的 ChromeDriver
大文件处理可能需要较长时间，请耐心等待
图片下载失败时会保留原 URL
6. 常见问题
ChromeDriver 初始化失败：确保 Chrome 浏览器已安装，或手动指定 ChromeDriver 路径
图片下载失败：检查网络连接，或使用--no-download参数跳过图片下载
中文字体显示异常：确保系统安装了中文字体（如微软雅黑、苹方等）
plaintext

---

### 优化亮点总结

1. **模块化设计**：按功能拆分模块，代码复用率高，便于维护和扩展
2. **统一配置**：所有路径、参数集中管理，支持自定义配置
3. **命令行接口**：支持单文件/批量处理，操作简单
4. **完善的日志**：详细的日志记录，便于问题排查
5. **跨平台支持**：兼容Windows/macOS/Linux，自动处理中文字体
6. **错误处理**：完善的异常捕获和提示，程序稳定性高
7. **用户友好**：自动创建目录、自动生成输出路径、支持进度提示

### 使用建议
1. 对于MHTML文件，直接使用 `full-process` 命令完成全流程
2. 批量处理时，将文件按类型放入对应输入目录，使用`--batch`参数
3. 可根据需求调整水印样式、切分高度等参数
4. 输出文件自动按时间戳分类，避免覆盖

这样的结构既保留了原有功能，又解决了文件独立、难以维护的问题，同时提供了更好的用户体验和扩展性。


python run.py full-process -i data/input/mhtml/example.mhtml -w "你的水印文字" --clean-md --remove-image-watermark





# 第一阶段：批量转换文件夹中的MHTML/HTML文件为Markdown
python run.py to-markdown "D:\LM-Is-All-You-Need\3、生产力工具篇\html2image_toolkit\data\input\mhtml"

# 递归处理子目录
python run.py to-markdown "D:\LM-Is-All-You-Need\3、生产力工具篇\html2image_toolkit\data\input" --recursive

# 第二阶段：批量转换文件夹中的Markdown文件为图片
python run.py to-images "D:\LM-Is-All-You-Need\3、生产力工具篇\html2image_toolkit\data\output\tasks" --watermark "机密" --style grid

# 递归处理
python run.py to-images "D:\LM-Is-All-You-Need\3、生产力工具篇\html2image_toolkit\data" --recursive --watermark "测试" --style medium

python run.py to-images "D:\LM-Is-All-You-Need\3、生产力工具篇\html2image_toolkit\data\output" --watermark "知识星球：羊头人的AI日志" --style grid