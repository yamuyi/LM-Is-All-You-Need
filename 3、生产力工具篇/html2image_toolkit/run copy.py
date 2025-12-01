import click
from pathlib import Path
from src.utils.log_utils import logger
from src.utils.file_utils import list_files_in_dir
from src.converters.mhtml2html import convert_mhtml_to_html
from src.converters.html2md import convert_html_to_md
from src.converters.md2html import convert_md_to_html
from src.processors.html2jpg import HTMLToSegmentedImage
from src.processors.md_cleaner import clean_markdown_content
from src.processors.image_watermark_remover import watermark_remover
from src.config import (
    MHTML_INPUT_DIR, HTML_INPUT_DIR, MD_INPUT_DIR,
    DEFAULT_WATERMARK
)

# 命令组
@click.group()
def cli():
    """HTML2Image Toolkit - 一站式格式转换与图片处理工具"""
    pass

# 1. MHTML转HTML
@cli.command(name="mhtml2html")
@click.option("--input", "-i", type=Path, help="单个MHTML文件路径")
@click.option("--batch", is_flag=True, help="批量处理input/mhtml目录下的所有MHTML文件")
def cmd_mhtml2html(input: Path, batch: bool):
    """MHTML文件转换为HTML文件"""
    files = []
    if batch:
        files = list_files_in_dir(MHTML_INPUT_DIR, [".mhtml", ".mht"])
    elif input and input.exists():
        files = [input]
    else:
        click.echo("请指定--input单个文件或--batch批量处理")
        return
    
    success_count = 0
    for file in files:
        result = convert_mhtml_to_html(file)
        if result:
            success_count += 1
    
    click.echo(f"\n处理完成: 成功 {success_count}/{len(files)} 个文件")

# 2. HTML转Markdown
@cli.command(name="html2md")
@click.option("--input", "-i", type=Path, help="单个HTML文件路径")
@click.option("--batch", is_flag=True, help="批量处理input/html目录下的所有HTML文件")
@click.option("--no-download", is_flag=True, help="不下载远程图片")
def cmd_html2md(input: Path, batch: bool, no_download: bool):
    """HTML文件转换为Markdown文件（支持下载图片）"""
    files = []
    if batch:
        files = list_files_in_dir(HTML_INPUT_DIR, [".html"])
    elif input and input.exists():
        files = [input]
    else:
        click.echo("请指定--input单个文件或--batch批量处理")
        return
    
    success_count = 0
    for file in files:
        result = convert_html_to_md(file, download_images=not no_download)
        if result:
            success_count += 1
    
    click.echo(f"\n处理完成: 成功 {success_count}/{len(files)} 个文件")

# 3. Markdown转HTML
@cli.command(name="md2html")
@click.option("--input", "-i", type=Path, help="单个Markdown文件路径")
@click.option("--batch", is_flag=True, help="批量处理input/md目录下的所有Markdown文件")
@click.option("--no-ext", is_flag=True, help="不启用Markdown扩展语法")
def cmd_md2html(input: Path, batch: bool, no_ext: bool):
    """Markdown文件转换为HTML文件（支持美化和扩展语法）"""
    files = []
    if batch:
        files = list_files_in_dir(MD_INPUT_DIR, [".md", ".markdown"])
    elif input and input.exists():
        files = [input]
    else:
        click.echo("请指定--input单个文件或--batch批量处理")
        return
    
    success_count = 0
    for file in files:
        result = convert_md_to_html(file, use_extensions=not no_ext)
        if result:
            success_count += 1
    
    click.echo(f"\n处理完成: 成功 {success_count}/{len(files)} 个文件")

