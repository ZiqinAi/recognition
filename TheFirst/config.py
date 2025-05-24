import os
import configparser

class ConfigManager:
    def __init__(self, config_path='config.ini'):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        
        # 如果配置文件存在，加载它
        if os.path.exists(config_path):
            self.config.read(config_path)
        else:
            # 创建默认配置
            self.config['General'] = {
                'api_token': 'f410f863-24d8-4fdb-8383-79616b631bfe',
                'email': '13399649125',
                'det_mode': 'sp',
                'image_size': '1024',
                'char_ocr': 'true',
                'return_position': 'true',
                'return_choices': 'true',
                'version': 'default', # 有beta和default两个版本，beta版本是优化的版本，default版本是默认版本
                'preprocess_enabled': 'true',  # 是否启用图像预处理
                'auto_deskew': 'true',        # 自动校正倾斜
                'enhance_contrast': 'true',   # 增强对比度
                'reduce_noise': 'true',       # 降噪
                'sharpen': 'true',            # 锐化
                'deepseek_api_key': 'sk-9772bfebc0a64bb79058227620f86174'  # DeepSeek API密钥
                
            }
            self.save_settings()
            
    def load_settings(self):
        """从配置文件中加载设置"""
        if not self.config.has_section('General'):
            self.config['General'] = {}
            
        return {
            'api_token': self.config['General'].get('api_token', 'f410f863-24d8-4fdb-8383-79616b631bfe'),
            'email': self.config['General'].get('email', '13399649125'),
            'det_mode': self.config['General'].get('det_mode', 'sp'),
            'image_size': int(self.config['General'].get('image_size', '1024')),
            'char_ocr': self.config['General'].get('char_ocr', 'true').lower() == 'true',
            'return_position': self.config['General'].get('return_position', 'true').lower() == 'true',
            'return_choices': self.config['General'].get('return_choices', 'true').lower() == 'true',
            'version': self.config['General'].get('version', 'default'),
            'preprocess_enabled': self.config['General'].get('preprocess_enabled', 'true').lower() == 'true',
            'auto_deskew': self.config['General'].get('auto_deskew', 'true').lower() == 'true',
            'enhance_contrast': self.config['General'].get('enhance_contrast', 'true').lower() == 'true',
            'reduce_noise': self.config['General'].get('reduce_noise', 'true').lower() == 'true',
            'sharpen': self.config['General'].get('sharpen', 'true').lower() == 'true',
            'deepseek_api_key': self.config['General'].get('deepseek_api_key', '') 
        }
    
    def save_settings(self, settings=None):
        """保存设置到配置文件"""
        if settings:
            if not self.config.has_section('General'):
                self.config.add_section('General')
                
            for key, value in settings.items():
                self.config['General'][key] = str(value)
                
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)