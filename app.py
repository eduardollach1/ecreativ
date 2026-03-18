import streamlit as st
from PIL import Image
import io
import inference

def load_resized_image(image_path, target_height=75):
    img = Image.open(image_path)
    aspect_ratio = img.width / img.height
    new_width = int(target_height * aspect_ratio)
    return img.resize((new_width, target_height), Image.Resampling.LANCZOS)

st.set_page_config(page_title="eCreativ V1.1 - The Fashion Vibe-Engine", layout="wide")

st.markdown("""
<style>
div.stButton > button:first-child {
    background-color: #e0f2fe;
    color: #0369a1;
    border: 1px solid #bae6fd;
}
div.stButton > button:first-child:hover {
    background-color: #bae6fd;
    color: #0284c7;
    border: 1px solid #7dd3fc;
}
</style>
""", unsafe_allow_html=True)

# Custom Header using the eCreativ Logo image
col_logo, col_v, _ = st.columns([1.5, 1, 6])
with col_logo:
    st.image("logo.png", use_container_width=True)
with col_v:
    st.markdown("<h4 style='margin-top: 45px; color: #268bd2;'>v1.1</h4>", unsafe_allow_html=True)

st.markdown("### Fashion Model & Scene based on Successful Brands & Retailers in the category: <span style='color: #268bd2; font-weight: bold;'>Cocktail Dresses</span><br><span style='font-size: 0.85em; font-weight: normal;'>We've analyzed 6 successful fashion images for Cocktail Dresses, and now you can create a best in class mix for your Cocktail Dress garments</span>", unsafe_allow_html=True)

# Stage A: The Brand Mixer
st.header("Stage A: The Brand Mixer")
st.write("Adjust the sliders to synthesize a 'Brand Average'. The model, pose, and lighting will dynamically interpolate between the selected brand DNAs. The total is locked at 100%.")

# Define the 6 brands
brands = ["Ralph Lauren", "Liu Jo", "Zara", "Liverpool", "Neiman Marcus", "Nordstrom"]
if 'brand_weights' not in st.session_state:
    st.session_state.brand_weights = {
        "Ralph Lauren": 50,
        "Liu Jo": 0,
        "Zara": 50,
        "Liverpool": 0,
        "Neiman Marcus": 0,
        "Nordstrom": 0
    }
    for b in brands:
        st.session_state[b + "_slider"] = st.session_state.brand_weights[b]

