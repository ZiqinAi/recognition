# utils.py - 实用工具类
import os

class ImageIDManager:
    def __init__(self, id_file='image_id.txt'):
        self.id_file = id_file
        self.current_id = self._load_id()
    
    def _load_id(self):
        """从文件加载当前ID或创建新ID"""
        if os.path.exists(self.id_file):
            try:
                with open(self.id_file, 'r') as f:
                    return int(f.read().strip()) # 读取当前ID
            except:
                return 1
        return 1
    
    def get_next_id(self):
        """获取下一个ID并保存"""
        self.current_id += 1
        with open(self.id_file, 'w') as f:
            f.write(str(self.current_id))
        return self.current_id