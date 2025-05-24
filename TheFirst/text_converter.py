# text_converter.py - 文本繁简体转换
from opencc import OpenCC
from flask import jsonify, request

def convert_text():
    """处理文本繁简体转换请求"""
    try:
        data = request.json
        text_to_convert = data.get('text')
        conversion_type = data.get('type')  # 's2t' (简转繁) or 't2s' (繁转简)

        if not text_to_convert:
            return jsonify({'error': '没有提供文本'}), 400
        if conversion_type not in ['s2t', 't2s']:
            return jsonify({'error': '无效的转换类型'}), 400

        if conversion_type == 's2t':
            converter = OpenCC('s2t.json') # 简体到繁体 (台灣正體)
            # 如果需要香港繁体，可以使用 's2hk.json'
            # 如果需要传统繁体（OpenCC标准），可以使用 's2twp.json' 加上 'tw2t.json' (s2tw.json -> s2t.json in new versions)
        else: # t2s
            converter = OpenCC('t2s.json') # 繁体到简体

        converted_text = converter.convert(text_to_convert)
        
        return jsonify({
            'status': 'success',
            'original_text': text_to_convert,
            'converted_text': converted_text,
            'conversion_type': conversion_type
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500