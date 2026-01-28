import PIL.Image
import google.generativeai as genai
import os

# 配置 Gemini API (需在 Google AI Studio 获取 API Key)
genai.configure(api_key="st.secrets["GEMINI_API_KEY"]")

def generate_outpainted_asset(source_image_path, target_size=(1080, 1920)):
    """
    使用 AI 扩展图片背景以适配 Facebook 版位
    """
    # 1. 加载原图
    source_img = PIL.Image.open(source_image_path)
    src_w, src_h = source_img.size
    
    # 2. 创建目标画布并居中原图
    # 这一步是为了生成一张带有空白边缘的参考图交给 AI
    canvas = PIL.Image.new("RGB", target_size, (255, 255, 255))
    offset = ((target_size[0] - src_w) // 2, (target_size[1] - src_h) // 2)
    canvas.paste(source_img, offset)
    
    # 3. 调用 Gemini 1.5 Pro 或 Imagen 进行二次创作
    # 注意：Gemini 目前支持通过 Multimodal Prompt 理解图片并指导生成
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    prompt = f"""
    这是一张原始图片素材，我将其放置在了一个 {target_size[0]}x{target_size[1]} 的画布中央。
    请分析原图的视觉风格、光影、纹理和主体元素。
    任务：
    1. 保持画布中心的原图内容完全不变。
    2. 自动扩展并填充四周的白色空白区域。
    3. 填充内容必须与原图无缝衔接，风格保持高度一致。
    4. 确保输出符合 Facebook 广告版位的审美。
    """
    
    # 在实际应用中，如果是调用 Imagen 模型（通过 Vertex AI），
    # 你会发送原始图 + 遮罩图 (Mask)
    # 以下为逻辑演示：
    response = model.generate_content([prompt, source_img])
    
    # 注意：Gemini API 直接返回图像的功能在不同区域的权限不同
    # 通常在 App 开发中，我们会通过 Vertex AI 的 Imagen API 进行 Outpainting
    return response.text # 或者返回生成的图像对象

# --- App 批量处理逻辑 ---
def batch_process_for_fb(image_list, placements):
    """
    placements: {'Stories': (1080, 1920), 'Feed': (1080, 1080)}
    """
    for img_path in image_list:
        for p_name, size in placements.items():
            print(f"正在为 {img_path} 生成 AI 扩展版位: {p_name}...")
            # 调用上面的 AI 函数
            # result = generate_outpainted_asset(img_path, size)
            # result.save(f"output_{p_name}_{img_path}")
