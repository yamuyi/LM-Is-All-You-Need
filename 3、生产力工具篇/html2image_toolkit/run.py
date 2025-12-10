import click
from pathlib import Path
import os
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

# 递归搜索文件的辅助函数
def list_files_recursive(folder_path: Path, extensions: list = None):
    """递归搜索文件夹中的所有文件（支持指定扩展名）"""
    # 确保使用绝对路径
    folder_path = Path(folder_path).absolute()
    if not folder_path.exists() or not folder_path.is_dir():
        return []
    
    files = []
    for item in folder_path.rglob("*"):
        if item.is_file():
            if extensions:
                if any(item.suffix.lower() == ext.lower() for ext in extensions):
                    files.append(item)
            else:
                files.append(item)
    
    return files

# 辅助函数：处理单个文件到Markdown
def process_single_to_markdown(input_file: Path, **kwargs):
    """处理单个文件到Markdown阶段"""
    # 确保使用绝对路径
    input_file = Path(input_file).absolute()
    file_ext = input_file.suffix.lower()
    
    # 创建任务目录
    task_dir = task_manager.create_task(input_file)
    
    result = None
    
    if file_ext in ['.mhtml', '.mht']:
        # MHTML -> HTML -> MD
        logger.info(f"处理MHTML文件到Markdown: {input_file}")
        
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
        
        result = {
            'mhtml': mhtml_result,
            'markdown': md_result,
            'status': 'markdown_generated'
        }
    
    elif file_ext == '.html':
        # HTML -> MD
        logger.info(f"处理HTML文件到Markdown: {input_file}")
        
        # HTML转Markdown
        md_result = convert_html_to_md(input_file, task_dir, download_images=True)
        if not md_result:
            logger.error(f"HTML转Markdown失败: {input_file}")
            return
        
        result = {
            'markdown': md_result,
            'status': 'markdown_generated'
        }
    
    elif file_ext in ['.md', '.markdown']:
        # 已经是Markdown文件，直接复制到任务目录
        logger.info(f"文件已经是Markdown格式: {input_file}")
        
        # 在任务目录中创建markdown子目录
        md_dir = task_dir / "markdown"
        md_dir.mkdir(exist_ok=True)
        
        # 复制文件
        target_md = md_dir / input_file.name
        import shutil
        shutil.copy2(input_file, target_md)
        
        md_result = {
            'output_md': str(target_md),
            'images_dir': str(md_dir / "images")
        }
        
        result = {
            'markdown': md_result,
            'status': 'markdown_ready'
        }
    
    # 更新任务状态
    if result:
        # 使用现有的update_task_status方法，避免调用不存在的get_task
        task_manager.update_task_status(input_file.stem, 'markdown_generated', result)
        logger.success(f"Markdown生成完成: {input_file}")
        logger.info(f"输出目录: {task_dir}")
        return {
            'task_dir': task_dir,
            'markdown_file': Path(result['markdown']['output_md']),
            'task_name': input_file.stem,
            'success': True
        }
    else:
        task_manager.update_task_status(input_file.stem, 'failed')
        return {'success': False, 'error': f'处理失败: {input_file}'}

