import sys
import inference
import time
from PIL import Image

def main():
    print("Testing Phase 4 End-to-End Pipeline (Prompt Modification & Dual Accessory Rendering)...")
    
    # 1. Generate Base Vibe with a Custom Scene
    brand_weights = {
        "Zara": 0.50,
        "Liu Jo": 0.50,
        "Ralph Lauren": 0.0,
        "Liverpool": 0.0,
        "Neiman Marcus": 0.0,
        "Nordstrom": 0.0
    }
    
    custom_scene = "Model is sitting elegantly at a small Parisian cafe table outdoors, holding a coffee."
    print(f"Generating Base Vibes via Vertex AI... with Custom Scene: '{custom_scene}'")
    
    base_vibes = inference.generate_base_vibe(brand_weights, custom_scene)
    
    if not base_vibes or 'standard' not in base_vibes or 'no_accessories' not in base_vibes:
        print("Failed to generate dual base vibes!")
        sys.exit(1)
        
    v1 = base_vibes['standard']
    v2 = base_vibes['no_accessories']
    
    v1.save("test_phase4_v1_base.jpg")
    v2.save("test_phase4_v2_base_no_acc.jpg")
    print("Base vibes generated. Checking them...")

    # 2. Load the test garment
    garment_path = "/Users/eduardo.llach/.gemini/antigravity/scratch/ecreativ/reference_images/Zara/01355011800-p copy.jpg"
    try:
        garment_image = Image.open(garment_path)
    except Exception as e:
        print(f"Failed to load garment image: {e}")
        sys.exit(1)

    # 3. Call synthesize_garment via Replicate IDM-VTON for BOTH
    category = "upper_body"
    description = "A chic black and white blouse"
    
    print("\nCalling Replicate IDM-VTON for Variation 1 (Standard)...")
    start_time = time.time()
    final_v1 = inference.synthesize_garment(v1, garment_image, category, description)
    print(f"V1 VTO took {time.time() - start_time:.2f}s")
    
    print("\nCalling Replicate IDM-VTON for Variation 2 (No Accessories)...")
    start_time = time.time()
    final_v2 = inference.synthesize_garment(v2, garment_image, category, description)
    print(f"V2 VTO took {time.time() - start_time:.2f}s")
    
    if final_v1:
        final_v1.save("test_phase4_v1_vto_success.jpg")
    if final_v2:
        final_v2.save("test_phase4_v2_vto_no_acc_success.jpg")
        
    print("Tests finished successfully! Check the output directory.")

if __name__ == "__main__":
    main()