# 4. HTML转带水印的切分图片
@cli.command(name="html2jpg")
@click.option("--input", "-i", type=Path, help="单个HTML文件路径")
@click.option("--batch", is_flag=True, help="批量处理input/html目录下的所有HTML文件")
@click.option("--watermark", "-w", default=DEFAULT_WATERMARK['text'], help="水印文字")
@click.option("--style", "-s", default=DEFAULT_WATERMARK['style'], 
              type=click.Choice(["grid", "sparse", "medium", "very_sparse"]),
              help="水印样式")
@click.option("--segment-height", "-h", default=DEFAULT_WATERMARK['segment_height'], 
              help="每段图片高度")
def cmd_html2jpg(input: Path, batch: bool, watermark: str, style: str, segment_height: int):
    """HTML文件转换为带水印的切分图片"""
    files = []
    if batch:
        files = list_files_in_dir(HTML_INPUT_DIR, [".html"])
    elif input and input.exists():
        files = [input]
    else:
        click.echo("请指定--input单个文件或--batch批量处理")
        return
    
    if not files:
        return
    
    # 初始化处理器
    processor = HTMLToSegmentedImage()
    success_count = 0
    
    try:
        for file in files:
            logger.info(f"\n开始处理: {file}")
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
            
            # 处理文件
            result = processor.process_html(file, **watermark_kwargs)
            if result:
                success_count += 1
                click.echo(f"✅ 成功处理: {file} -> 生成 {result['segment_count']} 个片段")
            else:
                click.echo(f"❌ 处理失败: {file}")
        
        click.echo(f"\n处理完成: 成功 {success_count}/{len(files)} 个文件")
        click.echo(f"输出文件保存在: data/output/segmented")
    
    finally:
        processor.close()

# 5. 完整流程：MHTML -> HTML -> MD -> HTML -> 带水印图片
# @cli.command(name="full-process")
# @click.option("--input", "-i", type=Path, required=True, help="单个MHTML文件路径")
# @click.option("--watermark", "-w", default=DEFAULT_WATERMARK['text'], help="水印文字")
# def cmd_full_process(input: Path, watermark: str):
#     """完整流程：MHTML -> HTML -> MD -> HTML -> 带水印切分图片"""
#     if not input.exists() or input.suffix.lower() not in [".mhtml", ".mht"]:
#         click.echo("请指定有效的MHTML文件")
#         return
    
#     try:
#         logger.info("=== 开始完整流程处理 ===")
        
#         # 1. MHTML -> HTML
#         html1 = convert_mhtml_to_html(input)
#         if not html1:
#             raise Exception("MHTML转HTML失败")
        
#         # 2. HTML -> MD
#         md = convert_html_to_md(html1)
#         if not md:
#             raise Exception("HTML转MD失败")
        
#         # 3. MD -> HTML（美化后）
#         html2 = convert_md_to_html(md)
#         if not html2:
#             raise Exception("MD转HTML失败")
        
#         # 4. HTML -> 带水印图片
#         processor = HTMLToSegmentedImage()
#         result = processor.process_html(html2, watermark_text=watermark)
#         processor.close()
        
#         if result:
#             click.echo("\n🎉 完整流程处理成功！")
#             click.echo(f"📁 最终切分图片: {result['segments_dir']}")
#             click.echo(f"📊 共生成 {result['segment_count']} 个片段")
#         else:
#             raise Exception("HTML转图片失败")
    
#     except Exception as e:
#         logger.error(f"完整流程处理失败: {str(e)}", exc_info=True)
#         click.echo(f"\n❌ 处理失败: {str(e)}")

