# baidu_ocr.py - 百度OCR处理
import base64
import json
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError
from flask import request, jsonify

# 百度OCR API 配置
BAIDU_OCR_API_KEY = 'cqdKn7AjEW7o2pxPw9JFPdD6'
BAIDU_OCR_SECRET_KEY = 'Q0Sc4KblFELsl2eslWDXmwdo467V3Lsz' 
BAIDU_OCR_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate"
BAIDU_TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'


def baidu_fetch_token():
    """获取百度OCR的access_token"""
    params = {'grant_type': 'client_credentials',
              'client_id': BAIDU_OCR_API_KEY,
              'client_secret': BAIDU_OCR_SECRET_KEY}
    post_data = urlencode(params).encode('utf-8')
    req = Request(BAIDU_TOKEN_URL, post_data)
    try:
        f = urlopen(req, timeout=5)
        result_str = f.read().decode()
        result = json.loads(result_str)
        return result['access_token']
    except URLError as err:
        print(f"百度OCR获取token失败: {err}")
        return None


def baidu_ocr(image_path):
    """调用百度OCR API"""
    token = baidu_fetch_token()
    if not token:
        return None

    ocr_url = BAIDU_OCR_URL + "?access_token=" + token
    try:
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
        img_base64 = base64.b64encode(image_data).decode()
        params = urlencode({'image': img_base64}).encode('utf-8')
        req = Request(ocr_url, params)
        result_str = urlopen(req).read().decode()
        return json.loads(result_str)
    except Exception as e:
        print(f"百度OCR API 请求失败: {e}")
        return None


def process_baidu_ocr():
    """处理使用百度OCR的OCR请求"""

    data = request.get_json()
    image_path = data.get('full_path')  #  从请求中获取完整路径

    if not image_path:
        return jsonify({'error': '未提供图像路径'}), 400

    ocr_result = baidu_ocr(image_path)

    if ocr_result:
        #  需要根据百度OCR API的返回结果调整以下代码，提取文本行
        text_lines = []
        for result in ocr_result.get('words_result', []):
            text = result.get('words', '')
            #  尝试获取位置信息，根据实际API返回调整
            location = result.get('location', {})  #  或者 'words_location'，请查阅API文档
            #  提取坐标
            x1 = location.get('left', 0)
            y1 = location.get('top', 0)
            x2 = x1 + location.get('width', 0)
            y2 = y1 + location.get('height', 0)
            position = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]

            text_lines.append({'text': text, 'position': position})

        response_data = {
            'ocr_result': {
                'data': {
                    'text_lines': text_lines,
                    'width': ocr_result.get('words_result', [{}])[0].get('width', 1000),  #  使用API返回的宽度
                    'height': ocr_result.get('words_result', [{}])[0].get('height', 1000) #  使用API返回的高度
                }
            },
            'processed_image': data.get('image_path')
        }
        return jsonify(response_data)
    else:
        return jsonify({'error': '百度OCR API 调用失败'}), 500