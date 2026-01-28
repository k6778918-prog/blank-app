import streamlit as st
import PIL.Image
import google.generativeai as genai
import io

# --- 1. 页面配置 ---
st.set_page_config(page_title="FB素材AI助手", layout="wide")

# 配置 API Key
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("🔑 请在 Secrets 中配置 GEMINI_API_KEY")

# Facebook 核心版位尺寸
FB_SIZES = {
    "Stories/Reels (9:16)": (1080, 1920),
    "Feed/Post (1:1)": (1080, 1080),
    "Feed/Ads (4:5)": (1080, 1350),
    "Ads Landscape (1.91:1)": (1200, 628)
}

# --- 2. 核心逻辑 ---

def get_flash_model():
    """获取可用的免费模型"""
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # 优先使用 flash 模型（免费、快速）
        for m in available_models:
            if 'flash' in m:
                return m
        return "gemini-1.5-pro" # 备选
    except:
        return "gemini-1.5-flash"

def generate_ai_advice(source_img, target_name):
    """调用免费模型获取 AI 建议"""
    try:
        model_name = get_flash_model()
        model = genai.GenerativeModel(model_name)
        prompt = f"分析此图，为适配FB {target_name} 版位给出背景扩展建议。保持主体不变，描述如何二次创作边缘元素。简短点。"
        response = model.generate_content([prompt, source_img])
        return response.text
    except Exception as e:
        return f"AI 构思暂不可用: {str(e)}"

def create_small_preview(image, target_size):
    """生成缩小的预览图"""
    tw, th = target_size
    # 获取边缘色作为画布底色
    bg_color = image.convert("RGB").getpixel((5, 5))
    canvas = PIL.Image.new("RGB", target_size, bg_color)
    
    img_copy = image.copy()
    # 保持原图内容完整放入画布
    img_copy.thumbnail((tw, th), PIL.Image.LANCZOS)
    offset = ((tw - img_copy.width) // 2, (th - img_copy.height) // 2)
    canvas.paste(img_copy, offset)
    
    # 将画布进行物理缩小，以便在网页上显示更精细且不占空间
    # 缩小到高度为 400 像素的等比例尺寸
    display_h = 400
    display_w = int(tw * (display_h / th))
    return canvas.resize((display_w, display_h), PIL.Image.LANCZOS)

# --- 3. UI 界面 ---
st.title("🎯 Facebook 素材 AI 适配器 (免费版)")

with st.sidebar:
    st.header("控制台")
    selected_placements = st.multiselect(
        "选择输出版位", 
        list(FB_SIZES.keys()), 
        default=["Stories/Reels (9:16)", "Feed/Post (1:1)"]
    )
    st.write("---")
    st.caption("提示：使用 Gemini 1.5 Flash 免费模型生成")

uploaded_file = st.file_uploader("📤 上传图片素材", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    source_img = PIL.Image.open(uploaded_file)
    
    if st.button("✨ 生成小型预览及 AI 建议", use_container_width=True):
        st.write("---")
        
        # 动态创建列，每行显示最多 3 个预览图，避免排版过大
        n_cols = 3
        rows = [selected_placements[i:i + n_cols] for i in range(0, len(selected_placements), n_cols)]
        
        for row in rows:
            cols = st.columns(len(row))
            for idx, p_name in enumerate(row):
                with cols[idx]:
                    target_dims = FB_SIZES[p_name]
                    # 生成缩小后的预览图
                    preview = create_small_preview(source_img, target_dims)
                    
                    st.image(preview, caption=f"{p_name}", use_container_width=False)
                    
                    with st.expander("📝 AI 创作建议", expanded=True):
                        with st.spinner("AI 思考中..."):
                            advice = generate_ai_advice(source_img, p_name)
                            st.caption(advice)
else:
    st.info("请先上传图片。预览图已设置为固定高度，更易于浏览。")
