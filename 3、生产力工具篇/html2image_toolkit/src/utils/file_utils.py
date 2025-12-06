"""
文件操作工具函数
"""
import os
import shutil
from pathlib import Path
from typing import List, Optional

def list_files_in_dir(directory: Path, extensions: List[str]) -> List[Path]:
    """
    列出目录中指定扩展名的文件
    
    Args:
        directory: 目录路径
        extensions: 扩展名列表（如 [".html", ".htm"]）
    
    Returns:
        List[Path]: 文件路径列表
    """
    if not directory.exists():
        return []
    
    files = []
    for ext in extensions:
        files.extend(directory.glob(f"*{ext}"))
        files.extend(directory.glob(f"*{ext.upper()}"))
    
    return sorted(set(files))

def copy_file_with_structure(source: Path, target_dir: Path) -> Path:
    """
    复制文件并保持目录结构
    
    Args:
        source: 源文件路径
        target_dir: 目标目录
    
    Returns:
        Path: 目标文件路径
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source.name
    
    if source.exists():
        shutil.copy2(source, target)
    
    return target

def safe_delete(path: Path, recursive: bool = False):
    """
    安全删除文件或目录
    
    Args:
        path: 路径
        recursive: 是否递归删除目录
    """
    try:
        if path.is_file():
            path.unlink()
        elif path.is_dir() and recursive:
            shutil.rmtree(path)
    except Exception as e:
        print(f"删除失败 {path}: {e}")

def ensure_directory(path: Path):
    """
    确保目录存在
    
    Args:
        path: 目录路径
    """
    path.mkdir(parents=True, exist_ok=True)

def get_relative_path(source: Path, target: Path) -> Path:
    """
    获取两个路径之间的相对路径
    
    Args:
        source: 源路径
        target: 目标路径
    
    Returns:
        Path: 相对路径
    """
    try:
        return target.relative_to(source.parent)
    except ValueError:
        return target