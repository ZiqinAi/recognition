# app.py：主应用程序文件，处理用户请求并调用API
# config.py：用于管理配置信息，包括API密钥、用户信息等

from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import base64
import configparser
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from io import BytesIO
import json
import numpy as np
import cv2
import math

app = Flask(__name__)
UPLOAD_FOLDER = 'TheFirst/static/uploads'  # 真实物理路径
WEB_UPLOAD_PREFIX = '/static/uploads'      # 浏览器可访问路径
PROCESSED_FOLDER = 'TheFirst/static/processed'  # 处理后图像存放路径
PREPROCESS_FOLDER = 'TheFirst/static/preprocessed'  # 预处理图像存放路径
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(PREPROCESS_FOLDER, exist_ok=True)

# 用于图片ID管理
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

# 创建全局ID管理器
id_manager = ImageIDManager()

# 配置管理器类
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
                'sharpen': 'true'             # 锐化
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
            'sharpen': self.config['General'].get('sharpen', 'true').lower() == 'true'
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

# 图像预处理类
class ImagePreprocessor:
    @staticmethod
    def preprocess_image(image_path, image_id, preprocess_options):
        """
        预处理图像以提高OCR准确性
        
        参数:
        - image_path: 原始图像路径
        - image_id: 图像ID
        - preprocess_options: 包含预处理选项的字典
            - auto_deskew: 是否自动校正图像倾斜
            - enhance_contrast: 是否增强图像对比度
            - reduce_noise: 是否减少图像噪点
            - sharpen: 是否锐化图像
            
        返回:
        - 预处理后图像的路径
        """
        try:
            # 读取图像
            cv_image = cv2.imread(image_path)
            if cv_image is None:
                # 如果OpenCV无法读取，尝试使用PIL读取并转换
                pil_image = Image.open(image_path)
                cv_image = np.array(pil_image)
                # 如果是RGB格式，需转换为BGR (OpenCV默认格式)
                if len(cv_image.shape) == 3 and cv_image.shape[2] == 3:
                    cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
            
            # 创建预处理图像的文件夹
            preprocess_dir = os.path.join(PREPROCESS_FOLDER, str(image_id))
            os.makedirs(preprocess_dir, exist_ok=True)
            
            # 保存原始图像的灰度版本用于处理
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY) if len(cv_image.shape) == 3 else cv_image.copy()
            
            # 1. 自动校正倾斜 (Deskew)
            if preprocess_options.get('auto_deskew', True):
                gray = ImagePreprocessor._deskew(gray)
                
            # 2. 增强对比度
            if preprocess_options.get('enhance_contrast', True):
                gray = ImagePreprocessor._enhance_contrast(gray)
                
            # 3. 降噪
            if preprocess_options.get('reduce_noise', True):
                gray = ImagePreprocessor._reduce_noise(gray)
                
            # 4. 锐化
            if preprocess_options.get('sharpen', True):
                gray = ImagePreprocessor._sharpen(gray)
                
            # 保存预处理后的图像 (灰度图)
            processed_gray_path = os.path.join(preprocess_dir, "preprocessed_gray.png")
            cv2.imwrite(processed_gray_path, gray)
            
            # 将处理后的灰度图转换回彩色图像 (如果原图是彩色的)
            if len(cv_image.shape) == 3:
                # 对原始彩色图像进行相同的倾斜校正
                if preprocess_options.get('auto_deskew', True):
                    cv_image = ImagePreprocessor._deskew_color(cv_image)
                
                # 其他增强可以选择性应用于彩色图像
                if preprocess_options.get('enhance_contrast', True):
                    cv_image = ImagePreprocessor._enhance_contrast_color(cv_image)
                
                if preprocess_options.get('sharpen', True):
                    cv_image = ImagePreprocessor._sharpen_color(cv_image)
            else:
                # 如果原图是灰度的，将处理后的灰度图转为3通道
                cv_image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            
            # 保存最终处理后的图像 (彩色或灰度)
            processed_image_path = os.path.join(preprocess_dir, "preprocessed.png")
            cv2.imwrite(processed_image_path, cv_image)
            
            return {
                'status': 'success',
                'preprocessed_image_path': f"/static/preprocessed/{image_id}/preprocessed.png",
                'preprocessed_gray_path': f"/static/preprocessed/{image_id}/preprocessed_gray.png",
                'local_path': processed_image_path
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    @staticmethod
    def _deskew(image):
        """校正图像倾斜"""
        # 尝试使用OpenCV的文本倾斜校正
        try:
            # 使用自适应阈值进行二值化，提高边缘清晰度
            thresh = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY_INV, 11, 2)
            
            # 寻找轮廓
            contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            
            # 过滤小轮廓
            contours = [c for c in contours if cv2.contourArea(c) > 100]
            
            if not contours:
                return image
                
            # 计算每个轮廓的最小外接矩形，获取角度
            angles = []
            for cnt in contours:
                rect = cv2.minAreaRect(cnt)
                angle = rect[2]
                
                # 标准化角度到-45到45度
                if angle < -45:
                    angle = 90 + angle
                elif angle > 45:
                    angle = angle - 90
                    
                angles.append(angle)
            
            # 移除异常值并计算平均角度
            if angles:
                angles.sort()
                q1 = angles[len(angles) // 4]
                q3 = angles[3 * len(angles) // 4]
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                filtered_angles = [a for a in angles if lower_bound <= a <= upper_bound]
                
                if filtered_angles:
                    skew_angle = sum(filtered_angles) / len(filtered_angles)
                    
                    # 只有当倾斜明显时才校正
                    if abs(skew_angle) > 0.5:
                        # 获取图像中心点和旋转矩阵
                        (h, w) = image.shape[:2]
                        center = (w // 2, h // 2)
                        
                        # 旋转图像
                        M = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
                        rotated = cv2.warpAffine(image, M, (w, h), 
                                              flags=cv2.INTER_CUBIC, 
                                              borderMode=cv2.BORDER_REPLICATE)
                        return rotated
            
            return image
            
        except Exception:
            # 如果倾斜校正失败，返回原始图像
            return image
    
    @staticmethod
    def _deskew_color(image):
        """校正彩色图像倾斜"""
        try:
            # 先将彩色图像转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 使用自适应阈值进行二值化，提高边缘清晰度
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY_INV, 11, 2)
            
            # 寻找轮廓
            contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            
            # 过滤小轮廓
            contours = [c for c in contours if cv2.contourArea(c) > 100]
            
            if not contours:
                return image
                
            # 计算每个轮廓的最小外接矩形，获取角度
            angles = []
            for cnt in contours:
                rect = cv2.minAreaRect(cnt)
                angle = rect[2]
                
                # 标准化角度到-45到45度
                if angle < -45:
                    angle = 90 + angle
                elif angle > 45:
                    angle = angle - 90
                    
                angles.append(angle)
            
            # 移除异常值并计算平均角度
            if angles:
                angles.sort()
                q1 = angles[len(angles) // 4]
                q3 = angles[3 * len(angles) // 4]
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                filtered_angles = [a for a in angles if lower_bound <= a <= upper_bound]
                
                if filtered_angles:
                    skew_angle = sum(filtered_angles) / len(filtered_angles)
                    
                    # 只有当倾斜明显时才校正
                    if abs(skew_angle) > 0.5:
                        # 获取图像中心点和旋转矩阵
                        (h, w) = image.shape[:2]
                        center = (w // 2, h // 2)
                        
                        # 旋转图像
                        M = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
                        rotated = cv2.warpAffine(image, M, (w, h), 
                                              flags=cv2.INTER_CUBIC, 
                                              borderMode=cv2.BORDER_REPLICATE)
                        return rotated
            
            return image
            
        except Exception:
            # 如果倾斜校正失败，返回原始图像
            return image
    
    @staticmethod
    def _enhance_contrast(image):
        """增强图像对比度"""
        try:
            # 使用CLAHE (对比度受限的自适应直方图均衡)提高对比度
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)
            
            return enhanced
        except Exception:
            return image
    
    @staticmethod
    def _enhance_contrast_color(image):
        """增强彩色图像对比度"""
        try:
            # 将图像转换到LAB色彩空间
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            
            # 分割通道
            l, a, b = cv2.split(lab)
            
            # 对亮度通道应用CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            
            # 合并通道
            enhanced_lab = cv2.merge((cl, a, b))
            
            # 转换回BGR色彩空间
            enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
            
            return enhanced_bgr
        except Exception:
            return image
    
    @staticmethod
    def _reduce_noise(image):
        """降低图像噪点"""
        try:
            # 非局部均值去噪
            denoised = cv2.fastNlMeansDenoising(image, None, h=10, searchWindowSize=21, templateWindowSize=7)
            
            return denoised
        except Exception:
            return image
    
    @staticmethod
    def _sharpen(image):
        """锐化图像"""
        try:
            # 创建锐化核
            kernel = np.array([[-1, -1, -1],
                             [-1,  9, -1],
                             [-1, -1, -1]])
            
            # 应用锐化
            sharpened = cv2.filter2D(image, -1, kernel)
            
            return sharpened
        except Exception:
            return image
    
    @staticmethod
    def _sharpen_color(image):
        """锐化彩色图像"""
        try:
            # 创建锐化核
            kernel = np.array([[-1, -1, -1],
                             [-1,  9, -1],
                             [-1, -1, -1]])
            
            # 应用锐化
            sharpened = cv2.filter2D(image, -1, kernel)
            
            return sharpened
        except Exception:
            return image

# OCR处理器类
class ImageOCRProcessor:
    @staticmethod
    def process_single_image(image_path, api_token, email, image_size, char_ocr, det_mode, return_position, return_choices, version):
        """处理单个图像并返回OCR结果"""
        with open(image_path, 'rb') as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        data = {
            'image': base64_image,
            'token': api_token,
            'email': email,
            'image_size': image_size,
            'char_ocr': char_ocr,
            'det_mode': det_mode,
            'return_position': return_position,
            'return_choices': return_choices,
            'version': version
        }

        try:
            response = requests.post('https://images.kandianguji.com:14141/ocr_api', data=data)
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'响应失败，状态码：{response.status_code}', 'detail': response.text}
        except Exception as e:
            return {'error': f'请求异常：{str(e)}'}

# 图像处理类
class ImageProcessor:
    @staticmethod
    def process_image(image_path, ocr_data, image_id):
        """处理图像，在图像上标记文本区域并返回处理后的图像路径和文字数据"""
        try:
            # 创建处理图像的文件夹
            processed_dir = os.path.join(PROCESSED_FOLDER, str(image_id))
            os.makedirs(processed_dir, exist_ok=True)
            
            image = Image.open(image_path)
            
            # 计算缩放比例
            ocr_height = ocr_data['data']['height']
            ocr_width = ocr_data['data']['width']
            actual_width, actual_height = image.size
            scale_width = ocr_width / actual_width
            scale_height = ocr_height / actual_height
            
            # 在图像上标记文本行
            draw = ImageDraw.Draw(image)
            
            for line in ocr_data['data']['text_lines']:
                (x1, y1), (x3, y3) = line['position'][0], line['position'][2]
                adjusted_x1, adjusted_y1 = int(x1 / scale_width), int(y1 / scale_height)
                adjusted_x3, adjusted_y3 = int(x3 / scale_width), int(y3 / scale_height)
                
                # 确保坐标顺序正确
                adjusted_x1, adjusted_x3 = min(adjusted_x1, adjusted_x3), max(adjusted_x1, adjusted_x3)
                adjusted_y1, adjusted_y3 = min(adjusted_y1, adjusted_y3), max(adjusted_y1, adjusted_y3)
                
                draw.rectangle([adjusted_x1, adjusted_y1, adjusted_x3, adjusted_y3], outline='red', width=3)
            
            # 处理和保存单词裁剪图像
            words_data = []
            word_count = 1  # 单词计数器
            
            for line in ocr_data['data']['text_lines']:
                for word in line.get('words', []):
                    if 'position' in word:
                        word_x1, word_y1, word_x2, word_y2 = word['position']
                        adjusted_word_x1 = int(word_x1 / scale_width)
                        adjusted_word_y1 = int(word_y1 / scale_height)
                        adjusted_word_x2 = int(word_x2 / scale_width)
                        adjusted_word_y2 = int(word_y2 / scale_height)
                        
                        # 确保坐标是有效的
                        adjusted_word_x1 = max(0, min(adjusted_word_x1, actual_width))
                        adjusted_word_y1 = max(0, min(adjusted_word_y1, actual_height))
                        adjusted_word_x2 = max(0, min(adjusted_word_x2, actual_width))
                        adjusted_word_y2 = max(0, min(adjusted_word_y2, actual_height))
                        
                        if adjusted_word_x1 < adjusted_word_x2 and adjusted_word_y1 < adjusted_word_y2:
                            cropped_image = image.crop((adjusted_word_x1, adjusted_word_y1, adjusted_word_x2, adjusted_word_y2))
                            
                            # 使用简单的递增数字作为文件名
                            word_image_filename = f"{word_count}.png"
                            word_count += 1
                            
                            word_image_path = os.path.join(processed_dir, word_image_filename)
                            cropped_image.save(word_image_path)
                            
                            # 为前端访问构建路径
                            web_word_image_path = f"/static/processed/{image_id}/{word_image_filename}"
                            
                            words_data.append({
                                'image': web_word_image_path,
                                'text': word.get('text', ''),
                                'confidence': word.get('confidence', 0)
                            })
            
            # 保存带有标记的整体图像
            processed_image_name = "main.png"  # 主处理图像名称
            processed_image_path = os.path.join(processed_dir, processed_image_name)
            image.save(processed_image_path)
            
            return {
                'processed_image_path': f"/static/processed/{image_id}/{processed_image_name}",
                'words_data': words_data
            }
            
        except Exception as e:
            return {'error': str(e)}

# 路由设置
@app.route('/')
def index():
    """渲染主页"""
    config_manager = ConfigManager()
    settings = config_manager.load_settings()
    return render_template('index.html', settings=settings)

@app.route('/static/<path:path>')
def serve_static(path):
    """提供静态文件"""
    return send_from_directory('static', path)

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    """处理设置的获取和保存"""
    config_manager = ConfigManager()
    
    if request.method == 'POST':
        data = request.json
        settings = {
            'api_token': data.get('api_token', 'f410f863-24d8-4fdb-8383-79616b631bfe'),
            'email': data.get('email', '13399649125'),
            'det_mode': data.get('det_mode', 'sp'),
            'image_size': data.get('image_size', 1024),
            'char_ocr': data.get('char_ocr', True),
            'return_position': data.get('return_position', True),
            'return_choices': data.get('return_choices', True),
            'version': data.get('version', 'default'),
            'preprocess_enabled': data.get('preprocess_enabled', True),
            'auto_deskew': data.get('auto_deskew', True),
            'enhance_contrast': data.get('enhance_contrast', True),
            'reduce_noise': data.get('reduce_noise', True),
            'sharpen': data.get('sharpen', True)
        }
        config_manager.save_settings(settings)
        return jsonify({'status': 'success', 'message': '设置已保存'})
    else:
        settings = config_manager.load_settings()
        return jsonify(settings)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """处理图像上传"""
    if 'image' not in request.files:
        return jsonify({'error': '未找到图像文件'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    # 获取下一个图片ID
    image_id = id_manager.get_next_id()
    
    # 获取文件扩展名
    _, file_extension = os.path.splitext(file.filename)
    
    # 用简单的数字命名文件
    new_filename = f"{image_id}{file_extension}"
    full_path = os.path.join(UPLOAD_FOLDER, new_filename)
    file.save(full_path)
    
    # 返回两个路径：一个用于前端显示，一个用于后端处理
    return jsonify({
        'status': 'success',
        'image_path': os.path.join('/static/uploads', new_filename),  # 用于前端显示的路径
        'full_path': full_path,  # 用于后端处理的完整路径
        'image_id': image_id  # 返回图片ID用于后续处理
    })

@app.route('/api/preprocess', methods=['POST'])
def preprocess_image():
    """处理图像预处理请求"""
    try:
        data = request.json
        image_path = data.get('image_path')
        
        # 更全面的路径处理
        if image_path.startswith('/static/'):
            # 移除开头的斜杠，因为UPLOAD_FOLDER已经包含了static/uploads
            local_path = image_path[1:]  # 移除开头的'/'
            image_path = os.path.join(os.getcwd(), local_path)
        elif image_path.startswith('static/'):
            image_path = os.path.join(os.getcwd(), image_path)
        elif image_path.startswith('TheFirst/'):
            # 处理TheFirst前缀的情况
            image_path = image_path

        # 如果客户端也发送了full_path，直接使用它
        full_path = data.get('full_path')
        if full_path and os.path.exists(full_path):
            image_path = full_path
            
        # 获取图片ID
        image_id = data.get('image_id')
        if not image_id:
            # 如果未提供ID，尝试从路径提取
            filename = os.path.basename(image_path)
            name_without_ext = os.path.splitext(filename)[0]
            try:
                image_id = int(name_without_ext)
            except ValueError:
                # 如果无法从文件名提取ID，生成一个新ID
                image_id = id_manager.get_next_id()
                
        # 获取预处理选项
        preprocess_options = {
            'auto_deskew': data.get('auto_deskew', True),
            'enhance_contrast': data.get('enhance_contrast', True),
            'reduce_noise': data.get('reduce_noise', True),
            'sharpen': data.get('sharpen', True)
        }
        
        # 进行图像预处理
        result = ImagePreprocessor.preprocess_image(image_path, image_id, preprocess_options)
        
        if result['status'] == 'error':
            return jsonify({'error': result['error']}), 400
            
        return jsonify({
            'status': 'success',
            'preprocessed_image': result['preprocessed_image_path'],
            'preprocessed_gray': result['preprocessed_gray_path'],
            'local_path': result['local_path'],
            'image_id': image_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ocr', methods=['POST'])
def process_ocr():
    """处理OCR请求"""
    try:
        data = request.json
        image_path = data.get('image_path')
        use_preprocessed = data.get('use_preprocessed', False)
        preprocess_enabled = data.get('preprocess_enabled', True)
        
        # 更全面的路径处理
        if image_path.startswith('/static/'):
            # 移除开头的斜杠，因为UPLOAD_FOLDER已经包含了static/uploads
            local_path = image_path[1:]  # 移除开头的'/'
            image_path = os.path.join(os.getcwd(), local_path)
        elif image_path.startswith('static/'):
            image_path = os.path.join(os.getcwd(), image_path)
        elif image_path.startswith('TheFirst/'):
            # 处理TheFirst前缀的情况
            image_path = image_path

        # 如果客户端也发送了full_path，直接使用它
        full_path = data.get('full_path')
        if full_path and os.path.exists(full_path):
            image_path = full_path
        
        # 获取图片ID（从路径提取或使用传入的值）
        image_id = data.get('image_id')
        if not image_id:
            # 如果未提供ID，尝试从路径提取
            filename = os.path.basename(image_path)
            name_without_ext = os.path.splitext(filename)[0]
            try:
                image_id = int(name_without_ext)
            except ValueError:
                # 如果无法从文件名提取ID，生成一个新ID
                image_id = id_manager.get_next_id()
        
        # 如果启用预处理且未提供预处理过的图像路径，则对图像进行预处理
        preprocessed_path = data.get('preprocessed_path')
        if preprocess_enabled and not preprocessed_path:
            preprocess_options = {
                'auto_deskew': data.get('auto_deskew', True),
                'enhance_contrast': data.get('enhance_contrast', True),
                'reduce_noise': data.get('reduce_noise', True),
                'sharpen': data.get('sharpen', True)
            }
            
            preprocess_result = ImagePreprocessor.preprocess_image(image_path, image_id, preprocess_options)
            
            if preprocess_result['status'] == 'success':
                # 如果预处理成功且设置使用预处理后的图像，则更新图像路径
                if use_preprocessed:
                    image_path = preprocess_result['local_path']
                    # 将预处理的图像路径返回给前端
                    preprocessed_path = preprocess_result['preprocessed_image_path']
            
        api_token = data.get('api_token', 'f410f863-24d8-4fdb-8383-79616b631bfe')
        email = data.get('email', '13399649125')
        det_mode = data.get('det_mode', 'auto')
        image_size = int(data.get('image_size', 1024))
        char_ocr = data.get('char_ocr', True)
        return_position = data.get('return_position', True)
        return_choices = data.get('return_choices', True)
        version = data.get('version', 'default') 
        
        # 调用OCR处理
        ocr_result = ImageOCRProcessor.process_single_image(
            image_path, api_token, email, image_size, char_ocr, det_mode, return_position, return_choices, version
        )
        
        if 'error' in ocr_result:
            return jsonify(ocr_result), 400
            
        # 处理图像（标记文本行等）并使用图片ID
        processing_result = ImageProcessor.process_image(image_path, ocr_result, image_id)
        
        if 'error' in processing_result:
            return jsonify({'error': processing_result['error']}), 400
            
        # 组合结果
        response = {
            'status': 'success',
            'ocr_result': ocr_result,
            'processed_image': processing_result['processed_image_path'],
            'words_data': processing_result['words_data'],
            'image_id': image_id
        }
        
        # 如果使用了预处理，添加预处理图像路径
        if preprocessed_path:
            response['preprocessed_image'] = preprocessed_path
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # 读取配置文件
    config_manager = ConfigManager()
    settings = config_manager.load_settings()
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=5000, debug=True)