# 6. Markdown内容清理
@cli.command(name="clean-md")
@click.option("--input", "-i", type=Path, help="单个Markdown文件路径")
@click.option("--batch", is_flag=True, help="批量处理input/md目录下的所有Markdown文件")
@click.option("--remove-image-watermark", is_flag=True, help="同时去除图片水印")
def cmd_clean_md(input: Path, batch: bool, remove_image_watermark: bool):
    """使用本地Ollama模型清理Markdown内容（去除无关内容+图片水印）"""
    files = []
    if batch:
        files = list_files_in_dir(MD_INPUT_DIR, [".md", ".markdown"])
    elif input and input.exists():
        files = [input]
    else:
        click.echo("请指定--input单个文件或--batch批量处理")
        return
    
    success_count = 0
    for file in files:
        try:
            logger.info(f"开始清理Markdown: {file}")
            
            # 读取原始内容
            original_content = file.read_text(encoding='utf-8')
            
            # 使用Ollama清理文本内容
            cleaned_content = clean_markdown_content(original_content, file)
            
            if cleaned_content and cleaned_content != original_content:
                # 保存清理后的内容
                file.write_text(cleaned_content, encoding='utf-8')
                
                # 如果需要去除图片水印
                if remove_image_watermark:
                    # 假设图片在相同目录的images文件夹中
                    images_dir = file.parent / "images"
                    if images_dir.exists():
                        watermark_remover.remove_watermarks_from_md_images(file, images_dir)
                
                success_count += 1
                click.echo(f"✅ 清理成功: {file}")
            else:
                click.echo(f"⚠️ 内容无变化: {file}")
                
        except Exception as e:
            logger.error(f"Markdown清理失败 {file}: {str(e)}", exc_info=True)
            click.echo(f"❌ 清理失败: {file}")
    
    click.echo(f"\n清理完成: 成功 {success_count}/{len(files)} 个文件")

# @cli.command(name="full-process")
# @click.option("--input", "-i", type=Path, required=True, help="单个MHTML文件路径")
# @click.option("--watermark", "-w", default=DEFAULT_WATERMARK['text'], help="水印文字")
# @click.option("--optimize", is_flag=True, help="优化HTML布局用于截图")
# def cmd_full_process(input: Path, watermark: str, optimize: bool):
#     """完整流程：MHTML -> HTML -> MD -> HTML -> 带水印切分图片"""
#     if not input.exists() or input.suffix.lower() not in [".mhtml", ".mht"]:
#         click.echo("请指定有效的MHTML文件")
#         return
    
#     try:
#         logger.info("=== 开始完整流程处理 ===")
        
#         # 1. MHTML -> HTML
#         html1 = convert_mhtml_to_html(input)
#         if not html1:
#             raise Exception("MHTML转HTML失败")
#         # import pdb
#         # pdb.set_trace()
#         # 2. HTML -> MD
#         md = convert_html_to_md(html1)
#         if not md:
#             raise Exception("HTML转MD失败")
#         # pdb.set_trace()
#         # 3. MD -> HTML（美化后）
#         html2 = convert_md_to_html(md)
#         if not html2:
#             raise Exception("MD转HTML失败")
#         # pdb.set_trace()
#         # 4. 可选：优化HTML布局
#         final_html = html2
#         if optimize:
#             from src.processors.html_optimizer import optimize_html_for_screenshot
#             final_html = optimize_html_for_screenshot(html2)
        
#         # 5. HTML -> 带水印图片
#         processor = HTMLToSegmentedImage()
#         result = processor.process_html(final_html, watermark_text=watermark)
#         processor.close()
        
#         if result:
#             click.echo("\n🎉 完整流程处理成功！")
#             click.echo(f"📁 最终切分图片: {result['segments_dir']}")
#             click.echo(f"📊 共生成 {result['segment_count']} 个片段")
#         else:
#             raise Exception("HTML转图片失败")
    
#     except Exception as e:
#         logger.error(f"完整流程处理失败: {str(e)}", exc_info=True)
#         click.echo(f"\n❌ 处理失败: {str(e)}")

