import streamlit as st
import random
from PIL import Image
import io
import inference
import base64

def load_resized_image(image_path, target_height=75):
    img = Image.open(image_path)
    aspect_ratio = img.width / img.height
    new_width = int(target_height * aspect_ratio)
    return img.resize((new_width, target_height), Image.Resampling.LANCZOS)

st.set_page_config(page_title="eCreativ V1.1 - The Fashion Vibe-Engine", layout="wide")

st.markdown("""
<style>
div[data-testid="stButton"] button[kind="secondary"] {
    background-color: #e0f2fe;
    color: #0369a1;
    border: 1px solid #bae6fd;
}
div[data-testid="stButton"] button[kind="secondary"]:hover {
    background-color: #bae6fd;
    color: #0284c7;
    border: 1px solid #7dd3fc;
}
</style>
""", unsafe_allow_html=True)

def render_centered_image(image_path, target_height=60):
    img = load_resized_image(image_path, target_height)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    html = f'<div style="display: flex; justify-content: center; align-items: center; height: {target_height}px;"><img src="data:image/png;base64,{img_str}" style="max-height: 100%;"></div>'
    st.markdown(html, unsafe_allow_html=True)

def render_centered_square(image_path, size=100):
    img = Image.open(image_path)
    img.thumbnail((size, size), Image.Resampling.LANCZOS)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    html = f'<div style="display: flex; justify-content: center; align-items: center; height: {size}px;"><img src="data:image/png;base64,{img_str}"></div>'
    st.markdown(html, unsafe_allow_html=True)



# Custom Header using the eCreativ Logo image
col_logo, col_v, _ = st.columns([1.5, 1, 6])
with col_logo:
    st.image("logo.png", use_container_width=True)
with col_v:
    st.markdown("<h4 style='margin-top: 45px; color: #268bd2;'>v1.1</h4>", unsafe_allow_html=True)

st.markdown("### Fashion Model & Scene based on Successful Brands & Retailers in the category: <span style='color: #268bd2; font-weight: bold;'>Cocktail Dresses</span><br><span style='font-size: 0.85em; font-weight: normal;'>We've analyzed 6 sets of successful fashion images for Cocktail Dresses, and now you can create a best in class mix for your Cocktail Dress garments</span>", unsafe_allow_html=True)

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
    render_centered_image("ralph_lauren_logo.png", 60)
with r1_col2:
    render_centered_image("zara_logo.png", 60)
with r1_col3:
    render_centered_image("liujo_logo.png", 60)

st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True) # Spacer between logos and sliders
r1s_col1, r1s_col2, r1s_col3, _ = st.columns([1, 1, 1, 3])

with r1s_col1:
    st.slider("Ralph Lauren", min_value=0, max_value=100, step=5, format="%d%%", key="Ralph Lauren_slider", on_change=update_sliders, args=("Ralph Lauren",), label_visibility="collapsed")
with r1s_col2:
    st.slider("Zara", min_value=0, max_value=100, step=5, format="%d%%", key="Zara_slider", on_change=update_sliders, args=("Zara",), label_visibility="collapsed")
with r1s_col3:
    st.slider("Liu Jo", min_value=0, max_value=100, step=5, format="%d%%", key="Liu Jo_slider", on_change=update_sliders, args=("Liu Jo",), label_visibility="collapsed")

st.write("") # Spacer

# Row 2: Liverpool, Nordstrom, Neiman Marcus
r2_col1, r2_col2, r2_col3, _ = st.columns([1, 1, 1, 3])

with r2_col1:
    render_centered_image("liverpool_logo.png", 60)
with r2_col2:
    render_centered_image("nordstrom_logo.png", 60)
with r2_col3:
    render_centered_image("neiman_marcus_logo.png", 60)

st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True) # Spacer between logos and sliders
r2s_col1, r2s_col2, r2s_col3, _ = st.columns([1, 1, 1, 3])

with r2s_col1:
    st.slider("Liverpool", min_value=0, max_value=100, step=5, format="%d%%", key="Liverpool_slider", on_change=update_sliders, args=("Liverpool",), label_visibility="collapsed")
with r2s_col2:
    st.slider("Nordstrom", min_value=0, max_value=100, step=5, format="%d%%", key="Nordstrom_slider", on_change=update_sliders, args=("Nordstrom",), label_visibility="collapsed")
with r2s_col3:
    st.slider("Neiman Marcus", min_value=0, max_value=100, step=5, format="%d%%", key="Neiman Marcus_slider", on_change=update_sliders, args=("Neiman Marcus",), label_visibility="collapsed")



custom_scene_prompt = st.text_area("Custom Scene/Pose Prompt (Optional)", placeholder="e.g. Model sitting at a Parisian cafe holding a red umbrella")

# Initialize session state for the generated base vibes
if 'base_vibe_standard' not in st.session_state:
    st.session_state.base_vibe_standard = None
if 'base_vibe_no_acc' not in st.session_state:
    st.session_state.base_vibe_no_acc = None

