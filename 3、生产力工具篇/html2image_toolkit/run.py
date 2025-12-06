import click
from pathlib import Path
from src.utils.log_utils import logger
from src.utils.file_utils import list_files_in_dir
from src.converters.mhtml2html import convert_mhtml_to_html
from src.converters.html2md import convert_html_to_md
from src.converters.md2html import convert_md_to_html
from src.processors.html2jpg import HTMLToSegmentedImage
from src.config import (
    MHTML_INPUT_DIR, HTML_INPUT_DIR, MD_INPUT_DIR,
    DEFAULT_WATERMARK, get_task_output_dir
)
from src.task_manager import task_manager

# 辅助函数
def process_single_file(input_file: Path, command: str, **kwargs):
    """处理单个文件"""
    # 根据输入文件类型确定处理流程
    file_ext = input_file.suffix.lower()
    
    # 创建任务目录
    task_dir = task_manager.create_task(input_file)
    
    result = None
    
    if file_ext in ['.mhtml', '.mht']:
        # MHTML -> HTML -> MD -> HTML -> 图片
        logger.info(f"处理MHTML文件: {input_file}")
        
        # 步骤1: MHTML转HTML
        mhtml_result = convert_mhtml_to_html(input_file, task_dir)
        if not mhtml_result:
            logger.error(f"MHTML转HTML失败: {input_file}")
            return
        
        # 步骤2: HTML转Markdown
        html_file = Path(mhtml_result['output_html'])
        md_result = convert_html_to_md(html_file, task_dir, download_images=True)
        if not md_result:
            logger.error(f"HTML转Markdown失败: {html_file}")
            return
        
        # 步骤3: Markdown转HTML（美化）
        md_file = Path(md_result['output_md'])
        html_result = convert_md_to_html(md_file, task_dir, use_extensions=True)
        if not html_result:
            logger.error(f"Markdown转HTML失败: {md_file}")
            return
        
        # 步骤4: HTML转带水印图片
        final_html = Path(html_result['output_html'])
        processor = HTMLToSegmentedImage()
        try:
            image_result = processor.process_html(final_html, task_dir, **kwargs)
            if image_result:
                result = {
                    'mhtml': mhtml_result,
                    'markdown': md_result,
                    'html': html_result,
                    'images': image_result
                }
        finally:
            processor.close()
    
    elif file_ext == '.html':
        # HTML -> MD -> HTML -> 图片
        logger.info(f"处理HTML文件: {input_file}")
        
        # 步骤1: HTML转Markdown
        md_result = convert_html_to_md(input_file, task_dir, download_images=True)
        if not md_result:
            logger.error(f"HTML转Markdown失败: {input_file}")
            return
        
        # 步骤2: Markdown转HTML（美化）
        md_file = Path(md_result['output_md'])
        html_result = convert_md_to_html(md_file, task_dir, use_extensions=True)
        if not html_result:
            logger.error(f"Markdown转HTML失败: {md_file}")
            return
        
        # 步骤3: HTML转带水印图片
        final_html = Path(html_result['output_html'])
        processor = HTMLToSegmentedImage()
        try:
            image_result = processor.process_html(final_html, task_dir, **kwargs)
            if image_result:
                result = {
                    'markdown': md_result,
                    'html': html_result,
                    'images': image_result
                }
        finally:
            processor.close()
    
    elif file_ext in ['.md', '.markdown']:
        # MD -> HTML -> 图片
        logger.info(f"处理Markdown文件: {input_file}")
        
        # 步骤1: Markdown转HTML（美化）
        html_result = convert_md_to_html(input_file, task_dir, use_extensions=True)
        if not html_result:
            logger.error(f"Markdown转HTML失败: {input_file}")
            return
        
        # 步骤2: HTML转带水印图片
        final_html = Path(html_result['output_html'])
        processor = HTMLToSegmentedImage()
        try:
            image_result = processor.process_html(final_html, task_dir, **kwargs)
            if image_result:
                result = {
                    'html': html_result,
                    'images': image_result
                }
        finally:
            processor.close()
    
    # 更新任务状态
    if result:
        task_manager.update_task_status(input_file.stem, 'completed', result)
        logger.success(f"处理完成: {input_file}")
        logger.info(f"输出目录: {task_dir}")
        return task_dir
    else:
        task_manager.update_task_status(input_file.stem, 'failed')
        return None

@click.group()
def cli():
    """HTML2Image Toolkit - 按任务组织的一站式格式转换与图片处理工具"""
    pass

@cli.command(name="process")
@click.argument("input_file", type=Path)
@click.option("--watermark", "-w", default=DEFAULT_WATERMARK['text'], help="水印文字")
@click.option("--style", "-s", default=DEFAULT_WATERMARK['style'], 
              type=click.Choice(["grid", "sparse", "medium", "very_sparse"]),
              help="水印样式")
@click.option("--segment-height", "-h", default=DEFAULT_WATERMARK['segment_height'], 
              help="每段图片高度")
