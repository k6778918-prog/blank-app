import streamlit as st
from PIL import Image
import os
import zipfile
from io import BytesIO

# --- 配置：Facebook 版位尺寸 ---
FB_SIZES = {
    "Feed (1:1) 正方形": (1080, 1080),
    "Feed/Ads (4:5) 纵向": (1080, 1350),
    "Stories/Reels (9:16) 竖屏": (1080, 1920),
    "Ads (1.91:1) 横向": (1200, 628)
}

def process_image_no_blur(image, target_size, bg_color=(255, 255, 255)):
    """处理核心：等比例缩放并填充背景"""
    target_w, target_h = target_size
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    
    img_w, img_h = image.size
    ratio = min(target_w / img_w, target_h / img_h)
    new_w, new_h = int(img_w * ratio), int(img_h * ratio)
    resized_img = image.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGB", (target_w, target_h), bg_color)
    offset = ((target_w - new_w) // 2, (target_h - new_h) // 2)
    canvas.paste(resized_img, offset)
    return canvas

# --- UI 界面 ---
st.set_page_config(page_title="FB素材无损预览转换", layout="wide")

st.title("🎯 Facebook 素材预览与批量处理")
st.caption("上传图片即可实时预览不同版位的显示效果，支持一键打包下载。")

# 侧边栏设置
with st.sidebar:
    st.header("⚙️ 全局设置")
    bg_choice = st.radio("填充背景色", ["白色", "黑色"])
    bg_color = (255, 255, 255) if bg_choice == "白色" else (0, 0, 0)
    
    selected_placements = st.multiselect(
        "选择需要输出的版位", 
        list(FB_SIZES.keys()), 
        default=list(FB_SIZES.keys())
    )
    quality = st.slider("图片压缩质量", 50, 100, 95)

# 上传组件
uploaded_files = st.file_uploader("选择素材图片", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files:
    # 遍历每张上传的图片
    for uploaded_file in uploaded_files:
        img = Image.open(uploaded_file)
        base_name = os.path.splitext(uploaded_file.name)[0]
        
        st.write("---")
        st.subheader(f"🖼️ 素材名称: {uploaded_file.name}")
        
        # 创建预览列
        cols = st.columns(len(selected_placements))
        
        # 存储当前图片的各尺寸结果
        processed_results = {}
        
        for idx, p_name in enumerate(selected_placements):
            target_dims = FB_SIZES[p_name]
            result_img = process_image_no_blur(img, target_dims, bg_color)
            processed_results[p_name] = result_img
            
            # 在对应的列展示预览
            with cols[idx]:
                st.image(result_img, caption=f"{p_name}\n({target_dims[0]}x{target_dims[1]})", use_container_width=True)

    # 底部下载区
    st.write("---")
    if st.button("🚀 生成并打包所有预览图", use_container_width=True):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
            for uploaded_file in uploaded_files:
                img = Image.open(uploaded_file)
                name = os.path.splitext(uploaded_file.name)[0]
                for p_name in selected_placements:
                    res_img = process_image_no_blur(img, FB_SIZES[p_name], bg_color)
                    buf = BytesIO()
                    res_img.save(buf, format="JPEG", quality=quality)
                    zip_file.writestr(f"{name}/{p_name.split(' ')[0]}.jpg", buf.getvalue())
        
        st.success("打包完成！")
        st.download_button(
            label="📥 下载 ZIP 压缩包",
            data=zip_buffer.getvalue(),
            file_name="fb_final_assets.zip",
            mime="application/zip",
            use_container_width=True
        )
