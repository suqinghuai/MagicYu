import os
import sys
import mimetypes
import base64
import configparser
from openai import OpenAI

def get_application_path():
    """
    获取程序的实际运行目录
    
    Returns:
        str: 程序的实际运行目录路径
    """
    if getattr(sys, 'frozen', False):
        # 打包成exe后的情况
        return os.path.dirname(sys.executable)
    else:
        # 开发环境的情况
        return os.path.dirname(os.path.abspath(__file__))

app_path = get_application_path()

config = configparser.ConfigParser()
config_path = os.path.join(app_path, 'config.ini')
config.read(config_path, encoding='utf-8')


def _load_api_config(section_name):
    """
    读取指定API配置段，若不存在则回退到[API]。

    Args:
        section_name (str): 配置段名称，例如“识图API”或“对话API”

    Returns:
        dict: 包含 api_key、base_url、model
    """
    target_section = section_name if section_name in config else 'API'

    if target_section not in config:
        raise KeyError("config.ini 缺少 [API] 配置段")

    section = config[target_section]
    api_key = section.get('API密钥', config.get('API', 'API密钥', fallback='')).strip()
    base_url = section.get('基础URL', config.get('API', '基础URL', fallback='https://api-inference.modelscope.cn/v1/')).strip()
    model = section.get('模型', config.get('API', '模型', fallback='')).strip()

    if not api_key:
        raise ValueError(f"[{target_section}] API密钥 不能为空")
    if not model:
        raise ValueError(f"[{target_section}] 模型 不能为空")

    return {
        'api_key': api_key,
        'base_url': base_url,
        'model': model,
    }


def image_to_data_url(image_path):
    """
    将图片文件转换为Data URL格式
    
    Args:
        image_path (str): 图片文件的路径
        
    Returns:
        str: 转换后的Data URL字符串
        
    Raises:
        FileNotFoundError: 如果图片文件不存在
    """
    try:
        # 检查图片文件是否存在
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # 读取图片文件内容
        with open(image_path, "rb") as f:
            image_data = f.read()

        # 猜测图片的MIME类型
        mime_type, _ = mimetypes.guess_type(image_path)

        # 如果无法确定MIME类型或不是图片类型，默认使用'image/png'
        if mime_type is None or not mime_type.startswith('image/'):
            mime_type = 'image/png'

        # 对图片数据进行base64编码并转换为字符串
        base64_encoded = base64.b64encode(image_data).decode('utf-8')
        # 构建并返回Data URL
        return f"data:{mime_type};base64,{base64_encoded}"
    except Exception as e:
        print(f"转换图片为Data URL时出错: {str(e)}")
        raise


def extract_chat_text_from_image(image_path, product_prompt):
    """
    使用识图模型从聊天截图中提取对话文本。
    
    Args:
        image_path (str): 图片文件的路径
        product_prompt (str): 商品相关提示词，用于帮助模型理解上下文
        
    Returns:
        str: 识别出的聊天文本
    """
    try:
        api_config = _load_api_config('识图API')
        client = OpenAI(
            api_key=api_config['api_key'],
            base_url=api_config['base_url']
        )

        image_url = image_to_data_url(image_path)

        extraction_prompt = (
            "你是OCR助手。请只做一件事：识别聊天截图中的文本并结构化输出。\n"
            "要求：\n"
            "1. 只输出识别到的聊天内容，不要给建议，不要代写回复。\n"
            "2. 尽量按时间顺序输出，每行一条消息，格式：角色: 内容。\n"
            "3. 如果文本不清晰，请在对应位置标记 [不清晰]。\n"
            "4. 可结合商品背景提示理解术语，但不要生成回复。\n"
            f"商品背景提示：{product_prompt}"
        )

        print("正在调用识图模型...")
        response = client.chat.completions.create(
            model=api_config['model'],
            messages=[
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': extraction_prompt,
                        },
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': image_url,
                            },
                        }
                    ],
                }
            ],
            stream=False
        )

        extracted_text = (response.choices[0].message.content or '').strip()
        if not extracted_text:
            raise ValueError("识图模型返回为空")

        return extracted_text
    except Exception as e:
        error_msg = f"调用识图模型时出错: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)


def generate_reply_from_chat_text(chat_text, product_prompt):
    """
    使用对话模型基于聊天文本生成回复。

    Args:
        chat_text (str): 由识图模型提取的聊天文本
        product_prompt (str): 商品相关提示词

    Returns:
        str: 对话模型生成的回复
    """
    try:
        api_config = _load_api_config('对话API')
        client = OpenAI(
            api_key=api_config['api_key'],
            base_url=api_config['base_url']
        )

        dialogue_prompt = (
            "你是青淮的小店客服，请根据下面的聊天记录生成一条可直接发送给顾客的回复。\n"
            "要求：\n"
            "1. 语气自然口语化，像真人客服。\n"
            "2. 简洁明确，不机械不重复。\n"
            "3. 不提及AI、机器人、模型等字样。\n"
            "4. 只输出最终回复内容，不要解释。\n\n"
            f"商品背景提示：{product_prompt}\n\n"
            "聊天记录：\n"
            f"{chat_text}"
        )

        print("正在调用对话模型...")
        response = client.chat.completions.create(
            model=api_config['model'],
            messages=[
                {
                    'role': 'user',
                    'content': dialogue_prompt,
                }
            ],
            stream=False
        )

        final_reply = (response.choices[0].message.content or '').strip()
        if not final_reply:
            raise ValueError("对话模型返回为空")

        return final_reply
    except Exception as e:
        error_msg = f"调用对话模型时出错: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)


def get_ai_response(image_path, prompt):
    """
    兼容旧调用：串联识图模型和对话模型。
    """
    chat_text = extract_chat_text_from_image(image_path, prompt)
    return generate_reply_from_chat_text(chat_text, prompt)