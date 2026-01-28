import streamlit as st
from PIL import Image
import os
import zipfile
from io import BytesIO

# --- 配置：Facebook 版位尺寸 ---
FB_SIZES = {
    "Feed (1:1) - 正方形": (1080, 1080),
    "Feed/Ads (4:5) - 纵向": (1080, 1350),
    "Stories/Reels (9:16) - 全屏": (1080, 1920),
    "Ads (1.91:1) - 横向广告": (1200, 628)
}

def process_image_no_blur(image, target_size, bg_color=(255, 255, 255)):
    """
    不裁剪、不模糊：等比例缩放并在剩余空间填充纯色
    """
    target_w, target_h = target_size
    # 统一转为 RGB
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    
    img_w, img_h = image.size

    # 1. 计算缩放比例，确保图片完全包含在画布内
    ratio = min(target_w / img_w, target_h / img_h)
    new_w = int(img_w * ratio)
    new_h = int(img_h * ratio)
    resized_img = image.resize((new_w, new_h), Image.LANCZOS)

    # 2. 创建纯色背景画布
    canvas = Image.new("RGB", (target_w, target_h), bg_color)
    
    # 3. 将原图粘贴在中心
    offset = ((target_w - new_w) // 2, (target_h - new_h) // 2)
    canvas.paste(resized_img, offset)
    
    return canvas

# --- Streamlit UI ---
st.set_page_config(page_title="FB尺寸无损助手", page_icon="🎯")

st.title("🎯 FB 素材尺寸一键生成 (无损模式)")
st.info("模式：保持原图比例不被裁剪，空白处填充纯色。")

with st.sidebar:
    st.header("⚙️ 配置参数")
    selected_placements = st.multiselect(
        "选择输出版位：", 
        list(FB_SIZES.keys()), 
        default=list(FB_SIZES.keys())
    )
    
    bg_choice = st.radio("填充背景颜色：", ("白色", "黑色"))
    color_map = {"白色": (255, 255, 255), "黑色": (0, 0, 0)}
    bg_color = color_map[bg_choice]
    
    quality = st.slider("导出质量", 50, 100, 95)

uploaded_files = st.file_uploader("上传图片", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files:
    if st.button(f"生成 {len(uploaded_files) * len(selected_placements)} 张素材"):
        zip_buffer = BytesIO()
        
        with st.spinner("处理中..."):
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
                for uploaded_file in uploaded_files:
                    img = Image.open(uploaded_file)
                    base_name = os.path.splitext(uploaded_file.name)[0]
                    
                    for p_name in selected_placements:
                        target_dims = FB_SIZES[p_name]
                        # 执行无损填充转换
                        final_img = process_image_no_blur(img, target_dims, bg_color)
                        
                        # 保存
                        buf = BytesIO()
                        final_img.save(buf, format="JPEG", quality=quality)
                        # 文件夹分类：原图名/版位名.jpg
                        clean_p_name = p_name.split(' ')[0].replace("/", "-")
                        zip_file.writestr(f"{base_name}/{clean_p_name}.jpg", buf.getvalue())
        
        st.success("处理完成！")
        st.download_button(
            label="📥 下载全尺寸素材包",
            data=zip_buffer.getvalue(),
            file_name="fb_batch_assets.zip",
            mime="application/zip"
        )
