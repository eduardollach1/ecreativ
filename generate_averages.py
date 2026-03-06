import os
import io
import time
import json
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

load_dotenv()

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REFERENCE_DIR = os.path.join(BASE_DIR, "reference_images")
AVERAGES_DIR = os.path.join(BASE_DIR, "reference_images_averages")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")

# Ensure output directory exists
os.makedirs(AVERAGES_DIR, exist_ok=True)

# Find the client secret file
client_secret_file = None
for f in os.listdir(BASE_DIR):
    if f.startswith("client_secret_") and f.endswith(".json"):
        client_secret_file = os.path.join(BASE_DIR, f)
        break

if not client_secret_file:
    print("Error: Could not find client_secret_...json in directory.")
    exit(1)

# Extract GCP Project ID dynamically from the client config
with open(client_secret_file, "r") as f:
    client_config = json.load(f)
    PROJECT_ID = client_config.get("installed", {}).get("project_id", "gen-lang-client-0232437645")

LOCATION = "us-central1"
SCOPES = ['https://www.googleapis.com/auth/cloud-platform']

def authenticate():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds

def init_vertex_ai():
    creds = authenticate()
    vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=creds)

def synthesize_prompt(brand_name, image_paths):
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("nano-banana-pro-preview")
    
    parts = []
    prompt_text = f"You are an expert fashion editorial creative director. Analyze the provided {len(image_paths)} images from the brand '{brand_name}'. Determine the mathematical 'average' of the model's appearance, the dominant pose, the exact style of the garments, the texture, and the background environment. Output ONLY a single, highly-detailed text prompt (under 100 words) that synthesizes these commonalities into one perfect fashion photograph. Do not include any introductory or concluding text. Be highly descriptive about lighting, model features, and clothing."
    parts.append(prompt_text)
    
    for img_path in image_paths:
        img = Image.open(img_path)
        parts.append(img)
            
    response = model.generate_content(parts)
    return response.text.strip()

def generate_average_image(brand_name, prompt):
    print(f"Generating image for {brand_name} with prompt: {prompt}")
    model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
    
    response = model.generate_images(
        prompt=prompt,
        number_of_images=1,
        aspect_ratio="3:4" 
    )
    
    if response.images:
        output_path = os.path.join(AVERAGES_DIR, f"{brand_name}_average.jpg")
        response.images[0].save(output_path)
        print(f"Saved {output_path}")
        return True
    return False

def main():
    print("Initializing Vertex AI...")
    init_vertex_ai()
    
    brands = [d for d in os.listdir(REFERENCE_DIR) if os.path.isdir(os.path.join(REFERENCE_DIR, d))]
    
    for brand in brands:
        print(f"\n--- Processing Brand: {brand} ---")
        brand_dir = os.path.join(REFERENCE_DIR, brand)
        output_path = os.path.join(AVERAGES_DIR, f"{brand}_average.jpg")
        
        if os.path.exists(output_path):
            print(f"Average already exists for {brand}! Skipping.")
            continue
            
        image_files = [os.path.join(brand_dir, f) for f in os.listdir(brand_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not image_files:
            print(f"No images found for {brand}. Skipping.")
            continue
            
        print(f"Found {len(image_files)} reference images. Asking Gemini 1.5 Pro to synthesize average prompt...")
        try:
            average_prompt = synthesize_prompt(brand, image_files)
            print(f"Gemini output prompt:\n{average_prompt}\n")
            
            print("Pinging Imagen 3 for physical generation...")
            if generate_average_image(brand, average_prompt):
                print("Sleeping for 45 seconds to respect Vertex AI quotas...")
                time.sleep(45)
        except Exception as e:
            print(f"Failed to process {brand}: {str(e)}")

if __name__ == "__main__":
    main()
