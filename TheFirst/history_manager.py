# history_manager.py - 历史记录管理器
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

class HistoryManager:
    def __init__(self, history_file='TheFirst/data/history.json', history_images_dir='TheFirst/static/history'):
        self.history_file = history_file
        self.history_images_dir = history_images_dir
        
        # 确保目录存在
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        os.makedirs(history_images_dir, exist_ok=True)
        
        # 初始化历史文件
        if not os.path.exists(history_file):
            self._save_history([])
    
    def _load_history(self):
        """加载历史记录"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_history(self, history_data):
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def add_record(self, image_path, ocr_result, settings, image_id=None):
        """添加新的历史记录"""
        try:
            # 生成唯一的历史记录ID
            timestamp = datetime.now()
            record_id = timestamp.strftime("%Y%m%d_%H%M%S")
            if image_id:
                record_id += f"_{image_id}"
            
            # 复制图像到历史目录
            original_filename = os.path.basename(image_path)
            file_ext = os.path.splitext(original_filename)[1]
            history_image_filename = f"{record_id}{file_ext}"
            history_image_path = os.path.join(self.history_images_dir, history_image_filename)
            
            # 确保源文件存在再复制
            if os.path.exists(image_path):
                shutil.copy2(image_path, history_image_path)
            else:
                print(f"警告: 源图像文件不存在: {image_path}")
                return None
            
            # 提取OCR文本
            ocr_text = ""
            if ocr_result and 'data' in ocr_result and 'text_lines' in ocr_result['data']:
                text_lines = [line.get('text', '') for line in ocr_result['data']['text_lines']]
                ocr_text = '\n'.join(text_lines)
            
            # 创建历史记录
            record = {
                'id': record_id,
                'timestamp': timestamp.isoformat(),
                'original_filename': original_filename,
                'image_path': f"/static/history/{history_image_filename}",
                'local_image_path': history_image_path,
                'ocr_text': ocr_text,
                'ocr_result': ocr_result,
                'settings': settings,
                'created_date': timestamp.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 加载现有历史记录
            history = self._load_history()
            
            # 添加新记录到开头
            history.insert(0, record)
            
            # 限制历史记录数量（最多保留100条）
            if len(history) > 100:
                # 删除超出的记录及其图像文件
                for old_record in history[100:]:
                    old_image_path = old_record.get('local_image_path')
                    if old_image_path and os.path.exists(old_image_path):
                        try:
                            os.remove(old_image_path)
                        except Exception as e:
                            print(f"删除旧历史图像失败: {e}")
                
                history = history[:100]
            
            # 保存历史记录
            self._save_history(history)
            
            return record_id
            
        except Exception as e:
            print(f"添加历史记录失败: {e}")
            return None
    
    def get_history_list(self, limit=50):
        """获取历史记录列表"""
        try:
            history = self._load_history()
            
            # 返回简化的列表信息
            history_list = []
            for record in history[:limit]:
                history_list.append({
                    'id': record['id'],
                    'timestamp': record['timestamp'],
                    'created_date': record['created_date'],
                    'original_filename': record['original_filename'],
                    'preview_text': record['ocr_text'][:50] + '...' if len(record['ocr_text']) > 50 else record['ocr_text']
                })
            
            return history_list
            
        except Exception as e:
            print(f"获取历史记录列表失败: {e}")
            return []
    
    def get_record_detail(self, record_id):
        """获取指定历史记录的详细信息"""
        try:
            history = self._load_history()
            
            for record in history:
                if record['id'] == record_id:
                    return record
            
            return None
            
        except Exception as e:
            print(f"获取历史记录详情失败: {e}")
            return None
    
    def delete_record(self, record_id):
        """删除指定的历史记录"""
        try:
            history = self._load_history()
            
            # 找到要删除的记录
            record_to_delete = None
            new_history = []
            
            for record in history:
                if record['id'] == record_id:
                    record_to_delete = record
                else:
                    new_history.append(record)
            
            if record_to_delete:
                # 删除关联的图像文件
                image_path = record_to_delete.get('local_image_path')
                if image_path and os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except Exception as e:
                        print(f"删除历史图像文件失败: {e}")
                
                # 保存更新后的历史记录
                self._save_history(new_history)
                return True
            
            return False
            
        except Exception as e:
            print(f"删除历史记录失败: {e}")
            return False
    
    def clear_all_history(self):
        """清空所有历史记录"""
        try:
            # 删除所有历史图像文件
            if os.path.exists(self.history_images_dir):
                for filename in os.listdir(self.history_images_dir):
                    file_path = os.path.join(self.history_images_dir, filename)
                    if os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            print(f"删除历史图像文件失败: {e}")
            
            # 清空历史记录文件
            self._save_history([])
            return True
            
        except Exception as e:
            print(f"清空历史记录失败: {e}")
            return False
    
    def cleanup_orphaned_images(self):
        """清理孤立的图像文件（不在历史记录中的图像）"""
        try:
            history = self._load_history()
            
            # 获取所有历史记录中的图像文件名
            used_images = set()
            for record in history:
                image_path = record.get('local_image_path', '')
                if image_path:
                    used_images.add(os.path.basename(image_path))
            
            # 检查历史图像目录中的所有文件
            if os.path.exists(self.history_images_dir):
                for filename in os.listdir(self.history_images_dir):
                    if filename not in used_images:
                        file_path = os.path.join(self.history_images_dir, filename)
                        if os.path.isfile(file_path):
                            try:
                                os.remove(file_path)
                                print(f"清理孤立图像文件: {filename}")
                            except Exception as e:
                                print(f"清理孤立图像文件失败: {e}")
            
            return True
            
        except Exception as e:
            print(f"清理孤立图像文件失败: {e}")
            return False