# 辅助函数：处理单个Markdown文件到图片（简化版本，不依赖get_task）
def process_single_markdown_to_images(md_file: Path, task_name: str = None, **kwargs):
    """处理单个Markdown文件到图片阶段"""
    # 确保使用绝对路径
    md_file = Path(md_file).absolute()
    
    # 如果没有指定任务名称，使用Markdown文件名
    if not task_name:
        task_name = md_file.stem
    
    # 创建一个新的任务目录（不使用现有的，避免get_task调用）
    # 根据md_file路径推断可能的任务目录
    task_dir = None
    
    # 尝试从文件路径推断任务目录
    # 假设Markdown文件在任务目录的markdown子目录中
    if "markdown" in str(md_file.parent):
        # 尝试获取父目录（任务目录）
        possible_task_dir = md_file.parent.parent
        if possible_task_dir.exists() and (possible_task_dir / "markdown").exists():
            task_dir = possible_task_dir.absolute()
            logger.info(f"从文件路径推断任务目录: {task_dir}")
    
    # 如果没有找到合适的任务目录，创建新任务
    if not task_dir:
        task_dir = task_manager.create_task(md_file, task_name)
        logger.info(f"创建新任务目录: {task_dir}")
        
        # 确保Markdown文件在任务目录中
        if not md_file.parent.samefile(task_dir / "markdown"):
            md_dir = task_dir / "markdown"
            md_dir.mkdir(exist_ok=True)
            import shutil
            target_md = md_dir / md_file.name
            shutil.copy2(md_file, target_md)
            md_file = target_md
    
    logger.info(f"处理Markdown文件到图片: {md_file}")
    
    # 步骤1: Markdown转HTML（美化）
    html_result = convert_md_to_html(md_file, task_dir, use_extensions=True)
    if not html_result:
        logger.error(f"Markdown转HTML失败: {md_file}")
        return {'success': False, 'error': f'Markdown转HTML失败: {md_file}'}
    
    # 步骤2: HTML转带水印图片
    final_html = Path(html_result['output_html'])
    processor = HTMLToSegmentedImage()
    try:
        image_result = processor.process_html(final_html, task_dir, **kwargs)
        if image_result:
            result = {
                'html': html_result,
                'images': image_result,
                'status': 'completed'
            }
            
            # 更新任务状态
            task_manager.update_task_status(task_name, 'completed', result)
            
            logger.success(f"图片生成完成: {md_file}")
            logger.info(f"输出目录: {task_dir}")
            return {
                'task_dir': task_dir,
                'success': True
            }
    finally:
        processor.close()
    
    task_manager.update_task_status(task_name, 'failed')
    return {'success': False, 'error': f'图片生成失败: {md_file}'}

# 批量处理文件夹到Markdown
def process_folder_to_markdown(folder_path: Path, **kwargs):
    """处理文件夹中的所有文件到Markdown"""
    # 确保使用绝对路径
    folder_path = Path(folder_path).absolute()
    if not folder_path.exists():
        return {'success': False, 'error': f'文件夹不存在: {folder_path}'}
    
    if not folder_path.is_dir():
        return process_single_to_markdown(folder_path, **kwargs)
    
    # 收集所有支持的文件
    extensions = ['.mhtml', '.mht', '.html', '.md', '.markdown']
    files = []
    
    for ext in extensions:
        files.extend(list_files_recursive(folder_path, [ext]))
    
    if not files:
        return {'success': False, 'error': f'未找到支持的文件: {", ".join(extensions)}'}
    
    logger.info(f"在文件夹中找到 {len(files)} 个文件: {folder_path}")
    
    results = []
    success_count = 0
    
    for file in files:
        try:
            result = process_single_to_markdown(file, **kwargs)
            if result.get('success'):
                success_count += 1
                results.append({
                    'file': file,
                    'markdown_file': result.get('markdown_file'),
                    'task_name': result.get('task_name')
                })
            else:
                results.append({
                    'file': file,
                    'error': result.get('error', '未知错误')
                })
        except Exception as e:
            logger.error(f"处理文件失败 {file}: {e}")
            results.append({
                'file': file,
                'error': str(e)
            })
    
    return {
        'success': success_count > 0,
        'total': len(files),
        'success_count': success_count,
        'results': results,
        'summary': f'成功处理 {success_count}/{len(files)} 个文件'
    }

# 批量处理文件夹中的Markdown文件到图片
def process_folder_to_images(folder_path: Path, **kwargs):
    """处理文件夹中的所有Markdown文件到图片"""
    # 确保使用绝对路径
    folder_path = Path(folder_path).absolute()
    if not folder_path.exists():
        return {'success': False, 'error': f'文件夹不存在: {folder_path}'}
    
    if not folder_path.is_dir():
        return process_single_markdown_to_images(folder_path, **kwargs)
    
    # 收集所有Markdown文件
    extensions = ['.md', '.markdown']
    files = []
    
    for ext in extensions:
        files.extend(list_files_recursive(folder_path, [ext]))
    
    if not files:
        return {'success': False, 'error': f'未找到Markdown文件: {", ".join(extensions)}'}
    
    logger.info(f"在文件夹中找到 {len(files)} 个Markdown文件: {folder_path}")
    
    results = []
    success_count = 0
    
    for file in files:
        try:
            result = process_single_markdown_to_images(file, **kwargs)
            if result.get('success'):
                success_count += 1
                results.append({
                    'file': file,
                    'task_dir': result.get('task_dir'),
                    'success': True
                })
            else:
                results.append({
                    'file': file,
                    'error': result.get('error', '未知错误')
                })
        except Exception as e:
            logger.error(f"处理文件失败 {file}: {e}")
            results.append({
                'file': file,
                'error': str(e)
            })
    
    return {
        'success': success_count > 0,
        'total': len(files),
        'success_count': success_count,
        'results': results,
        'summary': f'成功处理 {success_count}/{len(files)} 个文件'
    }

