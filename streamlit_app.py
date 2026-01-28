import streamlit as st
import PIL.Image
import google.generativeai as genai
import io
import time
import random

# --- 1. 页面配置 ---
st.set_page_config(page_title="FB素材AI二次创作工具", layout="wide", page_icon="🎨")

# 侧边栏配置 API Key
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("🔑 请在 Streamlit 云端 Secrets 中配置 GEMINI_API_KEY")

# Facebook 版位标准尺寸
FB_SIZES = {
    "Stories (9:16)": (1080, 1920),
    "Feed (1:1)": (1080, 1080),
    "Feed (4:5)": (1080, 1350),
    "Ads (1.91:1)": (1200, 628)
}

# --- 2. 核心逻辑函数 ---

def get_usable_model():
    """获取可用的模型名称"""
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in available:
            if 'flash' in m: return m
        return "models/gemini-1.5-pro"
    except:
        return "models/gemini-1.5-flash"

@st.cache_data(show_spinner=False, ttl=600)
def get_ai_creative_advice(img_bytes, placement_names):
    """
    带有【自动重试】和【合并请求】逻辑的 AI 调用
    """
    max_retries = 3
    for i in range(max_retries):
        try:
            model_name = get_usable_model()
            model = genai.GenerativeModel(model_name)
            img = PIL.Image.open(io.BytesIO(img_bytes))
            
            p_list = ", ".join(placement_names)
            prompt = f"""
            分析此图。我需要将其适配为：{p_list}。
            请基于原图的色彩和纹理，为每个版位提供具体的【背景扩展二次创作建议】。
            格式：[版位名]: 建议内容
            """
            
            response = model.generate_content([prompt, img])
            return response.text
        except Exception as e:
            if "429" in str(e) and i < max_retries - 1:
                time.sleep(2 * (i + 1) + random.random()) # 退避重试
                continue
            return f"LIMIT_ERROR: {str(e)}"

def create_styled_preview(image, target_size):
    """生成精致小型预览图，自动提取边缘色填充"""
    tw, th = target_size
    # 提取左上角像素色作为底色，增加视觉统一感
    bg_color = image.convert("RGB").getpixel((5, 5))
    canvas = PIL.Image.new("RGB", target_size, bg_color)
    
    img_copy = image.copy()
    img_copy.thumbnail((tw, th), PIL.Image.LANCZOS)
    canvas.paste(img_copy, ((tw - img_copy.width) // 2, (th - img_copy.height) // 2))
    
    # 物理缩小显示高度至 320 像素
    display_h = 320
    display_w = int(tw * (display_h / th))
    return canvas.resize((display_w, display_h), PIL.Image.LANCZOS)

# --- 3. UI 界面 ---
st.title("🎨 Facebook 素材 AI 二次创作助手")
st.markdown("上传图片，AI 将模拟背景扩展效果并提供创作构思。")

with st.sidebar:
    st.header("⚙️ 设置")
    selected = st.multiselect("目标版位", list(FB_SIZES.keys()), default=["Stories (9:16)", "Feed (1:1)"])
    st.divider()
    st.caption("注：预览图已按比例缩小。")

uploaded_file = st.file_uploader("📥 上传图片 (JPG/PNG)", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    file_bytes = uploaded_file.getvalue()
    source_img = PIL.Image.open(io.BytesIO(file_bytes))
    
    if st.button("🚀 开始 AI 分析并生成预览", use_container_width=True):
        # 1. AI 建议部分
        with st.spinner("AI 正在构思背景扩展方案..."):
            advice_text = get_ai_creative_advice(file_bytes, selected)
        
        # 2. 界面展示
        if "LIMIT_ERROR" in advice_text:
            st.warning("⚠️ AI 频率受限。已为您启用本地默认设计建议。")
            advice_text = "建议重点：保持主体居中，利用原图边缘色进行无缝延伸，确保文字避开版位遮挡区。"
        
        st.divider()

        # 3. 预览图矩阵
        n_cols = 4
        rows = [selected[i:i + n_cols] for i in range(0, len(selected), n_cols)]
        
        for row in rows:
            cols = st.columns(len(row))
            for idx, p_name in enumerate(row):
                with cols[idx]:
                    st.write(f"**{p_name}**")
                    # 生成预览
                    preview = create_styled_preview(source_img, FB_SIZES[p_name])
                    st.image(preview, use_container_width=False)
                    
                    # 针对性建议显示
                    with st.expander("💡 创作建议", expanded=True):
                        # 尝试匹配 AI 返回的特定版位行
                        specific_advice = [l for l in advice_text.split('\n') if p_name.split(' ')[0] in l]
                        st.caption(specific_advice[0].split(':')[-1] if specific_advice else advice_text)
                    
                    # 下载按钮
                    buf = io.BytesIO()
                    preview.save(buf, format="JPEG", quality=95)
                    st.download_button(
                        label="💾 下载预览图",
                        data=buf.getvalue(),
                        file_name=f"Preview_{p_name.replace(' ', '_')}.jpg",
                        mime="image/jpeg",
                        key=f"btn_{p_name}"
                    )
else:
    st.info("👋 欢迎！请上传一张素材图片开始。")
