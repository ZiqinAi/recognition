# ocr.py - 通用OCR处理
import base64
import requests

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