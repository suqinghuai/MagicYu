# 导入必要的库
import pyautogui  # 用于屏幕像素检测
import configparser  # 用于读取配置文件

# 初始化配置解析器并读取配置文件
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')


def check_new_message():
    """
    检查是否有新消息
    
    通过检测指定坐标的像素颜色是否与配置文件中定义的颜色匹配来判断是否有新消息
    
    Returns:
        bool: 如果检测到新消息返回True，否则返回False
    """
    try:
        # 从配置文件中读取新消息指示区域的坐标和颜色
        x = int(config['新消息']['横坐标'])
        y = int(config['新消息']['纵坐标'])
        r = int(config['新消息']['红色值'])
        g = int(config['新消息']['绿色值'])
        b = int(config['新消息']['蓝色值'])
        
        # 获取指定坐标的像素颜色
        pixel = pyautogui.pixel(x, y)
        # 比较像素颜色是否与配置的颜色匹配
        result = pixel == (r, g, b)
        print(f"检查新消息: 坐标({x},{y})，期望颜色({r},{g},{b})，实际颜色{pixel}，结果{result}")
        return result
    except Exception as e:
        error_msg = f"检查新消息时出错: {str(e)}"
        print(error_msg)
        # 出错时返回False，避免程序卡死
        return False


def check_product():
    """
    检查当前显示的商品
    
    通过检测不同商品指示区域的像素颜色来判断当前显示的商品
    
    Returns:
        str: 对应商品的提示词，如果没有检测到任何商品则返回默认提示词
    """
    try:
        # 商品列表
        products = ['商品1', '商品2', '商品3', '商品4', '商品5']
        
        # 遍历每个商品进行检查
        for prod in products:
            # 从配置文件中读取商品指示区域的坐标和颜色
            x = int(config[prod]['横坐标'])
            y = int(config[prod]['纵坐标'])
            r = int(config[prod]['红色值'])
            g = int(config[prod]['绿色值'])
            b = int(config[prod]['蓝色值'])
            
            # 检查像素颜色是否匹配
            pixel = pyautogui.pixel(x, y)
            if pixel == (r, g, b):
                # 如果匹配，返回该商品的提示词
                prompt = config[prod]['提示词']
                print(f"检测到商品: {prod}，坐标({x},{y})，颜色{pixel}")
                return prompt
        
        # 如果没有检测到任何商品，返回默认提示词
        default_prompt = config['默认']['提示词']
        print(f"未检测到任何商品，使用默认提示词")
        return default_prompt
    except Exception as e:
        error_msg = f"检查商品时出错: {str(e)}"
        print(error_msg)
        # 出错时返回默认提示词，避免程序卡死
        return config['default']['prompt']