if st.button("Generate Custom Model, Pose & Scene", type="primary"):
    with st.spinner("Synthesizing vibe (Standard & No Accessories)..."):
        float_weights = {b: val / 100.0 for b, val in st.session_state.brand_weights.items()}
        print(f"DEBUG APP.PY - Calling inference with weights: {float_weights}")
        generated_images = inference.generate_base_vibe(float_weights, custom_scene_prompt)
        if generated_images and 'standard' in generated_images and 'no_accessories' in generated_images:
            st.session_state.base_vibe_standard = generated_images['standard']
            st.session_state.base_vibe_no_acc = generated_images['no_accessories']
            st.success("Base Vibes generated successfully!")
        else:
            if isinstance(generated_images, dict) and "error" in generated_images:
                st.error(generated_images["error"])
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
st.write("Upload your garment (e.g., a cocktail dress) to place on your model, or choose one of our examples.")

if 'garment_option' not in st.session_state:
    st.session_state.garment_option = "Upload my own"

def select_garment(option):
    st.session_state.garment_option = option

g_col1, g_col2, g_col3, _ = st.columns([1.5, 1.5, 1.5, 2.5])
with g_col1:
    upload_html = '''
    <div style="display: flex; justify-content: center; align-items: center; height: 100px;">
        <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="#268bd2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
        </svg>
    </div>
    '''
    st.markdown(upload_html, unsafe_allow_html=True)
    st.button("Upload my own", on_click=select_garment, args=("Upload my own",), use_container_width=True, type="secondary")
with g_col2:
    render_centered_square("zara_black_dress.jpg", 100)
    st.button("Zara Black Dress", on_click=select_garment, args=("Zara Black Cocktail Dress",), use_container_width=True, type="secondary")
with g_col3:
    render_centered_square("ralph_lauren_red.jpg", 100)
    st.button("Ralph Lauren Red", on_click=select_garment, args=("Ralph Lauren Red Cocktail Dress",), use_container_width=True, type="secondary")

st.markdown(f"**Selected Source:** {st.session_state.garment_option}")

garment_option = st.session_state.garment_option
uploaded_garment = None
selected_garment_path = None

if garment_option == "Upload my own":
    uploaded_garment = st.file_uploader("Upload Garment Image (PNG/JPG)", type=["png", "jpg", "jpeg"])
elif garment_option == "Zara Black Cocktail Dress":
    selected_garment_path = "zara_black_dress.jpg"
elif garment_option == "Ralph Lauren Red Cocktail Dress":
    selected_garment_path = "ralph_lauren_red.jpg"

col_g1, col_g2 = st.columns(2)
with col_g1:
    garment_category = st.selectbox("Garment Category", ["upper_body", "lower_body", "dresses"])
with col_g2:
    garment_desc = st.text_input("Garment Description (Optional)", placeholder="e.g. cute pink top, long black dress")

garment_image = None
if uploaded_garment is not None:
    garment_image = Image.open(uploaded_garment)
elif selected_garment_path is not None:
    garment_image = Image.open(selected_garment_path)

if st.session_state.base_vibe_standard and st.session_state.base_vibe_no_acc and garment_image is not None:
    st.image(garment_image, caption=garment_option if garment_option != "Upload my own" else "Uploaded Garment", width=200)
    
    if st.button("Place the Dress on the Model Variations Above"):
        with st.spinner("Executing Virtual Try-On via Google Native Vertex AI on BOTH variations..."):
            res_standard = inference.synthesize_garment(
                st.session_state.base_vibe_standard, 
                garment_image,
                garment_category,
                garment_desc
            )
            if isinstance(res_standard, dict) and "error" in res_standard:
                st.error(res_standard["error"])
            elif res_standard:
                st.session_state.vto_standard = res_standard
            else:
                st.error("Failed on Standard Variation")
                
            final_no_acc = inference.synthesize_garment(
                st.session_state.base_vibe_no_acc, 
                garment_image,
                garment_category,
                garment_desc
            )
            if isinstance(final_no_acc, dict) and "error" in final_no_acc:
                st.error(final_no_acc["error"])
            elif final_no_acc:
                st.session_state.vto_no_acc = final_no_acc
            else:
                st.error("Failed on No Accessories Variation")
                
        st.success("Virtual Try-On successfully completed for both variations!")
        st.session_state.try_on_complete = True

    if st.session_state.get('try_on_complete', False) and 'vto_standard' in st.session_state and 'vto_no_acc' in st.session_state:
        st.markdown("### Original Try-On Results")
        _, col_r1, col_r2, _ = st.columns([1, 1, 1, 1])
        with col_r1:
            st.markdown("**Standard Variation**")
            st.image(st.session_state.vto_standard, caption="VTO Complete", use_container_width=True)
        with col_r2:
            st.markdown("**No Accessories Variation**")
            st.image(st.session_state.vto_no_acc, caption="VTO: No Accessories Variation", use_container_width=True)

elif garment_image is not None and not st.session_state.base_vibe_standard:
    st.warning("Please generate Base Vibes first before synthesizing the garment.")

