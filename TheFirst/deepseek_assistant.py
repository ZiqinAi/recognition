# deepseek_assistant.py - DeepSeek大模型API助手模块
import requests
import json
from flask import jsonify
import logging

class DeepSeekAssistant:
    def __init__(self, api_key=None, base_url="https://api.deepseek.com/v1/chat/completions"):
        """
        初始化DeepSeek助手

        Args:
            api_key (str): DeepSeek API密钥
            base_url (str): API基础URL
        """
        self.api_key = "sk-9772bfebc0a64bb79058227620f86174"  
        self.base_url = base_url
        self.system_prompt = """你是一位精通古代汉语和传统文献的专业学者助手。你的专长包括：

1. 古代汉语语法和词汇解释
2. 古籍文献的版本考据和文本校勘
3. 古代文化背景和历史语境分析
4. 诗词韵律和文学修辞手法
5. 传统文献的内容解读和注释

请用简洁明了的现代汉语回答问题，必要时可以引经据典。对于识别出的古文内容，你可以提供：
- 字词解释和读音
- 句子翻译和注释
- 文献来源和背景介绍
- 相关典故和引申含义
- 文本校勘建议（如发现明显错误）

请保持学术严谨性，如果遇到不确定的内容，请如实说明。"""

    def set_api_key(self, api_key):
        """设置API密钥"""
        self.api_key = api_key

    def chat_with_assistant(self, user_message, context_text="", conversation_history=None):
        """
        与DeepSeek助手对话

        Args:
            user_message (str): 用户提问
            context_text (str): 识别出的古文文本作为上下文
            conversation_history (list): 对话历史记录

        Returns:
            dict: 包含助手回复的结果
        """
        try:
            # 构建消息列表
            messages = [{"role": "system", "content": self.system_prompt}]

            # 如果有上下文文本，添加到对话中
            if context_text.strip():
                context_message = f"以下是通过OCR识别出的古代文献内容，可能存在识别错误，其中如有太过于明显的识别错误，指出并提供可能的正确字词，请作为参考：\n\n{context_text}"
                messages.append({"role": "user", "content": context_message})
                messages.append({"role": "assistant", "content": "我已经了解了这段古文内容，请问您想了解什么？"})

            # 添加对话历史
            if conversation_history:
                messages.extend(conversation_history)

            # 添加当前用户消息
            messages.append({"role": "user", "content": user_message})

            # 调用DeepSeek API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 2000,
                "top_p": 0.9
            }

            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                assistant_reply = result['choices'][0]['message']['content']

                return {
                    'status': 'success',
                    'reply': assistant_reply,
                    'usage': result.get('usage', {})
                }
            else:
                error_info = response.json() if response.headers.get('content-type') == 'application/json' else {'error': response.text}
                return {
                    'error': f'API调用失败 (状态码: {response.status_code})',
                    'details': error_info
                }

        except requests.exceptions.Timeout:
            return {'error': 'API调用超时，请稍后重试'}
        except requests.exceptions.RequestException as e:
            return {'error': f'网络请求错误: {str(e)}'}
        except Exception as e:
            logging.error(f"DeepSeek助手错误: {str(e)}")
            return {'error': f'助手服务错误: {str(e)}'}

    def analyze_ancient_text(self, text):
        """
        专门分析古代文本的方法

        Args:
            text (str): 古代文本

        Returns:
            dict: 分析结果
        """
        analysis_prompt = f"""请对以下古代文本进行全面分析：

{text}

请从以下几个方面进行分析：
1. 逐句翻译和注释
2. 重点字词解释
3. 语法结构分析
4. 可能的文献来源或类似文献
5. 历史文化背景
6. 如有明显的OCR识别错误，请指出并提供可能的正确字词

请用清晰的结构化格式回答。"""

        return self.chat_with_assistant(analysis_prompt, text)

# 单例模式的助手实例
deepseek_assistant = DeepSeekAssistant()

# # 测试函数
# def test_deepseek_api():
#     """测试DeepSeek API的调用和回复"""
#     # 确保设置了API密钥
#     # if not deepseek_assistant.api_key:  # 这行也不再需要了
#     #     print("请先设置DeepSeek API密钥 (通过环境变量 DEEPSEEK_API_KEY 或直接在代码中设置)。")
#     #     return

#     try:
#         # 简单提问测试
#         user_question = "请解释一下'学而时习之，不亦说乎'这句话。"
#         response = deepseek_assistant.chat_with_assistant(user_question)
#         print(f"问题：{user_question}")
#         if response and response.get('status') == 'success':
#             print(f"回答：{response['reply']}")
#         else:
#             print(f"调用失败：{response.get('error')}, 详细信息: {response.get('details')}")

#         print("\n" + "="*30 + "\n")

#         # 带有上下文的提问测试
#         context = "子曰：“学而时习之，不亦说乎？有朋自远方来，不亦乐乎？人不知而不愠，不亦君子乎？”"
#         user_question_with_context = "这段话出自哪里？"
#         response_with_context = deepseek_assistant.chat_with_assistant(user_question_with_context, context)
#         print(f"上下文：\n{context}")
#         print(f"问题：{user_question_with_context}")
#         if response_with_context and response_with_context.get('status') == 'success':
#             print(f"回答：{response_with_context['reply']}")
#         else:
#             print(f"调用失败：{response_with_context.get('error')}, 详细信息: {response_with_context.get('details')}")

#         print("\n" + "="*30 + "\n")

#         # 古文分析测试
#         ancient_text = "逝者如斯夫，不舍昼夜。"
#         analysis_response = deepseek_assistant.analyze_ancient_text(ancient_text)
#         print(f"分析古文：\n{ancient_text}")
#         if analysis_response and analysis_response.get('status') == 'success':
#             print(f"分析结果：\n{analysis_response['reply']}")
#         else:
#             print(f"分析失败：{analysis_response.get('error')}, 详细信息: {analysis_response.get('details')}")

#     except Exception as e:
#         print(f"测试过程中发生错误: {e}")

# if __name__ == "__main__":
#     test_deepseek_api()