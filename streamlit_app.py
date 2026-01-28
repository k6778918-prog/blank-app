import streamlit as st
import PIL.Image
import google.generativeai as genai
import io

# --- 1. 配置与初始化 ---
st.set_page_config(page_title="FB素材AI二次创作预览", layout="wide")

# 配置 API
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("⚠️ 提示：未检测到 API Key，预览功能正常，但 AI 分析建议将无法显示。")

# Facebook 2026 核心版位尺寸
FB_SIZES = {
    "Stories/Reels (9:16)": (1080, 1920),
    "Feed/Post (1:1)": (1080, 1080),
    "Feed/Ads (4:5)": (1080, 1350),
    "Ads Landscape (1.91:1)": (1200, 628)
}


def generate_ai_description(source_img, target_size_name):
    """
    带有容错机制的模型调用
    """
    # 尝试模型列表，按推荐顺序排列
    model_names = ['gemini-1.5-pro', 'gemini-1.5-flash']
    
    last_error = ""
    for name in model_names:
        try:
            # 确保使用最新的 GenerativeModel 调用方式
            model = genai.GenerativeModel(model_name=name)
            
            prompt = f"""
            分析这张图片。我需要将其适配为 Facebook 的 {target_size_name} 版位。
            请基于原图的纹理、色彩和元素，给出具体的【二次创作背景扩展建议】。
            要求：1. 保持主体内容不变；2. 描述应该在空白区域补充哪些元素以实现无缝扩展。
            """
            
            response = model.generate_content([prompt, source_img])
            return response.text
        except Exception as e:
            last_error = str(e)
            continue # 如果报错，尝试下一个模型
            
    return f"❌ AI 构思暂不可用。报错信息: {last_error}\n提示：请检查 API Key 是否已启用 Gemini API 权限。"



def create_preview(image, target_size, bg_color=(245, 245, 245)):
    """
    生成预览图：将原图等比例缩放并居中放置在指定版位画布上
    """
    tw, th = target_size
    canvas = PIL.Image.new("RGB", target_size, bg_color)
    
    # 缩放原图以契合画布（Contain 模式）
    img_copy = image.copy()
    img_copy.thumbnail((tw, th), PIL.Image.LANCZOS)
    
    # 计算居中坐标
    offset = ((tw - img_copy.width) // 2, (th - img_copy.height) // 2)
    canvas.paste(img_copy, offset)
    return canvas

# --- 2. UI 渲染 ---
st.title("🎯 FB 素材二次创作预览器")
st.write("不改变原图内容，一键生成所有版位占位预览，并获取 AI 背景扩展建议。")

with st.sidebar:
    st.header("⚙️ 样式设置")
    selected_placements = st.multiselect(
        "选择版位", 
        list(FB_SIZES.keys()), 
        default=["Stories/Reels (9:16)", "Feed/Post (1:1)"]
    )
    bg_mode = st.selectbox("预览画布底色", ["浅灰色", "纯白色", "黑色"])
    bg_color_map = {"浅灰色": (245, 245, 245), "纯白色": (255, 255, 255), "黑色": (0, 0, 0)}
    current_bg = bg_color_map[bg_mode]

uploaded_file = st.file_uploader("📥 上传图片素材", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    source_img = PIL.Image.open(uploaded_file)
    
    # 点击执行
    if st.button("✨ 一键生成版位预览及 AI 创作方案", use_container_width=True):
        st.write("---")
        # 创建网格
        cols = st.columns(len(selected_placements))
        
        for idx, p_name in enumerate(selected_placements):
            with cols[idx]:
                st.markdown(f"**{p_name}**")
                target_dims = FB_SIZES[p_name]
                
                # 1. 生成预览图（不展示原图，直接展示在画布里的样子）
                preview_img = create_preview(source_img, target_dims, current_bg)
                st.image(preview_img, use_container_width=True, caption=f"尺寸: {target_dims[0]}x{target_dims[1]}")
                
                # 2. 调用 AI 给出该版位的扩展方案
                with st.expander("👁️ AI 二次创作构思", expanded=True):
                    with st.spinner("构思中..."):
                        advice = generate_ai_description(source_img, p_name)
                        st.write(advice)

else:
    st.info("💡 请先上传一张图片，我们将为您生成所有 Facebook 版位的预览。")
