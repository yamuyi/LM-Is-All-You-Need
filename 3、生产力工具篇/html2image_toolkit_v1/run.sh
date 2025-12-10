# python run.py full-process -i data/input/mhtml/example.mhtml -w "羊头人的AI日志" --clean-md --remove-image-watermark

# 流程1：转换为Markdown供编辑
python run.py export-md --batch

# 用户手动编辑 data/working/md/ 中的Markdown文件

# 流程2：处理编辑后的Markdown生成图片
python run.py process-edited-md --batch --optimize
