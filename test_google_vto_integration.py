import os
import io
import time
from PIL import Image
from pathlib import Path

# Fix the import path to find `inference` locally
import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

import inference

def test():
    print("Testing Google VTO Pipeline in codebase...")
    
    # 1. Create a dummy base person image and dummy garment
    person_img = Image.new('RGB', (1024, 1024), color='white')
    garment_img = Image.new('RGB', (1024, 1024), color='black')
    
    # 2. Call synthesize_garment directly
    try:
        start = time.time()
        result = inference.synthesize_garment(
            base_vibe_image=person_img,
            garment_image=garment_img,
            category="dresses",
            garment_desc="Test black dress"
        )
        duration = time.time() - start
        
        if result:
            print(f"SUCCESS! Rendered in {duration:.2f} seconds.")
            output_path = os.path.join(BASE_DIR, "google_vto_integration_success.jpg")
            result.save(output_path)
            print(f"Saved test output to {output_path}")
        else:
            print("FAILED! synthesize_garment returned None")
    
    except Exception as e:
        print(f"FAILED with unexpected exception: {e}")

if __name__ == "__main__":
    test()
