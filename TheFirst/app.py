# app.py - 主应用程序，处理路由和核心逻辑
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from config import ConfigManager
from utils import ImageIDManager
from preprocess import ImagePreprocessor
from ocr import ImageOCRProcessor
from process_image import ImageProcessor
from text_converter import convert_text
from baidu_ocr import process_baidu_ocr
from history_manager import HistoryManager
from deepseek_assistant import deepseek_assistant  # 导入DeepSeek助手
import requests
app = Flask(__name__)

# 定义静态文件路径和初始化
UPLOAD_FOLDER = 'TheFirst/static/uploads'
PROCESSED_FOLDER = 'TheFirst/static/processed'
PREPROCESS_FOLDER = 'TheFirst/static/preprocessed'
HISTORY_IMAGES_DIR = 'TheFirst/static/history'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(PREPROCESS_FOLDER, exist_ok=True)
os.makedirs(HISTORY_IMAGES_DIR, exist_ok=True)

id_manager = ImageIDManager()
history_manager = HistoryManager()  # 初始化历史记录管理器

# 路由
@app.route('/')
def index():
    return render_template('index.html', settings=ConfigManager().load_settings())

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
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
    if 'image' not in request.files:
        return jsonify({'error': '未找到图像文件'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400

    image_id = id_manager.get_next_id()
    _, file_extension = os.path.splitext(file.filename)
    new_filename = f"{image_id}{file_extension}"
    full_path = os.path.join(UPLOAD_FOLDER, new_filename)
    file.save(full_path)

    return jsonify({
        'status': 'success',
        'image_path': os.path.join('/static/uploads', new_filename),
        'full_path': full_path,
        'image_id': image_id
    })

@app.route('/api/preprocess', methods=['POST'])
def preprocess_image_route():
    try:
        data = request.json
        image_path = data.get('image_path')

        # 更全面的路径处理
        if image_path.startswith('/static/'):
            local_path = image_path[1:]
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
    try:
        data = request.json
        image_path = data.get('image_path')
        full_path = data.get('full_path')
        image_id = data.get('image_id')
        det_mode = data.get('det_mode')
        image_size = data.get('image_size')
        char_ocr = data.get('char_ocr')
        version = data.get('version')
        preprocess = data.get('preprocess')
        preprocess_options = data.get('preprocess_options')
        use_preprocessed = data.get('use_preprocessed', False)  # 是否使用预处理后的图像

        # 确定要使用的图像路径
        final_image_path = full_path if full_path and os.path.exists(full_path) else image_path

        # 如果启用了预处理，则进行预处理
        preprocessed_path = None
        if preprocess:
            preprocess_result = ImagePreprocessor.preprocess_image(
                final_image_path, image_id, preprocess_options
            )
            if preprocess_result['status'] == 'error':
                return jsonify({'error': preprocess_result['error']}), 400
            final_image_path = f"TheFirst/{preprocess_result['preprocessed_image_path']}"
            preprocessed_path = f"TheFirst/{preprocess_result['preprocessed_image_path']}"  # 保存预处理后的路径
            if use_preprocessed:
                final_image_path = preprocess_result['local_path']  # 确保使用本地路径

        # 加载设置
        config_manager = ConfigManager()
        settings = config_manager.load_settings()
        api_token = settings.get('api_token')
        email = settings.get('email')
        return_position = settings.get('return_position', True)
        return_choices = settings.get('return_choices', True)

        # 调用OCR处理
        ocr_result = ImageOCRProcessor.process_single_image(
            final_image_path, api_token, email, image_size, char_ocr, det_mode, return_position, return_choices, version
        )

        if 'error' in ocr_result:
            return jsonify(ocr_result), 400

        # 处理图像（标记文本行等）并使用图片ID
        processing_result = ImageProcessor.process_image(final_image_path, ocr_result, image_id)

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
        
        # 保存历史记录
        history_manager.add_record(final_image_path, ocr_result, settings, image_id)

        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/baidu_ocr', methods=['POST'])
def process_baidu_ocr_route():
    return process_baidu_ocr()

@app.route('/api/convert_text', methods=['POST'])
def convert_text_route():
    return convert_text()


# === DeepSeek助手相关路由 ===
@app.route('/api/assistant/chat', methods=['POST'])
def chat_with_assistant():
    """与DeepSeek古文助手对话"""
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        context_text = data.get('context_text', '')
        conversation_history = data.get('conversation_history', [])

        if not user_message:
            return jsonify({'error': '请输入您的问题'}), 400

        # 确保API密钥已配置
        config_manager = ConfigManager()
        settings = config_manager.load_settings()
        deepseek_api_key = settings.get('deepseek_api_key', '')
        
        if deepseek_api_key:
            deepseek_assistant.set_api_key(deepseek_api_key)

        # 调用助手进行对话
        result = deepseek_assistant.chat_with_assistant(
            user_message, 
            context_text, 
            conversation_history
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': f'助手服务错误: {str(e)}'}), 500

# TODO: 其余的四个快捷功能+clear功能
@app.route('/api/assistant/analyze', methods=['POST'])
def analyze_text():
    """对古文进行全面分析"""
    try:
        data = request.json
        ancient_text = data.get('text', '').strip()
        if not ancient_text:
            return jsonify({'error': '请输入需要分析的古文文本'}), 400

        result = deepseek_assistant.analyze_ancient_text(ancient_text)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': f'助手分析服务错误: {str(e)}'}), 500


@app.route('/api/assistant/translate', methods=['POST'])
def translate_text():
    """对古文进行逐句翻译和注释"""
    try:
        data = request.json
        text = data.get('text', '').strip()
        if not text:
            return jsonify({'error': '请输入需要翻译的古文'}), 400

        prompt = f"请对以下古文进行逐句翻译和简要注释：\n\n{text}"
        result = deepseek_assistant.chat_with_assistant(prompt, context_text=text)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': f'助手翻译服务错误: {str(e)}'}), 500


@app.route('/api/assistant/grammar', methods=['POST'])
def grammar_analysis():
    """古文语法结构分析"""
    try:
        data = request.json
        text = data.get('text', '').strip()
        if not text:
            return jsonify({'error': '请输入需要分析的古文'}), 400

        prompt = f"请对以下古文的语法结构进行分析，说明句式、词性、修辞等要素：\n\n{text}"
        result = deepseek_assistant.chat_with_assistant(prompt, context_text=text)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': f'语法分析服务错误: {str(e)}'}), 500


@app.route('/api/assistant/sources', methods=['POST'])
def trace_sources():
    """文献溯源与背景"""
    try:
        data = request.json
        text = data.get('text', '').strip()
        if not text:
            return jsonify({'error': '请输入古文内容'}), 400

        prompt = f"请尝试考证以下古文的文献来源、作者背景、历史语境及相关典故：\n\n{text}"
        result = deepseek_assistant.chat_with_assistant(prompt, context_text=text)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': f'文献溯源服务错误: {str(e)}'}), 500


@app.route('/api/assistant/clear', methods=['POST'])
def clear_conversation():
    """清除对话历史"""
    try:
        # 实际可根据前端存储清除对话记录，此处返回默认空历史
        return jsonify({
            'status': 'success',
            'message': '对话历史已清除',
            'conversation_history': []
        })
    except Exception as e:
        return jsonify({'error': f'清除对话历史时出错: {str(e)}'}), 500


# === 历史记录相关路由 ===
@app.route('/api/history', methods=['GET'])
def get_history():
    """获取历史记录列表"""
    history = history_manager.get_history_list()
    return jsonify(history)

@app.route('/api/history/<record_id>', methods=['GET'])
def get_history_record(record_id):
    """获取特定历史记录的详细信息"""
    record = history_manager.get_record_detail(record_id)
    if record:
        return jsonify(record)
    else:
        return jsonify({'error': '记录未找到'}), 404

@app.route('/api/history/delete/<record_id>', methods=['DELETE'])
def delete_history_record(record_id):
    """删除特定历史记录"""
    if history_manager.delete_record(record_id):
        return jsonify({'status': 'success', 'message': '记录删除成功'})
    else:
        return jsonify({'error': '记录删除失败'}), 404

@app.route('/api/history/clear', methods=['DELETE'])
def clear_history():
    """清除所有历史记录"""
    if history_manager.clear_history():
        return jsonify({'status': 'success', 'message': '历史记录已清除'})
    else:
        return jsonify({'error': '清除历史记录失败'}), 500

    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