# 原有的完整处理流程（保留兼容性）
def process_single_file(input_file: Path, command: str, **kwargs):
    """处理单个文件（完整流程）"""
    # 确保使用绝对路径
    input_file = Path(input_file).absolute()
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

# 第一阶段命令：转换为Markdown（支持文件和文件夹）
@cli.command(name="to-markdown")
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option("--recursive", "-r", is_flag=True, help="递归处理子目录")
def cmd_to_markdown(input_path: Path, recursive: bool):
    """将MHTML/HTML文件转换为Markdown格式（支持文件和文件夹）"""
    # 转换为绝对路径
    input_path = Path(input_path).absolute()
    
    if input_path.is_file():
        # 单个文件处理
        result = process_single_to_markdown(input_path)
        if result.get('success'):
            click.echo(f"✅ Markdown生成成功！")
            click.echo(f"📁 任务名称: {result['task_name']}")
            click.echo(f"📁 Markdown文件: {result['markdown_file']}")
            click.echo(f"📁 输出目录: {result['task_dir']}")
            click.echo(f"\n💡 下一步使用命令:")
            click.echo(f'  python run.py to-images "{result["markdown_file"]}"')
        else:
            click.echo(f"❌ 转换失败: {result.get('error', '未知错误')}")
    else:
        # 文件夹批量处理
        click.echo(f"📂 处理文件夹: {input_path}")
        if recursive:
            click.echo("🔍 递归处理子目录...")
        
        result = process_folder_to_markdown(input_path)
        
        if result.get('success_count', 0) > 0:
            click.echo(f"✅ {result['summary']}")
            click.echo(f"📊 统计:")
            click.echo(f"  - 总文件数: {result['total']}")
            click.echo(f"  - 成功: {result['success_count']}")
            click.echo(f"  - 失败: {result['total'] - result['success_count']}")
            
            # 显示成功的文件
            click.echo(f"\n📋 成功处理的文件:")
            for item in result['results']:
                if 'markdown_file' in item:
                    click.echo(f"  ✅ {item['file'].name}")
            
            # 显示失败的文件（如果有）
            failed_items = [item for item in result['results'] if 'error' in item]
            if failed_items:
                click.echo(f"\n❌ 失败的文件:")
                for item in failed_items:
                    click.echo(f"  ❌ {item['file'].name}: {item['error']}")
            
            click.echo(f"\n💡 下一步使用命令:")
            click.echo(f'  python run.py to-images "{input_path}"')
        else:
            click.echo(f"❌ 批量转换失败: {result.get('error', '未知错误')}")

# 第二阶段命令：从Markdown生成图片（支持文件和文件夹）
@cli.command(name="to-images")
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option("--task", "-t", help="指定任务名称（可选，仅对单个文件有效）")
@click.option("--watermark", "-w", default=DEFAULT_WATERMARK['text'], help="水印文字")
@click.option("--style", "-s", default=DEFAULT_WATERMARK['style'], 
              type=click.Choice(["grid", "sparse", "medium", "very_sparse"]),
              help="水印样式")
@click.option("--segment-height", "-h", default=DEFAULT_WATERMARK['segment_height'], 
              help="每段图片高度")
