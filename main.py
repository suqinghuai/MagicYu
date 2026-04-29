# 导入必要的库
import time  # 用于时间相关操作
import logging  # 用于日志记录
import os  # 用于文件操作
import sys
import random  # 用于生成随机数，增加操作随机性
import pyautogui  # 用于屏幕截图和鼠标/键盘操作
import pyperclip  # 用于剪贴板操作
from PIL import Image  # 用于图像处理
import configparser  # 用于读取配置文件
from pixel_reader import check_new_message, check_product  # 导入像素检测函数
from ai_copilot import extract_chat_text_from_image, generate_reply_from_chat_text  # 导入AI识图与对话函数

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

# 获取应用路径
app_path = get_application_path()

# 初始化配置解析器并读取配置文件
config = configparser.ConfigParser()
config_path = os.path.join(app_path, 'config.ini')
config.read(config_path, encoding='utf-8')

# 设置日志
import datetime
logs_dir = os.path.join(app_path, 'logs')
if not os.path.exists(logs_dir):  # 检查logs目录是否存在
    os.makedirs(logs_dir)  # 如果不存在则创建
# 生成带时间戳的日志文件名，确保每次运行都生成新的日志文件
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
log_filename = f'magicyu_{timestamp}.log'
log_path = os.path.join(logs_dir, log_filename)
# 配置日志，指定utf-8编码，避免乱码
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    encoding='utf-8'
)
print(f"日志文件已创建: {log_path}")

# 创建统一的日志记录函数
def log_info(message, print_to_console=True):
    """
    统一记录信息日志
    
    Args:
        message (str): 日志消息
        print_to_console (bool): 是否同时打印到控制台
    """
    logging.info(message)
    if print_to_console:
        print(f"[INFO] {message}")

def log_debug(message, print_to_console=True):
    """
    统一记录调试日志
    
    Args:
        message (str): 日志消息
        print_to_console (bool): 是否同时打印到控制台
    """
    logging.debug(message)
    if print_to_console:
        print(f"[DEBUG] {message}")

def log_error(message, print_to_console=True):
    """
    统一记录错误日志
    
    Args:
        message (str): 日志消息
        print_to_console (bool): 是否同时打印到控制台
    """
    logging.error(message)
    if print_to_console:
        print(f"[ERROR] {message}")

def log_warning(message, print_to_console=True):
    """
    统一记录警告日志
    
    Args:
        message (str): 日志消息
        print_to_console (bool): 是否同时打印到控制台
    """
    logging.warning(message)
    if print_to_console:
        print(f"[WARNING] {message}")


def get_random_wait_time(base_time, random_range):
    """
    生成带随机误差的等待时间
    
    Args:
        base_time (float): 基础等待时间
        random_range (float): 随机误差范围（秒）
        
    Returns:
        float: 带随机误差的等待时间
    """
    return base_time + random.uniform(0, random_range)


def get_random_coordinate(base_x, base_y, jitter_range):
    """
    根据基础坐标和抖动范围生成随机坐标
    
    Args:
        base_x (int): 基础X坐标
        base_y (int): 基础Y坐标
        jitter_range (int): 抖动范围（像素）
        
    Returns:
        tuple: (随机X坐标, 随机Y坐标)
    """
    jitter_x = random.randint(-jitter_range, jitter_range)
    jitter_y = random.randint(-jitter_range, jitter_range)
    
    random_x = base_x + jitter_x
    random_y = base_y + jitter_y
    
    return random_x, random_y


def random_mouse_move(start_x, start_y, end_x, end_y, steps=10):
    """
    模拟人类鼠标移动轨迹，直接移动到抖动范围内的随机位置
    
    Args:
        start_x (int): 起始点X坐标
        start_y (int): 起始点Y坐标
        end_x (int): 目标点X坐标
        end_y (int): 目标点Y坐标
        steps (int): 移动步数
    """
    # 计算基础移动向量
    dx = (end_x - start_x) / steps
    dy = (end_y - start_y) / steps
    
    # 添加随机抖动
    for i in range(steps):
        # 计算当前点位置
        current_x = start_x + dx * i
        current_y = start_y + dy * i
        
        # 添加随机偏移（±5像素）
        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-5, 5)
        
        # 移动鼠标到带抖动的位置
        pyautogui.moveTo(current_x + offset_x, current_y + offset_y, duration=0.05)
        
        # 随机微小延迟
        time.sleep(random.uniform(0.01, 0.05))
    
    # 直接停留在抖动位置，不移动到准确位置
    # 这样更符合人类操作习惯，避免风控检测


