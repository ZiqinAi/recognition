# process_image.py - 图像处理，用于在图像上标记文本区域
import os
from PIL import Image, ImageDraw

PROCESSED_FOLDER = 'TheFirst/static/processed'  # 处理后图像存放路径

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