@click.option("--recursive", "-r", is_flag=True, help="递归处理子目录")
def cmd_to_images(input_path: Path, task: str, watermark: str, style: str, 
                  segment_height: int, recursive: bool):
    """将Markdown文件转换为带水印的图片（支持文件和文件夹）"""
    # 转换为绝对路径
    input_path = Path(input_path).absolute()
    
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
    
    if input_path.is_file():
        # 单个文件处理
        result = process_single_markdown_to_images(input_path, task, **watermark_kwargs)
        if result.get('success'):
            click.echo(f"✅ 图片生成成功！输出目录: {result['task_dir']}")
        else:
            click.echo(f"❌ 图片生成失败: {result.get('error', '未知错误')}")
    else:
        # 文件夹批量处理
        click.echo(f"📂 处理文件夹: {input_path}")
        click.echo(f"🖼️  水印设置: {watermark} ({style})")
        
        result = process_folder_to_images(input_path, **watermark_kwargs)
        
        if result.get('success_count', 0) > 0:
            click.echo(f"✅ {result['summary']}")
            click.echo(f"📊 统计:")
            click.echo(f"  - 总文件数: {result['total']}")
            click.echo(f"  - 成功: {result['success_count']}")
            click.echo(f"  - 失败: {result['total'] - result['success_count']}")
            
            # 显示成功的文件
            click.echo(f"\n📋 成功处理的文件:")
            for item in result['results']:
                if 'task_dir' in item:
                    click.echo(f"  ✅ {item['file'].name}")
            
            # 显示失败的文件（如果有）
            failed_items = [item for item in result['results'] if 'error' in item]
            if failed_items:
                click.echo(f"\n❌ 失败的文件:")
                for item in failed_items:
                    click.echo(f"  ❌ {item['file'].name}: {item['error']}")
            
            click.echo(f"\n📁 所有输出目录: data/output/final/")
        else:
            click.echo(f"❌ 批量图片生成失败: {result.get('error', '未知错误')}")

# 原有的完整处理命令（保留兼容性）
@cli.command(name="process")
@click.argument("input_file", type=Path)
@click.option("--watermark", "-w", default=DEFAULT_WATERMARK['text'], help="水印文字")
@click.option("--style", "-s", default=DEFAULT_WATERMARK['style'], 
              type=click.Choice(["grid", "sparse", "medium", "very_sparse"]),
              help="水印样式")
@click.option("--segment-height", "-h", default=DEFAULT_WATERMARK['segment_height'], 
              help="每段图片高度")
def cmd_process(input_file: Path, watermark: str, style: str, segment_height: int):
    """处理单个文件（完整流程，自动识别格式）"""
    # 转换为绝对路径
    input_file = Path(input_file).absolute()
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

# 批量处理命令（更新为支持两个阶段）
@cli.command(name="batch-process")
@click.option("--type", "-t", type=click.Choice(["mhtml", "html", "md", "all"]), 
              default="all", help="处理文件类型")
@click.option("--stage", "-s", type=click.Choice(["markdown", "images", "all"]), 
              default="all", help="处理阶段")
@click.option("--watermark", "-w", default=DEFAULT_WATERMARK['text'], help="水印文字")
@click.option("--style", "-s", default=DEFAULT_WATERMARK['style'], 
              type=click.Choice(["grid", "sparse", "medium", "very_sparse"]),
              help="水印样式")
@click.option("--segment-height", "-h", default=DEFAULT_WATERMARK['segment_height'], 
              help="每段图片高度")
def cmd_batch_process(type: str, stage: str, watermark: str, style: str, segment_height: int):
    """批量处理输入目录下的文件（可指定阶段）"""
    # 注意：这里有两个-s选项，一个用于stage，一个用于style
    # 我们需要修改其中一个的名称以避免冲突
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
            if stage in ["markdown", "all"]:
                result = process_single_to_markdown(file)
                if result.get('success'):
                    click.echo(f"✅ {file.name}: Markdown生成成功")
                    
                    # 如果需要继续处理到图片
                    if stage == "all" and result.get('markdown_file'):
                        image_result = process_single_markdown_to_images(
                            result['markdown_file'], 
                            result['task_name'],
                            **watermark_kwargs
                        )
                        if image_result.get('success'):
                            success_count += 1
                            click.echo(f"   ✅ 图片生成成功")
                        else:
                            click.echo(f"   ❌ 图片生成失败")
                    else:
                        success_count += 1
                else:
                    click.echo(f"❌ {file.name}: Markdown生成失败")
            elif stage == "images":
                # 直接从Markdown生成图片
                result = process_single_markdown_to_images(file, **watermark_kwargs)
                if result.get('success'):
                    success_count += 1
                    click.echo(f"✅ {file.name}: 图片生成成功")
                else:
                    click.echo(f"❌ {file.name}: 图片生成失败")
        except Exception as e:
            logger.error(f"处理文件失败 {file}: {e}")
            click.echo(f"❌ {file.name}: 异常 - {str(e)[:50]}...")
    
    click.echo(f"\n📊 批量处理完成: 成功 {success_count}/{len(files)} 个文件")
    click.echo(f"📁 输出目录: data/output/final/")

# 其余命令保持不变...
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