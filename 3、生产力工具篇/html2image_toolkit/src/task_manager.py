"""
任务管理器 - 负责创建和管理任务目录结构
"""
import shutil
from pathlib import Path
from datetime import datetime
from src.utils.log_utils import logger
from src.config import FINAL_OUTPUT_DIR

class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.tasks = {}
    
    def create_task(self, source_file: Path, task_name: str = None) -> Path:
        """
        创建新任务目录
        
        Args:
            source_file: 源文件路径
            task_name: 任务名称（可选，默认使用文件名）
        
        Returns:
            Path: 任务目录路径
        """
        if task_name is None:
            task_name = source_file.stem
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_dir = FINAL_OUTPUT_DIR / f"{task_name}_{timestamp}"
        
        # 创建标准子目录结构
        subdirs = {
            'html': task_dir / "html",
            'markdown': task_dir / "markdown",
            'images': task_dir / "markdown" / "images",
            'working_md': task_dir / "working_md",
            'segmented': task_dir / "segmented",
            'temp': task_dir / ".temp",
            'source': task_dir / "source"  # 保存原始文件副本
        }
        
        # 创建所有目录
        for dir_path in subdirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 复制源文件到任务目录
        source_copy = subdirs['source'] / source_file.name
        shutil.copy2(source_file, source_copy)
        
        logger.info(f"创建任务目录: {task_dir}")
        
        # 保存任务信息
        self.tasks[task_name] = {
            'task_dir': task_dir,
            'subdirs': subdirs,
            'source_file': str(source_file),
            'source_copy': str(source_copy),
            'created_at': timestamp,
            'status': 'created'
        }
        
        return task_dir
    
    def get_task_info(self, task_name: str) -> dict:
        """获取任务信息"""
        return self.tasks.get(task_name)
    
    def update_task_status(self, task_name: str, status: str, result: dict = None):
        """更新任务状态"""
        if task_name in self.tasks:
            self.tasks[task_name]['status'] = status
            self.tasks[task_name]['last_update'] = datetime.now().strftime("%Y%m%d_%H%M%S")
            if result:
                self.tasks[task_name]['result'] = result
            logger.info(f"任务状态更新: {task_name} -> {status}")
    
    def list_tasks(self) -> list:
        """列出所有任务"""
        return [
            {
                'name': name,
                'dir': info['task_dir'],
                'status': info['status'],
                'created_at': info['created_at']
            }
            for name, info in self.tasks.items()
        ]
    
    def cleanup_task_temp(self, task_name: str):
        """清理任务的临时文件"""
        if task_name in self.tasks:
            temp_dir = self.tasks[task_name]['subdirs']['temp']
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                logger.info(f"清理任务临时文件: {temp_dir}")
    
    def archive_task(self, task_name: str, archive_dir: Path = None):
        """
        归档任务目录（压缩或移动到归档位置）
        
        Args:
            task_name: 任务名称
            archive_dir: 归档目录
        """
        if task_name not in self.tasks:
            logger.error(f"任务不存在: {task_name}")
            return
        
        if archive_dir is None:
            archive_dir = FINAL_OUTPUT_DIR / "archived"
            archive_dir.mkdir(exist_ok=True)
        
        task_dir = self.tasks[task_name]['task_dir']
        archive_path = archive_dir / f"{task_name}.zip"
        
        try:
            # 使用shutil创建zip归档
            shutil.make_archive(
                str(archive_path.with_suffix('')),  # 去除.zip后缀
                'zip',
                task_dir
            )
            logger.info(f"任务归档成功: {archive_path}")
            
            # 标记为已归档
            self.tasks[task_name]['archived'] = True
            self.tasks[task_name]['archive_path'] = str(archive_path)
            
        except Exception as e:
            logger.error(f"任务归档失败: {str(e)}")

# 全局任务管理器实例
task_manager = TaskManager()