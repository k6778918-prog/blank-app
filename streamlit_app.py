import streamlit as st
import PIL.Image
import google.generativeai as genai
import io

# --- 1. 配置与初始化 ---
st.set_page_config(page_title="FB素材AI助手(专业版)", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("🔑 请在 Secrets 中配置 GEMINI_API_KEY")

FB_SIZES = {
    "Stories/Reels (9:16)": (1080, 1920),
    "Feed/Post (1:1)": (1080, 1080),
    "Feed/Ads (4:5)": (1080, 1350),
    "Ads Landscape (1.91:1)": (1200, 628)
}

# --- 2. 逻辑函数 ---

def get_best_model():
    """动态获取可用模型"""
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in available:
            if 'flash' in m: return m
        return "models/gemini-1.5-pro"
    except:
        return "models/gemini-1.5-flash"

@st.cache_data(show_spinner=False)
def get_combined_ai_advice(img_bytes, placement_names):
    """合并所有版位需求，单次请求 AI"""
    try:
        model = genai.GenerativeModel(get_best_model())
        img = PIL.Image.open(io.BytesIO(img_bytes))
        
        placements_list = "\n".join([f"- {name}" for name in placement_names])
        prompt = f"""
        任务：分析图片并为以下 Facebook 广告版位提供背景扩展建议：
        {placements_list}
        
        要求：
        1. 针对每个版位，描述如何基于原图风格（纹理、光影）向外扩展。
        2. 保持主体不变，二次创作边缘元素。
        3. 请按以下格式返回：
           [版位名称]: 建议内容
        """
        response = model.generate_content([prompt, img])
        return response.text
    except Exception as e:
        if "429" in str(e):
            return "ERROR_429: 触发频率限制，请等待 60 秒后重试。"
        return f"ERROR: {str(e)}"

def make_compact_preview(image, target_size):
    """生成精致的小型预览图"""
    tw, th = target_size
    # 提取边缘颜色提升美感
    bg_color = image.convert("RGB").getpixel((5, 5))
    canvas = PIL.Image.new("RGB", target_size, bg_color)
    
    img_copy = image.copy()
    img_copy.thumbnail((tw, th), PIL.Image.LANCZOS)
    canvas.paste(img_copy, ((tw - img_copy.width) // 2, (th - img_copy.height) // 2))
    
    # 缩小至显示高度 320px
    display_h = 320
    display_w = int(tw * (display_h / th))
    return canvas.resize((display_w, display_h), PIL.Image.LANCZOS)

# --- 3. UI 界面 ---
st.title("🚀 Facebook 素材 AI 适配与二次创作")
st.caption("使用一次性合并请求技术，规避频率限制，支持免费模型预览。")

with st.sidebar:
    st.header("控制中心")
    selected_placements = st.multiselect(
        "选择输出版位", 
        list(FB_SIZES.keys()), 
        default=["Stories/Reels (9:16)", "Feed/Post (1:1)"]
    )
    st.divider()
    st.info("💡 提示：预览图已按比例缩小显示。")

uploaded_file = st.file_uploader("📥 上传图片素材", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    # 读取图片字节用于缓存识别
    file_bytes = uploaded_file.getvalue()
    source_img = PIL.Image.open(io.BytesIO(file_bytes))
    
    if st.button("✨ 生成小型预览及 AI 创作方案", use_container_width=True):
        # 1. 发起单次 AI 请求
        with st.spinner("AI 正在深度分析图片并构思所有版位方案..."):
            all_advice = get_combined_ai_advice(file_bytes, selected_placements)
        
        if "ERROR_429" in all_advice:
            st.error(all_advice)
        else:
            # 2. 展示整体 AI 建议（可选）
            with st.expander("📘 全版位 AI 二次创作指导说明", expanded=False):
                st.write(all_advice)

            st.divider()

            # 3. 动态网格展示预览图
            n_cols = 4 # 预览图调小了，一行可以放更多
            rows = [selected_placements[i:i + n_cols] for i in range(0, len(selected_placements), n_cols)]
            
            for row in rows:
                cols = st.columns(len(row))
                for idx, p_name in enumerate(row):
                    with cols[idx]:
                        st.markdown(f"**{p_name}**")
                        # 生成预览图
                        preview = make_compact_preview(source_img, FB_SIZES[p_name])
                        st.image(preview, use_container_width=False)
                        
                        # 从合并后的建议中提取属于该版位的部分（简单通过关键词匹配）
                        st.caption("建议重点：")
                        # 尝试通过版位名定位描述，如果没匹配到则显示通篇建议
                        advice_lines = [line for line in all_advice.split('\n') if p_name.split('/')[0] in line]
                        if advice_lines:
                            st.write(advice_lines[0].split(':')[-1].strip())
                        else:
                            st.write("详见上方指导说明")
else:
    st.info("请先上传图片。系统将自动按原图边缘色填充背景。")