@cli.command(name="full-process")
@click.option("--input", "-i", type=Path, required=True, help="单个MHTML文件路径")
@click.option("--watermark", "-w", default=DEFAULT_WATERMARK['text'], help="水印文字")
@click.option("--optimize", is_flag=True, help="优化HTML布局用于截图")
@click.option("--clean-md", is_flag=True, help="清理Markdown内容（去除无关内容）")
@click.option("--remove-image-watermark", is_flag=True, help="去除图片水印")
def cmd_full_process(input: Path, watermark: str, optimize: bool, clean_md: bool, remove_image_watermark: bool):
    """完整流程：MHTML -> HTML -> MD -> [清理MD] -> HTML -> 带水印切分图片"""
    if not input.exists() or input.suffix.lower() not in [".mhtml", ".mht"]:
        click.echo("请指定有效的MHTML文件")
        return
    
    try:
        logger.info("=== 开始完整流程处理 ===")
        
        # 1. MHTML -> HTML
        html1 = convert_mhtml_to_html(input)
        if not html1:
            raise Exception("MHTML转HTML失败")
        
        # 2. HTML -> MD
        md = convert_html_to_md(html1)
        if not md:
            raise Exception("HTML转MD失败")
        
        # 新增：3. 清理Markdown内容
        if clean_md:
            logger.info("=== 开始清理Markdown内容 ===")
            md_content = md.read_text(encoding='utf-8')
            cleaned_content = clean_markdown_content(md_content, md)
            
            if cleaned_content and cleaned_content != md_content:
                md.write_text(cleaned_content, encoding='utf-8')
                logger.info("Markdown内容清理完成")
            
            # 新增：去除图片水印
            if remove_image_watermark:
                logger.info("=== 开始去除图片水印 ===")
                # 假设图片在Markdown文件同级的images目录中
                images_dir = md.parent / "images"
                if images_dir.exists():
                    watermark_remover.remove_watermarks_from_md_images(md, images_dir)
        
        # 4. MD -> HTML（美化后）
        html2 = convert_md_to_html(md)
        if not html2:
            raise Exception("MD转HTML失败")
        
        # 5. 可选：优化HTML布局
        final_html = html2
        if optimize:
            from src.processors.html_optimizer import optimize_html_for_screenshot
            final_html = optimize_html_for_screenshot(html2)
        
        # 6. HTML -> 带水印图片
        processor = HTMLToSegmentedImage()
        result = processor.process_html(final_html, watermark_text=watermark)
        processor.close()
        
        if result:
            click.echo("\n🎉 完整流程处理成功！")
            click.echo(f"📁 最终切分图片: {result['segments_dir']}")
            click.echo(f"📊 共生成 {result['segment_count']} 个片段")
        else:
            raise Exception("HTML转图片失败")
    
    except Exception as e:
        logger.error(f"完整流程处理失败: {str(e)}", exc_info=True)
        click.echo(f"\n❌ 处理失败: {str(e)}")

@cli.command(name="export-md")
@click.option("--input", "-i", type=Path, help="单个HTML/MHTML文件路径")
@click.option("--batch", is_flag=True, help="批量处理：HTML（input/html）、MHTML（input/mhtml）")
def cmd_export_md(input: Path, batch: bool):
    """导出Markdown到工作目录（供手动编辑）：data/working/md/"""
    files = []
    if batch:
        # 批量处理input/html和input/mhtml目录下的所有文件
        html_files = list_files_in_dir(HTML_INPUT_DIR, [".html"])
        mhtml_files = list_files_in_dir(MHTML_INPUT_DIR, [".mhtml", ".mht"])
        files = html_files + mhtml_files
    elif input and input.exists():
        files = [input]
    else:
        click.echo("请指定--input单个文件（HTML/MHTML）或--batch批量处理")
        return
    
    if not files:
        click.echo("未找到可处理的文件")
        return
    
    success_count = 0
    for file in files:
        file = Path(file)
        logger.info(f"\n开始导出: {file}")
        
        try:
            # 步骤1：如果是MHTML，先转HTML
            if file.suffix.lower() in [".mhtml", ".mht"]:
                html_file = convert_mhtml_to_html(file)
                if not html_file:
                    click.echo(f"❌ 导出失败: {file}（MHTML转HTML失败）")
                    continue
            else:
                html_file = file  # 已经是HTML，直接使用
            
            # 步骤2：HTML转MD（输出到工作目录，供手动编辑）
            edited_md_path = get_output_path(file, WORKING_MD_DIR, ".md")
            result = convert_html_to_md(
                html_file=html_file,
                output_md_file=edited_md_path,
                download_images=True
            )
            
            if result:
                success_count += 1
                click.echo(f"✅ 导出成功: {file} -> {edited_md_path}")
            else:
                click.echo(f"❌ 导出失败: {file}（HTML转MD失败）")
        
        except Exception as e:
            logger.error(f"导出MD失败: {str(e)}", exc_info=True)
            click.echo(f"❌ 导出失败: {file}（{str(e)}）")
    
    click.echo(f"\n导出完成: 成功 {success_count}/{len(files)} 个文件")
    click.echo(f"📌 手动编辑Markdown文件后，放入：{WORKING_MD_DIR}")
    click.echo(f"📌 下一步执行：python run.py process-edited-md")