# Stage C: Optimization Workflow
if st.session_state.get('try_on_complete', False):
    st.markdown("---")
    st.markdown("### You've now placed the above images on your website and received orders.", unsafe_allow_html=True)
    st.markdown("<span style='font-size: 0.85em; font-weight: normal;'>Here is the data on sales: the dresses are selling in the size and location shown below.<br>You can tap Optimize to get an updated optimal image that you can add to your website</span><br><br>", unsafe_allow_html=True)
    
    if 'sim_size' not in st.session_state:
        st.session_state.sim_size = random.choice(["Small", "Medium", "Large"])
    if 'sim_location' not in st.session_state:
        st.session_state.sim_location = random.choice(["Mexico", "USA"])
        
    st.markdown(f"**Size:** {st.session_state.sim_size} &nbsp;&nbsp;|&nbsp;&nbsp; **Location:** {st.session_state.sim_location}")
    st.write("")
    
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        st.selectbox("Option: You can override Sales Results and Select the Dress Size & Location of Sales to Optimize for", ["Small", "Medium", "Large"], key="sim_size")
    with col_opt2:
        st.selectbox("Select Target Location", ["Mexico", "USA"], key="sim_location")
        
    st.write("")

    st.markdown("""
    <style>
    div.element-container:has(.optimize-marker) + div.element-container div[data-testid="stButton"] button {
        background-color: #ccfbf1 !important; 
        border-color: #99f6e4 !important;
    }
    div.element-container:has(.optimize-marker) + div.element-container div[data-testid="stButton"] button p {
        color: #0f766e !important;
        font-weight: 500 !important;
    }
    div.element-container:has(.optimize-marker) + div.element-container div[data-testid="stButton"] button:hover {
        background-color: #99f6e4 !important;
        border-color: #5eead4 !important;
    }
    div.element-container:has(.optimize-marker) + div.element-container div[data-testid="stButton"] button:hover p {
        color: #115e59 !important;
    }
    </style>
    <div class="optimize-marker" style="display: none;"></div>
    """, unsafe_allow_html=True)
    
    opt_submitted = st.button("Optimize Model Images", use_container_width=True)

    if opt_submitted:
        with st.spinner("Generating Optimized Vibes and re-running Virtual Try-On..."):
            opt_prompt = custom_scene_prompt + ", " if custom_scene_prompt.strip() else ""
            
            if st.session_state.sim_location == "Mexico":
                opt_prompt += "Change the model to a 30 to 40-year-old Latina Model with light brown hair and hazel eyes, "
            elif st.session_state.sim_location == "USA":
                opt_prompt += "Change the model to a 30 to 40-year-old Caucasian model with blonde hair and blue eyes, "
                
            if st.session_state.sim_size == "Small":
                opt_prompt += "and make the model petite in size"
            elif st.session_state.sim_size == "Medium":
                opt_prompt += "and keep the model size as is"
            elif st.session_state.sim_size == "Large":
                opt_prompt += "and make the model plus size"
                
            float_weights = {b: val / 100.0 for b, val in st.session_state.brand_weights.items()}
            opt_generated_images = inference.generate_base_vibe(float_weights, opt_prompt)
            
            if opt_generated_images and 'standard' in opt_generated_images and 'no_accessories' in opt_generated_images:
                st.session_state.opt_base_vibe_standard = opt_generated_images['standard']
                st.session_state.opt_base_vibe_no_acc = opt_generated_images['no_accessories']
                
                opt_res_standard = inference.synthesize_garment(
                    st.session_state.opt_base_vibe_standard, 
                    garment_image,
                    garment_category,
                    garment_desc
                )
                if isinstance(opt_res_standard, dict) and "error" in opt_res_standard:
                    st.error(opt_res_standard["error"])
                elif opt_res_standard:
                    st.session_state.opt_vto_standard = opt_res_standard
                
                opt_final_no_acc = inference.synthesize_garment(
                    st.session_state.opt_base_vibe_no_acc, 
                    garment_image,
                    garment_category,
                    garment_desc
                )
                if isinstance(opt_final_no_acc, dict) and "error" in opt_final_no_acc:
                    st.error(opt_final_no_acc["error"])
                elif opt_final_no_acc:
                    st.session_state.opt_vto_no_acc = opt_final_no_acc
                    
                st.session_state.opt_complete = True
                st.success("Optimization Virtual Try-On successfully completed!")
            else:
                if isinstance(opt_generated_images, dict) and "error" in opt_generated_images:
                    st.error(opt_generated_images["error"])
                else:
                    st.error("Failed to generate optimized base vibe.")
                
    if st.session_state.get('opt_complete', False) and 'opt_vto_standard' in st.session_state and 'opt_vto_no_acc' in st.session_state:
        st.markdown("### Optimized Try-On Results")
        _, col_o1, col_o2, _ = st.columns([1, 1, 1, 1])
        with col_o1:
            st.markdown("**Optimized Standard Variation**")
            st.image(st.session_state.opt_vto_standard, caption="Optimized VTO Complete", use_container_width=True)
        with col_o2:
            st.markdown("**Optimized No Accessories Variation**")
            st.image(st.session_state.opt_vto_no_acc, caption="Optimized VTO: No Accessories", use_container_width=True)

