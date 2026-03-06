import streamlit as st
from PIL import Image
import io
import inference

st.set_page_config(page_title="eCreativ V1.0 - The Fashion Vibe-Engine", layout="wide")

st.title("eCreativ V1.0")
st.subheader("The Fashion Vibe-Engine")

# Stage A: The Brand Mixer
st.header("Stage A: The Brand Mixer")
st.write("Adjust the sliders to synthesize a 'Brand Average'. The model, pose, and lighting will dynamically interpolate between the selected brand DNAs.")

# Define the 6 brands
brands = ["Ralph Lauren", "Liu Jo", "Zara", "Liverpool", "Neiman Marcus", "Nordstrom"]
brand_weights = {}

col1, col2, col3 = st.columns(3)

with col1:
    brand_weights[brands[0]] = st.slider(brands[0], 0.0, 1.0, 0.5, 0.1)
    brand_weights[brands[1]] = st.slider(brands[1], 0.0, 1.0, 0.0, 0.1)
with col2:
    brand_weights[brands[2]] = st.slider(brands[2], 0.0, 1.0, 0.5, 0.1)
    brand_weights[brands[3]] = st.slider(brands[3], 0.0, 1.0, 0.0, 0.1)
with col3:
    brand_weights[brands[4]] = st.slider(brands[4], 0.0, 1.0, 0.0, 0.1)
    brand_weights[brands[5]] = st.slider(brands[5], 0.0, 1.0, 0.0, 0.1)

custom_scene_prompt = st.text_area("Custom Scene/Pose Prompt (Optional)", placeholder="e.g. Model sitting at a Parisian cafe holding a red umbrella")

# Initialize session state for the generated base vibes
if 'base_vibe_standard' not in st.session_state:
    st.session_state.base_vibe_standard = None
if 'base_vibe_no_acc' not in st.session_state:
    st.session_state.base_vibe_no_acc = None

if st.button("Generate Base Vibe"):
    with st.spinner("Synthesizing vibe (Standard & No Accessories)..."):
        print(f"DEBUG APP.PY - Calling inference with weights: {brand_weights}")
        generated_images = inference.generate_base_vibe(brand_weights, custom_scene_prompt)
        if generated_images and 'standard' in generated_images and 'no_accessories' in generated_images:
            st.session_state.base_vibe_standard = generated_images['standard']
            st.session_state.base_vibe_no_acc = generated_images['no_accessories']
            st.success("Base Vibes generated successfully!")
        else:
            st.error("Failed to generate base vibe. Ensure at least one weight > 0.")

if st.session_state.base_vibe_standard and st.session_state.base_vibe_no_acc:
    st.write("### Generated Base Vibes")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.image(st.session_state.base_vibe_standard, caption="Variation 1: Standard (With Accessories)", use_container_width=True)
    with col_v2:
        st.image(st.session_state.base_vibe_no_acc, caption="Variation 2: No Accessories (Just Garment & Shoes)", use_container_width=True)

# Stage B: Garment Synthesis
st.header("Stage B: Garment Synthesis (Virtual Try-On)")
st.write("Upload a custom garment (e.g., a cocktail dress) to drape onto the synthesized model.")

uploaded_garment = st.file_uploader("Upload Garment Image (PNG/JPG)", type=["png", "jpg", "jpeg"])

col_g1, col_g2 = st.columns(2)
with col_g1:
    garment_category = st.selectbox("Garment Category", ["upper_body", "lower_body", "dresses"])
with col_g2:
    garment_desc = st.text_input("Garment Description (Optional)", placeholder="e.g. cute pink top, long black dress")

if st.session_state.base_vibe_standard and st.session_state.base_vibe_no_acc and uploaded_garment is not None:
    garment_image = Image.open(uploaded_garment)
    st.image(garment_image, caption="Uploaded Garment", width=200)
    
    if st.button("Synthesize Garment"):
        with st.spinner("Executing Virtual Try-On via Replicate IDM-VTON on BOTH variations..."):
            col_r1, col_r2 = st.columns(2)
            
            with col_r1:
                st.write("Synthesizing Standard Variation...")
                final_standard = inference.synthesize_garment(
                    st.session_state.base_vibe_standard, 
                    garment_image,
                    garment_category,
                    garment_desc
                )
                if final_standard:
                    st.image(final_standard, caption="VTO: Standard Variation", use_container_width=True)
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