@cli.command(name="process-edited-md")
@click.option("--input", "-i", type=Path, help="单个手动编辑后的MD文件路径（可选）")
@click.option("--batch", is_flag=True, help="批量处理工作目录下的所有MD：data/working/md/")
@click.option("--watermark", "-w", default=DEFAULT_WATERMARK['text'], help="水印文字")
@click.option("--style", "-s", default=DEFAULT_WATERMARK['style'], 
              type=click.Choice(["grid", "sparse", "medium", "very_sparse"]),
              help="水印样式")
@click.option("--segment-height", "-h", default=DEFAULT_WATERMARK['segment_height'], 
              help="每段图片高度")
def cmd_process_edited_md(input: Path, batch: bool, watermark: str, style: str, segment_height: int):
    """处理手动编辑后的Markdown：MD -> HTML -> 带水印切分图片"""
    files = []
    if batch:
        # 批量处理工作目录下的所有MD文件
        files = list_files_in_dir(WORKING_MD_DIR, [".md", ".markdown"])
    elif input and input.exists():
        # 处理单个编辑后的MD文件
        files = [input]
    else:
        click.echo("请指定--input单个编辑后的MD文件或--batch批量处理（data/working/md/）")
        return
    
    if not files:
        click.echo("未找到可处理的编辑后Markdown文件")
        return
    
    # 初始化处理器
    processor = HTMLToSegmentedImage()
    success_count = 0
    
    try:
        for md_file in files:
            md_file = Path(md_file)
            logger.info(f"\n开始处理编辑后的MD: {md_file}")
            
            # 步骤1：MD转HTML（美化后）
            html_file = get_output_path(md_file, HTML_OUTPUT_DIR, ".html")
            html_result = convert_md_to_html(
                md_file=md_file,
                output_html_file=html_file,
                use_extensions=True
            )
            
            if not html_result:
                click.echo(f"❌ 处理失败: {md_file}（MD转HTML失败）")
                continue
            
            # 步骤2：HTML转带水印的切分图片
            watermark_kwargs = {
                'watermark_text': watermark,
                'style': style,
                'segment_height': segment_height
            }
            
            # 水印样式参数
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
            
            # 处理图片
            image_result = processor.process_html(html_result, **watermark_kwargs)
            if image_result:
                success_count += 1
                click.echo(f"✅ 处理成功: {md_file} -> 生成 {image_result['segment_count']} 个片段")
                click.echo(f"   📁 HTML文件: {html_result}")
                click.echo(f"   📁 图片片段: {image_result['segments_dir']}")
            else:
                click.echo(f"❌ 处理失败: {md_file}（HTML转图片失败）")
        
        click.echo(f"\n处理完成: 成功 {success_count}/{len(files)} 个文件")
    
    finally:
        processor.close()

if __name__ == "__main__":
    cli()