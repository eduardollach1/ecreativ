import sys
import inference
import time
from PIL import Image

def main():
    print("Testing End-to-End VTO Pipeline directly...")
    
    # 1. Generate Base Vibe (Zara + Liu Jo)
    brand_weights = {
        "Zara": 0.70,
        "Liu Jo": 0.30,
        "Ralph Lauren": 0.0,
        "Liverpool": 0.0,
        "Neiman Marcus": 0.0,
        "Nordstrom": 0.0
    }
    print("Generating Base Vibe via Vertex AI...")
    base_vibe_dict = inference.generate_base_vibe(brand_weights)
    if not base_vibe_dict or "standard" not in base_vibe_dict:
        print("Failed to generate base vibe!")
        sys.exit(1)
    
    base_vibe = base_vibe_dict["standard"]
    base_vibe.save("test_base_vibe.jpg")
    print("Base vibe generated and saved as test_base_vibe.jpg")

    # 2. Load the test garment
    garment_path = "/Users/eduardo.llach/.gemini/antigravity/scratch/ecreativ/reference_images/Zara/01355011800-p copy.jpg"
    try:
        garment_image = Image.open(garment_path)
    except Exception as e:
        print(f"Failed to load garment image: {e}")
        sys.exit(1)

    # 3. Call synthesize_garment via Replicate IDM-VTON
    category = "upper_body"
    description = "A chic black and white blouse"
    
    print("\nCalling Replicate IDM-VTON...")
    start_time = time.time()
    final_image = inference.synthesize_garment(base_vibe, garment_image, category, description)
    end_time = time.time()
    
    if final_image == base_vibe or not final_image:
        print("VTO Synthesis Failed or returned unchanged base vibe.")
        sys.exit(1)
        
    final_image.save("test_vto_success.jpg")
    print(f"Success! VTO synthesis completed in {end_time - start_time:.2f} seconds.")
    print("Saved as test_vto_success.jpg")

if __name__ == "__main__":
    main()