def random_click(x, y, click_interval, jitter_range=0):
    """
    带随机抖动的鼠标点击，直接移动到抖动范围内的随机位置点击
    
    Args:
        x (int): 目标X坐标
        y (int): 目标Y坐标
        click_interval (float): 基础点击间隔
        jitter_range (int): 点击位置抖动范围（像素）
        
    Returns:
        tuple: (实际等待时间, 实际点击坐标)
    """
    # 如果指定了抖动范围，生成随机坐标
    if jitter_range > 0:
        actual_x, actual_y = get_random_coordinate(x, y, jitter_range)
        print(f"原始坐标: ({x}, {y}), 抖动后坐标: ({actual_x}, {actual_y}), 抖动范围: {jitter_range}像素")
    else:
        actual_x, actual_y = x, y
    
    # 确保坐标在屏幕范围内
    screen_width, screen_height = pyautogui.size()
    actual_x = max(0, min(actual_x, screen_width - 1))
    actual_y = max(0, min(actual_y, screen_height - 1))
    
    # 直接移动到抖动后的随机位置，不经过准确位置
    current_x, current_y = pyautogui.position()
    
    # 模拟人类移动轨迹，直接移动到抖动位置
    dx = (actual_x - current_x) / 10
    dy = (actual_y - current_y) / 10
    
    for i in range(10):
        current_step_x = current_x + dx * i
        current_step_y = current_y + dy * i
        
        # 添加轻微随机偏移
        offset_x = random.randint(-2, 2)
        offset_y = random.randint(-2, 2)
        
        # 确保移动坐标在屏幕范围内
        step_x = max(0, min(current_step_x + offset_x, screen_width - 1))
        step_y = max(0, min(current_step_y + offset_y, screen_height - 1))
        
        pyautogui.moveTo(step_x, step_y, duration=0.03)
        time.sleep(random.uniform(0.01, 0.03))
    
    # 确保最终位置准确
    pyautogui.moveTo(actual_x, actual_y, duration=0.1)
    
    # 随机等待时间
    wait_time = get_random_wait_time(click_interval, 1.0)  # 1秒内随机抖动
    time.sleep(wait_time)
    
    # 点击
    pyautogui.click()
    
    return wait_time, (actual_x, actual_y)


def screenshot_chat():
    """
    截取聊天区域的截图
    
    Returns:
        str: 保存的截图文件路径
    """
    # 从配置文件中读取聊天区域的坐标和尺寸
    x = int(config['坐标']['聊天区域横坐标'])
    y = int(config['坐标']['聊天区域纵坐标'])
    w = int(config['坐标']['聊天区域宽度'])
    h = int(config['坐标']['聊天区域高度'])
    
    # 截取指定区域的屏幕
    screenshot = pyautogui.screenshot(region=(x, y, w, h))
    
    # 创建images文件夹
    images_dir = os.path.join(app_path, config['设置']['截图保存路径'])
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    
    # 按时间命名截图文件
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    filename = f'chat_screenshot_{timestamp}.png'
    path = os.path.join(images_dir, filename)
    
    # 保存截图
    screenshot.save(path)
    print(f"截图已保存到: {path}")
    
    # 返回截图路径
    return path

