import streamlit as st
from PIL import Image, ImageFilter
import os
import zipfile
from io import BytesIO

# --- 配置：Facebook 2026 最新版位尺寸 ---
FB_SIZES = {
    "Feed (1:1) - 正方形": (1080, 1080),
    "Feed/Ads (4:5) - 纵向": (1080, 1350),
    "Stories/Reels (9:16) - 全屏": (1080, 1920),
    "Landscape (1.91:1) - 横向": (1200, 628)
}

def process_image_smart(image, target_size):
    """
    核心逻辑：保持主体完整，使用高斯模糊填充背景
    """
    target_w, target_h = target_size
    # 统一转为 RGB 模式，避免处理 PNG 透明层时报错
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    
    img_w, img_h = image.size

    # 1. 缩放主体：确保原图内容 100% 完整显示
    ratio = min(target_w / img_w, target_h / img_h)
    new_w = int(img_w * ratio)
    new_h = int(img_h * ratio)
    resized_main = image.resize((new_w, new_h), Image.LANCZOS)

    # 2. 生成背景：放大并模糊
    bg_ratio = max(target_w / img_w, target_h / img_h)
    bg_w = int(img_w * bg_ratio)
    bg_h = int(img_h * bg_ratio)
    background = image.resize((bg_w, bg_h), Image.LANCZOS)
    
    # 居中裁剪背景
    left = (bg_w - target_w) / 2
    top = (bg_h - target_h) / 2
    background = background.crop((left, top, left + target_w, top + target_h))
    
    # 施加高斯模糊 (radius=30 是比较自然的社交媒体风格)
    background = background.filter(ImageFilter.GaussianBlur(radius=30))

    # 3. 合成：将缩小的主体贴在模糊背景中央
    offset = ((target_w - new_w) // 2, (target_h - new_h) // 2)
    background.paste(resized_main, offset)
    
    return background

# --- Streamlit UI 界面 ---
st.set_page_config(page_title="FB素材智能转换器", page_icon="🖼️")

st.title("🖼️ Facebook 素材批量智能转换器")
st.markdown("""
**功能说明：** 上传任意比例图片，系统将自动生成适配 FB 不同版位的尺寸。
* ✅ **内容不丢失**：原图 100% 完整保留，不进行暴力裁剪。
* ✅ **智能填充**：空白处自动使用原图色彩进行高斯模糊填充。
""")

with st.sidebar:
    st.header("设置")
    selected_placements = st.multiselect(
        "选择需要生成的版位：", 
        list(FB_SIZES.keys()), 
        default=["Feed (1:1) - 正方形", "Stories/Reels (9:16) - 全屏"]
    )
    quality = st.slider("导出质量", 50, 100, 90)

uploaded_files = st.file_uploader("上传图片 (支持多选)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files:
    if st.button(f"开始处理 {len(uploaded_files)} 张图片"):
        zip_buffer = BytesIO()
        
        with st.status("正在处理图片...", expanded=True) as status:
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
                for uploaded_file in uploaded_files:
                    img = Image.open(uploaded_file)
                    base_name = os.path.splitext(uploaded_file.name)[0]
                    
                    for p_name in selected_placements:
                        target_dims = FB_SIZES[p_name]
                        # 执行智能转换
                        processed_img = process_image_smart(img, target_dims)
                        
                        # 保存到内存
                        buf = BytesIO()
                        processed_img.save(buf, format="JPEG", quality=quality)
                        file_path = f"{base_name}/{p_name.split(' ')[0]}.jpg"
                        zip_file.writestr(file_path, buf.getvalue())
            
            status.update(label="全部处理完成！", state="complete", expanded=False)

        st.success("🎉 所有图片已准备就绪")
        st.download_button(
            label="📥 点击下载全部压缩包 (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="facebook_assets_output.zip",
            mime="application/zip"
        )
