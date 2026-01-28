import streamlit as st
import PIL.Image
import google.generativeai as genai
import io
import time
import random

# --- 1. 页面配置 ---
st.set_page_config(page_title="FB素材AI助手", layout="wide", page_icon="🎨")

# 尝试初始化 API
api_key = st.secrets.get("GEMINI_API_KEY", "")
if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("🔑 未在 Secrets 中配置 GEMINI_API_KEY")

FB_SIZES = {
    "Stories (9:16)": (1080, 1920),
    "Feed (1:1)": (1080, 1080),
    "Feed (4:5)": (1080, 1350),
    "Ads (1.91:1)": (1200, 628)
}

# --- 2. 新增：API 连通性测试函数 ---
def test_gemini_connection():
    """自动化诊断：寻找可用模型并测试连接"""
    try:
        # 1. 检查 API 是否能列出模型 (验证 Key 的基础有效性)
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if not available_models:
            return False, "❌ Key 有效但未授权任何生成模型。请在 AI Studio 启用 Gemini API。"

        # 2. 自动选择列表中第一个可用的模型进行握手 (解决 404 问题)
        test_model_name = available_models[0]
        test_model = genai.GenerativeModel(test_model_name)
        
        # 极简生成测试
        response = test_model.generate_content("Hi", generation_config={"max_output_tokens": 5})
        
        if response:
            return True, f"✅ 连接成功！已自动匹配模型：{test_model_name}"
            
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            return False, "⚠️ 频率限制：Key 正常但请求太快。"
        elif "API_KEY_INVALID" in error_msg:
            return False, "❌ Key 错误：请检查 Secrets 中的字符串。"
        else:
            return False, f"❌ 诊断失败：{error_msg}"

# --- 3. 核心逻辑函数 ---
def get_usable_model():
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in available:
            if 'flash' in m: return m
        return "models/gemini-1.5-pro"
    except:
        return "models/gemini-1.5-flash"

@st.cache_data(show_spinner=False, ttl=600)
def get_ai_creative_advice(img_bytes, placement_names):
    try:
        model = genai.GenerativeModel(get_usable_model())
        img = PIL.Image.open(io.BytesIO(img_bytes))
        p_list = ", ".join(placement_names)
        prompt = f"分析此图并适配：{p_list}。简述各版位背景扩展建议。格式：[版位名]: 建议"
        response = model.generate_content([prompt, img])
        return response.text
    except Exception as e:
        return f"LIMIT_ERROR: {str(e)}"

def create_styled_preview(image, target_size):
    tw, th = target_size
    bg_color = image.convert("RGB").getpixel((5, 5))
    canvas = PIL.Image.new("RGB", target_size, bg_color)
    img_copy = image.copy()
    img_copy.thumbnail((tw, th), PIL.Image.LANCZOS)
    canvas.paste(img_copy, ((tw - img_copy.width) // 2, (th - img_copy.height) // 2))
    display_h = 320
    display_w = int(tw * (display_h / th))
    return canvas.resize((display_w, display_h), PIL.Image.LANCZOS)

# --- 4. UI 界面 ---
st.title("🎨 FB 素材 AI 助手 + 连通性测试")

with st.sidebar:
    st.header("⚙️ 系统控制")
    
    # 诊断按钮
    if st.button("🔍 测试 Gemini 连接状态"):
        with st.spinner("正在握手测试..."):
            success, message = test_gemini_connection()
            if success:
                st.success(message)
            else:
                st.error(message)
                
    st.divider()
    selected = st.multiselect("目标版位", list(FB_SIZES.keys()), default=["Stories (9:16)", "Feed (1:1)"])

uploaded_file = st.file_uploader("📥 上传图片", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    file_bytes = uploaded_file.getvalue()
    source_img = PIL.Image.open(io.BytesIO(file_bytes))
    
    if st.button("🚀 生成预览与 AI 建议", use_container_width=True):
        with st.spinner("AI 分析中..."):
            advice_text = get_ai_creative_advice(file_bytes, selected)
        
        # 即使 AI 报错，预览图也要出来
        st.divider()
        n_cols = 4
        rows = [selected[i:i + n_cols] for i in range(0, len(selected), n_cols)]
        
        for row in rows:
            cols = st.columns(len(row))
            for idx, p_name in enumerate(row):
                with cols[idx]:
                    st.write(f"**{p_name}**")
                    preview = create_styled_preview(source_img, FB_SIZES[p_name])
                    st.image(preview, use_container_width=False)
                    
                    with st.expander("💡 建议", expanded=True):
                        if "LIMIT_ERROR" in advice_text:
                            st.caption("AI 暂时休息，请参考手动扩展建议：保持色调统一，延展边缘纹理。")
                        else:
                            st.write(advice_text)

                    # 下载按钮
                    buf = io.BytesIO()
                    preview.save(buf, format="JPEG")
                    st.download_button("💾 下载", buf.getvalue(), f"{p_name}.jpg", "image/jpeg", key=f"d_{p_name}")
