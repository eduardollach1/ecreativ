import os
import sys
import time
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

import inference

def test_real_vto():
    print("Testing Google VTO Pipeline with Real Images...")
    
    # Let's load the generated base vibe from Phase 3 caching
    brain_dir = "/Users/eduardo.llach/.gemini/antigravity/brain/4ef1eb20-617b-4854-84bd-5f6e7415d4a2"
    vibe_path = os.path.join(brain_dir, "phase3_test_base_vibe.jpg")
    garment_path = os.path.join(BASE_DIR, "vto_reference_image.jpeg") # User's red dress
    
    if not os.path.exists(garment_path):
        print(f"Garment not found at {garment_path}")
        return
        
    if not os.path.exists(vibe_path):
        print(f"Base Vibe not found at {vibe_path}")
        # Try another one
        vibe_path = os.path.join(brain_dir, "test_phase4_v1_base.jpg")
        if not os.path.exists(vibe_path):
            print("No cached test vibes found. Need real images.")
            return

    person_img = Image.open(vibe_path).convert("RGB")
    garment_img = Image.open(garment_path).convert("RGB")
    
    print(f"Loaded Person: {person_img.size}")
    print(f"Loaded Garment: {garment_img.size}")
    
    try:
        start = time.time()
        result = inference.synthesize_garment(
            base_vibe_image=person_img,
            garment_image=garment_img,
            category="dresses",
            garment_desc="Red floral dress"
        )
        duration = time.time() - start
        
        if result:
            print(f"SUCCESS! Rendered in {duration:.2f} seconds.")
            output_path = os.path.join(brain_dir, "phase7_google_vto_success.jpg")
            result.save(output_path)
            print(f"Saved real VTO test output to {output_path}")
        else:
            print("FAILED! synthesize_garment returned None")
    
    except Exception as e:
        print(f"FAILED with unexpected exception: {e}")

if __name__ == "__main__":
    test_real_vto()
