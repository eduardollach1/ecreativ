import os
import io
import json
import base64
import math
import requests
from PIL import Image
from dotenv import load_dotenv
import replicate

import google.generativeai as genai
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")

def get_client_secret_file():
    for f in os.listdir(BASE_DIR):
        if f.startswith("client_secret_") and f.endswith(".json"):
            return os.path.join(BASE_DIR, f)
    raise FileNotFoundError("Could not find client_secret_...json")

def authenticate():
    client_secret_file = get_client_secret_file()
    SCOPES = ['https://www.googleapis.com/auth/cloud-platform']
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
    client_secret_file = get_client_secret_file()
    with open(client_secret_file, "r") as f:
        client_config = json.load(f)
        PROJECT_ID = client_config.get("installed", {}).get("project_id", "gen-lang-client-0232437645")
    
    creds = authenticate()
    vertexai.init(project=PROJECT_ID, location="us-central1", credentials=creds)

def load_vibe_config():
    with open(os.path.join(BASE_DIR, "vibe_config.json"), "r") as f:
        return json.load(f)

def generate_base_vibe(brand_weights, custom_scene_prompt=None):
    """
    Simulates Stage A: The Brand Mixer inside Phase 4.
    Takes sliding weights & custom text overrides, blends them mathematically 
    into TWO prompts using Gemini Text Synthesis (With and Without Accessories), 
    and renders both results using Imagen 3 via Vertex AI.
    """
    config = load_vibe_config()
    total_weight = sum(brand_weights.values())
    if total_weight == 0:
        return None

    # Step 1: Collect Phase 1 Master Prompts
    prompt_ingredients = []
    for brand, weight in brand_weights.items():
        if weight > 0:
            traits = config.get(brand, {})
            master_p = traits.get("master_prompt", "")
            brand_desc = f"[Brand: {brand}, Weight: {weight:.2f}, Characteristic: {master_p}]"
            prompt_ingredients.append(brand_desc)

    print("Phase 4: Collected prompt ingredients based on sliders:")
    for pi in prompt_ingredients:
        print(f" - {pi}")
    
    # Step 2: Use Gemini 1.5 Pro to blend them into distinct variations
    print("\nAsking Gemini 1.5 Pro to synthesize the final Phase 4 Vibe prompts...")
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel("nano-banana-pro-preview")
    
    blending_prompt = (
        "You are an expert fashion AI. I have several 'master prompts' from different clothing brands, "
        "and a weight for how much influence each brand should have. "
        "I need you to synthesize these descriptions into TWO highly-detailed text prompts (under 100 words each) "
        "for an image generator. Mathematically blend the model traits, poses, and clothing based on the weights provided.\n"
    )
    
    if custom_scene_prompt and custom_scene_prompt.strip():
        blending_prompt += f"\nCRITICAL CONSTRAINT: The user has requested the following custom override: '{custom_scene_prompt}'. You MUST incorporate this exactly into both prompts, overriding any conflicting background or pose from the brand traits.\n"

    blending_prompt += (
        "\nPrompt 1 (standard): A cohesive fashion photograph retaining any accessories (like purses, bags, jackets, sunglasses) mentioned in the traits or custom constraint.\n"
        "Prompt 2 (no_accessories): The exact same cohesive fashion photograph, EXCEPT you must strictly REMOVE all accessories (no purses, no bags, no jackets, no sunglasses) so that the focus is purely on the core garment and shoes.\n\n"
        "Return ONLY a valid JSON object matching this schema exactly, nothing else. No markdown wrappers:\n"
        '{\n  "standard": "...",\n  "no_accessories": "..."\n}\n\n'
        "Here are the ingredients:\n" + "\n".join(prompt_ingredients)
    )
    
    try:
        response = model.generate_content(blending_prompt)
        text_resp = response.text.strip()
        # Clean markdown codeblocks if Gemini adds them
        if text_resp.startswith("```"):
            text_resp = text_resp.split("```json")[-1].split("```")[0].strip()
        if text_resp.startswith("```"):
             text_resp = text_resp.split("```")[-1].split("```")[0].strip()
             
        final_prompts = json.loads(text_resp)
        print(f"Blended Prompts Successful:\nStandard: {final_prompts.get('standard')}\nNo Acc: {final_prompts.get('no_accessories')}\n")
    except Exception as e:
        print(f"Failed to synthesize blended prompt JSON: {e}\nRaw Response: {response.text}")
        return None
        
    # Step 3: Use Imagen 3 to render BOTH blended prompts
    print("Pinging Vertex AI Imagen 3 to dynamically render both Vibes...")
    results = {}
    try:
        init_vertex_ai()
        imagen_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        
        for key, prompt in final_prompts.items():
            print(f"Generating Imagen 3 render for {key}...")
            response = imagen_model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="3:4"
            )
            if response.images:
                output_path = os.path.join(BASE_DIR, f"temp_blend_{key}.jpg")
                response.images[0].save(output_path)
                results[key] = Image.open(output_path).convert("RGB")
                
        print("Latent Space Image calculations complete!")
        return results if len(results) == 2 else None
    except Exception as e:
        print(f"Imagen 3 Generation failed: {e}")
        return None

def synthesize_garment(base_vibe_image, garment_image, category, garment_desc):
    """
    Executes Stage B: Garment Synthesis (Virtual Try-On).
    Pipes the physical Vertex AI Base Vibe, User's Garment, category text, 
    and description text directly to Replicate's IDM-VTON endpoint.
    """
    try:
        print(f"Triggering IDM-VTON with category: {category} | desc: {garment_desc}")
        
        # We must buffer the PIL images to bytes so the Replicate SDK can upload them
        human_img_bytes = io.BytesIO()
        base_vibe_image.save(human_img_bytes, format="JPEG")
        human_img_bytes.seek(0)
        
        garm_img_bytes = io.BytesIO()
        garment_image.convert("RGB").save(garm_img_bytes, format="JPEG")
        garm_img_bytes.seek(0)

        # Call the idm-vton model
        output = replicate.run(
            "cuuupid/idm-vton:c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4",
            input={
                "crop": False,
                "seed": 42,
                "steps": 30,
                "category": category,
                "force_dc": False if category != "dresses" else True,
                "garm_img": garm_img_bytes,
                "human_img": human_img_bytes,
                "garment_des": garment_desc
            }
        )
        
        print(f"IDM-VTON finished successfully. Generated output URL: {output}")
        # Parse the output
        if output:
            response = requests.get(output)
            return Image.open(io.BytesIO(response.content))
        return base_vibe_image 
        
    except Exception as e:
        print(f"Error in VTO synthesis: {e}")
        return None