def cmd_process(input_file: Path, watermark: str, style: str, segment_height: int):
    """处理单个文件（自动识别格式）"""
    if not input_file.exists():
        click.echo(f"❌ 文件不存在: {input_file}")
        return
    
    # 构建水印参数
    watermark_kwargs = {
        'watermark_text': watermark,
        'style': style,
        'segment_height': segment_height
    }
    
    # 针对不同样式添加额外参数
    if style == "grid":
        watermark_kwargs.update({
            'grid_columns': DEFAULT_WATERMARK['grid_columns'],
            'grid_rows': DEFAULT_WATERMARK['grid_rows']
        })
    elif style == "very_sparse":
        watermark_kwargs['spacing_ratio'] = 4.0
    elif style == "sparse":
        watermark_kwargs['spacing_ratio'] = 3.0
    elif style == "medium":
        watermark_kwargs['spacing_ratio'] = 2.5
    
    result = process_single_file(input_file, "process", **watermark_kwargs)
    if result:
        click.echo(f"✅ 处理成功！输出目录: {result}")
    else:
        click.echo(f"❌ 处理失败")

@cli.command(name="batch-process")
@click.option("--type", "-t", type=click.Choice(["mhtml", "html", "md", "all"]), 
              default="all", help="处理文件类型")
@click.option("--watermark", "-w", default=DEFAULT_WATERMARK['text'], help="水印文字")
@click.option("--style", "-s", default=DEFAULT_WATERMARK['style'], 
              type=click.Choice(["grid", "sparse", "medium", "very_sparse"]),
              help="水印样式")
@click.option("--segment-height", "-h", default=DEFAULT_WATERMARK['segment_height'], 
              help="每段图片高度")
def cmd_batch_process(type: str, watermark: str, style: str, segment_height: int):
    """批量处理输入目录下的文件"""
    # 构建水印参数
    watermark_kwargs = {
        'watermark_text': watermark,
        'style': style,
        'segment_height': segment_height
    }
    
    if style == "grid":
        watermark_kwargs.update({
            'grid_columns': DEFAULT_WATERMARK['grid_columns'],
            'grid_rows': DEFAULT_WATERMARK['grid_rows']
        })
    elif style == "very_sparse":
        watermark_kwargs['spacing_ratio'] = 4.0
    elif style == "sparse":
        watermark_kwargs['spacing_ratio'] = 3.0
    elif style == "medium":
        watermark_kwargs['spacing_ratio'] = 2.5
    
    # 收集要处理的文件
    files = []
    
    if type in ["mhtml", "all"]:
        mhtml_files = list_files_in_dir(MHTML_INPUT_DIR, [".mhtml", ".mht"])
        files.extend(mhtml_files)
    
    if type in ["html", "all"]:
        html_files = list_files_in_dir(HTML_INPUT_DIR, [".html"])
        files.extend(html_files)
    
    if type in ["md", "all"]:
        md_files = list_files_in_dir(MD_INPUT_DIR, [".md", ".markdown"])
        files.extend(md_files)
    
    if not files:
        click.echo("❌ 未找到可处理的文件")
        return
    
    click.echo(f"📋 找到 {len(files)} 个文件，开始批量处理...")
    
    success_count = 0
    for file in files:
        try:
            result = process_single_file(file, "batch-process", **watermark_kwargs)
            if result:
                success_count += 1
                click.echo(f"✅ {file.name}: 成功")
            else:
                click.echo(f"❌ {file.name}: 失败")
        except Exception as e:
            logger.error(f"处理文件失败 {file}: {e}")
            click.echo(f"❌ {file.name}: 异常 - {str(e)[:50]}...")
    
    click.echo(f"\n📊 批量处理完成: 成功 {success_count}/{len(files)} 个文件")
    click.echo(f"📁 输出目录: data/output/final/")

@cli.command(name="list-tasks")
def cmd_list_tasks():
    """列出所有任务"""
    tasks = task_manager.list_tasks()
    
    if not tasks:
        click.echo("📭 暂无任务")
        return
    
    click.echo("📋 任务列表:")
    click.echo("-" * 60)
    for task in tasks:
        status_icon = "✅" if task['status'] == 'completed' else "🔄"
        click.echo(f"{status_icon} {task['name']}")
        click.echo(f"   目录: {task['dir']}")
        click.echo(f"   状态: {task['status']} | 创建时间: {task['created_at']}")
        click.echo("-" * 60)

@cli.command(name="cleanup")
@click.option("--task", "-t", help="清理指定任务（名称）")
@click.option("--all-temp", is_flag=True, help="清理所有任务的临时文件")
def cmd_cleanup(task: str, all_temp: bool):
    """清理任务文件"""
    if task:
        task_manager.cleanup_task_temp(task)
        click.echo(f"✅ 已清理任务临时文件: {task}")
    elif all_temp:
        tasks = task_manager.list_tasks()
        for t in tasks:
            task_manager.cleanup_task_temp(t['name'])
        click.echo(f"✅ 已清理 {len(tasks)} 个任务的临时文件")

@cli.command(name="archive")
@click.argument("task_name")
def cmd_archive(task_name: str):
    """归档任务目录"""
    task_manager.archive_task(task_name)
    click.echo(f"✅ 任务已归档: {task_name}")

if __name__ == "__main__":
    cli()