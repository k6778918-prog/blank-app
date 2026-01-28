import streamlit as st
import PIL.Image
import google.generativeai as genai
import io

# --- 1. 配置与初始化 ---
st.set_page_config(page_title="AI FB 素材扩展器", layout="wide")

# 修复之前的引号语法错误
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("未在 Secrets 中找到 GEMINI_API_KEY，请检查设置。")

# Facebook 版位尺寸参考
FB_SIZES = {
    "Stories/Reels (9:16)": (1080, 1920),
    "Feed (1:1)": (1080, 1080),
    "Feed/Ads (4:5)": (1080, 1350)
}

# --- 2. 核心 AI 逻辑函数 ---
def generate_ai_description(source_img, target_size):
    """
    使用 Gemini 分析图片并生成用于 Outpainting 的二次创作描述
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    分析这张图片的内容。如果我要将它放在一个 {target_size[0]}x{target_size[1]} 的画布中央，
    并自动扩展边缘空白区域，请描述应该补充什么内容以保持风格统一。
    请以“补充内容建议：”开头。
    """
    response = model.generate_content([prompt, source_img])
    return response.text

# --- 3. Streamlit UI 界面渲染 ---
st.title("🚀 AI Facebook 素材自动扩展与预览")
st.write("上传图片，AI 将分析并模拟如何二次创作不同尺寸的版位。")

# 侧边栏设置
with st.sidebar:
    st.header("参数设置")
    selected_placements = st.multiselect(
        "选择版位", 
        list(FB_SIZES.keys()), 
        default=["Stories/Reels (9:16)"]
    )

# 文件上传
uploaded_file = st.file_uploader("上传原始图片素材", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    # 展示原图
    source_img = PIL.Image.open(uploaded_file)
    st.subheader("✅ 原图已上传")
    st.image(source_img, width=300)

    if st.button("执行 AI 风格分析与尺寸扩展预览"):
        # 创建多列预览
        cols = st.columns(len(selected_placements))
        
        for idx, p_name in enumerate(selected_placements):
            with cols[idx]:
                st.write(f"**{p_name}**")
                target_size = FB_SIZES[p_name]
                
                # 模拟处理：1. 缩放居中预览
                # 这里目前使用 Python 先渲染一个预览图给用户看
                canvas = PIL.Image.new("RGB", target_size, (240, 240, 240)) # 灰色背景模拟空白
                img_copy = source_img.copy()
                img_copy.thumbnail((target_size[0], target_size[1]))
                offset = ((target_size[0] - img_copy.width) // 2, (target_size[1] - img_copy.height) // 2)
                canvas.paste(img_copy, offset)
                
                st.image(canvas, use_container_width=True)
                
                # 2. 调用 AI 生成二次创作建议
                with st.spinner(f"AI 正在构思 {p_name} 的扩展方案..."):
                    ai_advice = generate_ai_description(source_img, target_size)
                    st.info(ai_advice)

else:
    st.info("请在上方上传图片以开始。")