def update_sliders(changed_brand):
    new_val = st.session_state[changed_brand + "_slider"]
    st.session_state.brand_weights[changed_brand] = new_val
    leftover = 100 - new_val
    
    other_brands = [b for b in brands if b != changed_brand]
    sum_others = sum(st.session_state.brand_weights[b] for b in other_brands)
    
    if sum_others > 0:
        for b in other_brands:
            raw_val = st.session_state.brand_weights[b] * leftover / sum_others
            st.session_state.brand_weights[b] = int(round(raw_val / 5.0) * 5)
    else:
        split = (leftover // len(other_brands)) // 5 * 5
        for b in other_brands:
            st.session_state.brand_weights[b] = split
            
    current_sum = sum(st.session_state.brand_weights[b] for b in brands)
    error = 100 - current_sum
    while error > 0:
        largest_other = min(other_brands, key=lambda b: st.session_state.brand_weights[b])
        st.session_state.brand_weights[largest_other] += 5
        error -= 5
    while error < 0:
        candidates = [b for b in other_brands if st.session_state.brand_weights[b] >= 5]
        if not candidates:
            break
        largest_other = max(candidates, key=lambda b: st.session_state.brand_weights[b])
        st.session_state.brand_weights[largest_other] -= 5
        error += 5

    for b in brands:
        st.session_state.brand_weights[b] = max(0, min(100, st.session_state.brand_weights[b]))
        st.session_state[b + "_slider"] = st.session_state.brand_weights[b]

# Row 1: Ralph Lauren, Zara, Liu Jo
st.write("") # Spacer
r1_col1, r1_col2, r1_col3, _ = st.columns([1, 1, 1, 3])

with r1_col1:
    st.image(load_resized_image("ralph_lauren_logo.png"))
    st.slider("Ralph Lauren", min_value=0, max_value=100, step=5, format="%d%%", key="Ralph Lauren_slider", on_change=update_sliders, args=("Ralph Lauren",), label_visibility="collapsed")
with r1_col2:
    st.image(load_resized_image("zara_logo.png"))
    st.slider("Zara", min_value=0, max_value=100, step=5, format="%d%%", key="Zara_slider", on_change=update_sliders, args=("Zara",), label_visibility="collapsed")
with r1_col3:
    st.image(load_resized_image("liujo_logo.png"))
    st.slider("Liu Jo", min_value=0, max_value=100, step=5, format="%d%%", key="Liu Jo_slider", on_change=update_sliders, args=("Liu Jo",), label_visibility="collapsed")

st.write("") # Spacer

# Row 2: Liverpool, Nordstrom, Neiman Marcus
r2_col1, r2_col2, r2_col3, _ = st.columns([1, 1, 1, 3])

with r2_col1:
    st.image(load_resized_image("liverpool_logo.png"))
    st.slider("Liverpool", min_value=0, max_value=100, step=5, format="%d%%", key="Liverpool_slider", on_change=update_sliders, args=("Liverpool",), label_visibility="collapsed")
with r2_col2:
    st.image(load_resized_image("nordstrom_logo.png"))
    st.slider("Nordstrom", min_value=0, max_value=100, step=5, format="%d%%", key="Nordstrom_slider", on_change=update_sliders, args=("Nordstrom",), label_visibility="collapsed")
with r2_col3:
    st.image(load_resized_image("neiman_marcus_logo.png"))
    st.slider("Neiman Marcus", min_value=0, max_value=100, step=5, format="%d%%", key="Neiman Marcus_slider", on_change=update_sliders, args=("Neiman Marcus",), label_visibility="collapsed")

custom_scene_prompt = st.text_area("Custom Scene/Pose Prompt (Optional)", placeholder="e.g. Model sitting at a Parisian cafe holding a red umbrella")

# Initialize session state for the generated base vibes
if 'base_vibe_standard' not in st.session_state:
    st.session_state.base_vibe_standard = None
if 'base_vibe_no_acc' not in st.session_state:
    st.session_state.base_vibe_no_acc = None

if st.button("Generate Vibe Model, Pose & Scene"):
    with st.spinner("Synthesizing vibe (Standard & No Accessories)..."):
        float_weights = {b: val / 100.0 for b, val in st.session_state.brand_weights.items()}
        print(f"DEBUG APP.PY - Calling inference with weights: {float_weights}")
        generated_images = inference.generate_base_vibe(float_weights, custom_scene_prompt)
        if generated_images and 'standard' in generated_images and 'no_accessories' in generated_images:
            st.session_state.base_vibe_standard = generated_images['standard']
            st.session_state.base_vibe_no_acc = generated_images['no_accessories']
            st.success("Base Vibes generated successfully!")
        else:
            st.error("Failed to generate base vibe. Ensure at least one weight > 0.")

if st.session_state.base_vibe_standard and st.session_state.base_vibe_no_acc:
    st.write("### Generated Base Vibes")
    _, col_v1, col_v2, _ = st.columns([1, 1, 1, 1])
    with col_v1:
        st.image(st.session_state.base_vibe_standard, caption="Variation 1: Standard (With Accessories)", use_container_width=True)
    with col_v2:
        st.image(st.session_state.base_vibe_no_acc, caption="Variation 2: No Accessories (Just Garment & Shoes)", use_container_width=True)

# Stage B: Garment Synthesis
st.header("Stage B: Garment Virtual Try-On")
st.write("Upload your garment (e.g., a cocktail dress) to place on your model.")

uploaded_garment = st.file_uploader("Upload Garment Image (PNG/JPG)", type=["png", "jpg", "jpeg"])

col_g1, col_g2 = st.columns(2)
with col_g1:
    garment_category = st.selectbox("Garment Category", ["upper_body", "lower_body", "dresses"])
with col_g2:
    garment_desc = st.text_input("Garment Description (Optional)", placeholder="e.g. cute pink top, long black dress")

if st.session_state.base_vibe_standard and st.session_state.base_vibe_no_acc and uploaded_garment is not None:
    garment_image = Image.open(uploaded_garment)
    st.image(garment_image, caption="Uploaded Garment", width=200)
    
    if st.button("Place the Dress on the Model Variations Above"):
        with st.spinner("Executing Virtual Try-On via Google Native Vertex AI on BOTH variations..."):
            _, col_r1, col_r2, _ = st.columns([1, 1, 1, 1])
            
            with col_r1:
                st.markdown("**Standard Variation**")
                res_standard = inference.synthesize_garment(
                    st.session_state.base_vibe_standard, 
                    garment_image,
                    garment_category,
                    garment_desc
                )
                if res_standard:
                    w, h = res_standard.size
                    st.image(res_standard, caption="VTO Complete", use_container_width=True)
                else:
                    st.error("Failed on Standard Variation")
                    
            with col_r2:
                st.write("Synthesizing No Accessories Variation...")
                final_no_acc = inference.synthesize_garment(
                    st.session_state.base_vibe_no_acc, 
                    garment_image,
                    garment_category,
                    garment_desc
                )
                if final_no_acc:
                    st.image(final_no_acc, caption="VTO: No Accessories Variation", use_container_width=True)
                else:
                    st.error("Failed on No Accessories Variation")
                    
        st.success("Virtual Try-On successfully completed for both variations!")
elif uploaded_garment is not None and not st.session_state.base_vibe_standard:
    st.warning("Please generate Base Vibes first before synthesizing the garment.")