def main():
    """
    主函数，程序的核心逻辑
    """
    try:
        # 从配置文件中读取设置和坐标
        check_interval = int(config['设置']['检查间隔'])  # 检查间隔（秒）
        click_interval = float(config['设置']['点击间隔'])  # 点击间隔（秒）
        buffer_time = float(config['设置']['缓冲时间'])  # 缓冲时间（秒）
        refresh_interval = int(config['设置']['刷新间隔'])  # 刷新间隔（秒）
        dialog_x = int(config['坐标']['对话框横坐标'])  # 对话框点击坐标X
        dialog_y = int(config['坐标']['对话框纵坐标'])  # 对话框点击坐标Y
        input_x = int(config['坐标']['输入框横坐标'])  # 输入框点击坐标X
        input_y = int(config['坐标']['输入框纵坐标'])  # 输入框点击坐标Y
        send_x = int(config['坐标']['发送按钮横坐标'])  # 发送按钮坐标X
        send_y = int(config['坐标']['发送按钮纵坐标'])  # 发送按钮坐标Y
        blank_x = int(config['坐标']['空白区域横坐标'])  # 空白区域坐标X（用于回到初始状态）
        blank_y = int(config['坐标']['空白区域纵坐标'])  # 空白区域坐标Y
        clear_msg_x = int(config['坐标']['清除未读消息按钮横坐标'])  # 清除未读消息按钮坐标X
        clear_msg_y = int(config['坐标']['清除未读消息按钮纵坐标'])  # 清除未读消息按钮坐标Y
        confirm_clear_x = int(config['坐标']['确认清除按钮横坐标'])  # 确认清除按钮坐标X
        confirm_clear_y = int(config['坐标']['确认清除按钮纵坐标'])  # 确认清除按钮坐标Y
        refresh_x = int(config['坐标']['刷新按钮横坐标'])  # 刷新按钮坐标X
        refresh_y = int(config['坐标']['刷新按钮纵坐标'])  # 刷新按钮坐标Y
        
        # 读取点击位置随机抖动范围
        dialog_jitter = int(config['点击抖动']['对话框抖动范围'])  # 对话框抖动范围
        input_jitter = int(config['点击抖动']['输入框抖动范围'])  # 输入框抖动范围
        send_jitter = int(config['点击抖动']['发送按钮抖动范围'])  # 发送按钮抖动范围
        blank_jitter = int(config['点击抖动']['空白区域抖动范围'])  # 空白区域抖动范围
        clear_msg_jitter = int(config['点击抖动']['清除未读消息按钮抖动范围'])  # 清除未读消息按钮抖动范围
        confirm_clear_jitter = int(config['点击抖动']['确认清除按钮抖动范围'])  # 确认清除按钮抖动范围
        refresh_jitter = int(config['点击抖动']['刷新按钮抖动范围'])  # 刷新按钮抖动范围
        
        print(f"点击抖动配置 - 对话框: {dialog_jitter}像素, 输入框: {input_jitter}像素, 发送按钮: {send_jitter}像素, 空白区域: {blank_jitter}像素")
        
        # 读取点击位置随机抖动范围
        dialog_jitter = int(config['点击抖动']['对话框抖动范围'])  # 对话框抖动范围
        input_jitter = int(config['点击抖动']['输入框抖动范围'])  # 输入框抖动范围
        send_jitter = int(config['点击抖动']['发送按钮抖动范围'])  # 发送按钮抖动范围
        blank_jitter = int(config['点击抖动']['空白区域抖动范围'])  # 空白区域抖动范围
        
        print(f"点击抖动配置 - 对话框: {dialog_jitter}像素, 输入框: {input_jitter}像素, 发送按钮: {send_jitter}像素, 空白区域: {blank_jitter}像素")

        log_info("程序启动")
        log_info(f"检查间隔: {check_interval}秒")
        log_info(f"点击间隔: {click_interval}秒")
        log_info(f"缓冲时间: {buffer_time}秒")
        log_info(f"刷新间隔: {refresh_interval}秒")
        log_info(f"点击抖动配置 - 对话框: {dialog_jitter}像素, 输入框: {input_jitter}像素, 发送按钮: {send_jitter}像素, 空白区域: {blank_jitter}像素, 清除未读消息: {clear_msg_jitter}像素, 确认清除: {confirm_clear_jitter}像素, 刷新按钮: {refresh_jitter}像素")
        
        # 初始化上次刷新时间
        last_refresh_time = time.time()
        
        # 无限循环，持续监控
        while True:
            try:
                log_info("检查新消息...")
                # 检查是否有新消息
                if check_new_message():
                    log_info("检测到新消息")
                    log_info("开始处理新消息流程...")
                    start_processing_time = time.time()
                    
                    # 发现新消息后随机等待1-3秒
                    wait_after_detection = random.uniform(1.0, 3.0)
                    log_info(f"发现新消息，随机等待 {wait_after_detection:.2f} 秒...")
                    time.sleep(wait_after_detection)
                    
                    # 点击对话框（带随机抖动）
                    log_info(f"点击对话框: ({dialog_x}, {dialog_y})")
                    actual_click_interval, actual_coords = random_click(dialog_x, dialog_y, click_interval, dialog_jitter)
                    log_info(f"实际点击间隔: {actual_click_interval:.2f} 秒, 实际点击坐标: {actual_coords}")
                    log_debug(f"对话框抖动范围: {dialog_jitter}像素")
                    
                    # 增加缓冲时间，确保界面完全加载（带3秒内随机抖动）
                    actual_buffer_time = get_random_wait_time(buffer_time, 3.0)
                    log_info(f"等待{actual_buffer_time:.2f}秒缓冲时间，确保界面完全加载...")
                    time.sleep(actual_buffer_time)
                    
                    # 检查商品信息并生成提示词
                    log_info("检查商品信息...")
                    product_prompt = check_product()
                    log_info(f"商品提示词: {product_prompt}")
                    
                    # 截取聊天区域的截图
                    log_info("截取聊天区域截图...")
                    image_path = screenshot_chat()
                    log_info(f"截图保存到: {image_path}")
                    
                    # 第一阶段：识图模型提取聊天文本
                    log_info("调用识图模型提取聊天文本...")
                    chat_text = extract_chat_text_from_image(image_path, product_prompt)
                    log_info(f"识图结果: {chat_text}")

                    # 第二阶段：对话模型基于文本生成回复
                    log_info("调用对话模型生成回复...")
                    response = generate_reply_from_chat_text(chat_text, product_prompt)
                    log_info(f"AI回复: {response}")
                    log_debug(f"原始回复长度: {len(response)} 字符")
                    # 点击输入框激活（带随机抖动）
                    log_info(f"点击输入框: ({input_x}, {input_y})")
                    actual_click_interval, actual_coords = random_click(input_x, input_y, click_interval, input_jitter)
                    log_info(f"实际点击间隔: {actual_click_interval:.2f} 秒, 实际点击坐标: {actual_coords}")
                    log_debug(f"输入框抖动范围: {input_jitter}像素")
                    
                    # 处理AI回复中的转义字符
                    log_info("处理AI回复内容...")
                    # 替换可能导致问题的转义字符
                    processed_response = response.replace('\n', ' ').replace('\r', ' ').strip()
                    log_info(f"处理后的回复: {processed_response}")
                    log_debug(f"处理后回复长度: {len(processed_response)} 字符")
                    
                    # 使用剪贴板方式输入内容
                    log_info("使用剪贴板输入回复内容...")
                    try:
                        # 将处理后的回复复制到剪贴板
                        pyperclip.copy(processed_response)
                        log_info("已复制到剪贴板")
                        log_debug(f"剪贴板内容长度: {len(processed_response)} 字符")
                        
                        # 点击输入框确保激活（带随机抖动）
                        actual_click_interval, actual_coords = random_click(input_x, input_y, click_interval, input_jitter)
                        log_info(f"实际点击间隔: {actual_click_interval:.2f} 秒, 实际点击坐标: {actual_coords}")
                        
                        # 使用Ctrl+V粘贴内容
                        pyautogui.hotkey('ctrl', 'v')
                        log_info("已粘贴到输入框")
                        
                        # 随机等待时间
                        wait_time = get_random_wait_time(click_interval, 0.5)
                        time.sleep(wait_time)
                        log_info(f"粘贴后等待 {wait_time:.2f} 秒")
                    except Exception as e:
                        log_error(f"使用剪贴板输入时出错: {str(e)}")
                        # fallback到逐字符输入
                        log_warning("fallback到逐字符输入...")
                        log_debug(f"开始逐字符输入，共 {len(processed_response)} 个字符")
                        for i, char in enumerate(processed_response):
                            pyautogui.typewrite(char)
                            time.sleep(0.05)
                            if i % 20 == 0:  # 每20个字符记录一次进度
                                log_debug(f"已输入 {i+1}/{len(processed_response)} 个字符")
                    # 点击发送按钮（带随机抖动）
                    log_info(f"点击发送按钮: ({send_x}, {send_y})")
                    actual_click_interval, actual_coords = random_click(send_x, send_y, click_interval, send_jitter)
                    log_info(f"实际点击间隔: {actual_click_interval:.2f} 秒, 实际点击坐标: {actual_coords}")
                    log_debug(f"发送按钮抖动范围: {send_jitter}像素")
                    
                    # 点击空白区域，回到初始状态（带随机抖动）
                    log_info(f"点击空白区域: ({blank_x}, {blank_y})")
                    actual_click_interval, actual_coords = random_click(blank_x, blank_y, click_interval, blank_jitter)
                    log_info(f"实际点击间隔: {actual_click_interval:.2f} 秒, 实际点击坐标: {actual_coords}")
                    log_debug(f"空白区域抖动范围: {blank_jitter}像素")
                    
                    # 等待2-3秒随机时间，确保界面稳定
                    wait_before_clear = random.uniform(2.0, 3.0)
                    log_info(f"等待 {wait_before_clear:.2f} 秒后点击清除未读消息按钮...")
                    time.sleep(wait_before_clear)
                    
                    # 点击清除未读消息按钮（带随机抖动）
                    log_info(f"点击清除未读消息按钮: ({clear_msg_x}, {clear_msg_y})")
                    actual_click_interval, actual_coords = random_click(clear_msg_x, clear_msg_y, click_interval, clear_msg_jitter)
                    log_info(f"实际点击间隔: {actual_click_interval:.2f} 秒, 实际点击坐标: {actual_coords}")
                    log_debug(f"清除未读消息按钮抖动范围: {clear_msg_jitter}像素")
                    
                    # 等待2-3秒随机时间，确保清除对话框弹出
                    wait_before_confirm = random.uniform(2.0, 3.0)
                    log_info(f"等待 {wait_before_confirm:.2f} 秒后点击确认清除按钮...")
                    time.sleep(wait_before_confirm)
                    
                    # 点击确认清除按钮（带随机抖动）
                    log_info(f"点击确认清除按钮: ({confirm_clear_x}, {confirm_clear_y})")
                    actual_click_interval, actual_coords = random_click(confirm_clear_x, confirm_clear_y, click_interval, confirm_clear_jitter)
                    log_info(f"实际点击间隔: {actual_click_interval:.2f} 秒, 实际点击坐标: {actual_coords}")
                    log_debug(f"确认清除按钮抖动范围: {confirm_clear_jitter}像素")
                    
                    log_info("回复完成，清除未读消息，回到初始状态")
                    log_info(f"本次消息处理总耗时: {time.time() - start_processing_time:.2f} 秒")
                    # 根据配置决定是否删除临时截图
                    auto_clean = config['设置']['自动清除截图'].strip().lower() == '是'
                    if auto_clean and os.path.exists(image_path):
                        os.remove(image_path)
                        log_info(f"已删除临时截图: {image_path}")
                    elif not auto_clean:
                        log_info(f"截图已保存，未自动删除: {image_path}")
                else:
                    log_info("未检测到新消息")
                    log_debug("继续监控中...")
                
                # 检查是否需要执行定时刷新
                current_time = time.time()
                time_since_last_refresh = current_time - last_refresh_time
                
                if time_since_last_refresh >= refresh_interval:
                    log_info(f"距离上次刷新已过 {time_since_last_refresh:.2f} 秒，执行定时刷新...")
                    
                    # 点击刷新按钮（带随机抖动）
                    log_info(f"点击刷新按钮: ({refresh_x}, {refresh_y})")
                    actual_click_interval, actual_coords = random_click(refresh_x, refresh_y, click_interval, refresh_jitter)
                    log_info(f"实际点击间隔: {actual_click_interval:.2f} 秒, 实际点击坐标: {actual_coords}")
                    log_debug(f"刷新按钮抖动范围: {refresh_jitter}像素")
                    
                    # 等待刷新完成（带随机抖动）
                    refresh_wait_time = get_random_wait_time(3.0, 2.0)
                    log_info(f"等待 {refresh_wait_time:.2f} 秒让刷新操作完成...")
                    time.sleep(refresh_wait_time)
                    
                    # 更新上次刷新时间
                    last_refresh_time = current_time
                    log_info(f"刷新完成，下次刷新将在 {refresh_interval} 秒后执行")
                
                # 等待检查间隔（带6秒随机误差）
                actual_check_interval = get_random_wait_time(check_interval, 6.0)
                log_info(f"等待 {actual_check_interval:.2f} 秒后再次检查...")
                time.sleep(actual_check_interval)
            except Exception as e:
                error_msg = f"处理消息时出错: {str(e)}"
                log_error(error_msg)
                # 记录详细的错误信息
                import traceback
                error_details = traceback.format_exc()
                log_error(f"错误详情:\n{error_details}", print_to_console=False)
                # 继续循环，不因为错误而停止程序
                time.sleep(check_interval)
    except Exception as e:
        error_msg = f"程序初始化失败: {str(e)}"
        log_error(error_msg)
        import traceback
        error_details = traceback.format_exc()
        log_error(f"初始化错误详情:\n{error_details}", print_to_console=False)
        raise

# 程序入口
if __name__ == "__main__":
    main()