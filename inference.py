import os
import io
import json
import base64
import math
import requests
from PIL import Image
from dotenv import load_dotenv
import replicate

import google.generativeai as legacy_genai
from google import genai
from google.genai.types import RecontextImageSource, ProductImage, RecontextImageConfig, Image as SDKImage
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import google.auth
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

def get_vertex_credentials():
    # 1. Permanent Cloud Auth: Check for Hugging Face Secret / Env Var
    gcp_sa_key = os.environ.get("GCP_SA_KEY")
    if gcp_sa_key:
        try:
            sa_info = json.loads(gcp_sa_key)
            creds = service_account.Credentials.from_service_account_info(sa_info)
            PROJECT_ID = sa_info.get("project_id", "gen-lang-client-0232437645")
            print("Successfully loaded Vertex AI creds via GCP_SA_KEY environment variable.")
            return PROJECT_ID, creds
        except Exception as e:
            print(f"Failed to load GCP_SA_KEY Secret: {e}")

    # 2. Permanent Local Auth: Check for local service_account.json
    sa_file = os.path.join(BASE_DIR, "service_account.json")
    if os.path.exists(sa_file):
        try:
            creds = service_account.Credentials.from_service_account_file(sa_file)
            with open(sa_file, 'r') as f:
                PROJECT_ID = json.load(f).get("project_id", "gen-lang-client-0232437645")
            print("Successfully loaded Vertex AI creds via local service_account.json.")
            return PROJECT_ID, creds
        except Exception as e:
            print(f"Failed to load service_account.json: {e}")

    # 3. Fallback: Cloud Run Native ADC
    try:
        if os.environ.get("K_SERVICE") or os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            creds, project_id = google.auth.default()
            PROJECT_ID = project_id or "gen-lang-client-0232437645"
            print("Successfully loaded Vertex AI creds via Google Cloud ADC.")
            return PROJECT_ID, creds
    except Exception as e:
        print(f"Fallback to ADC failed: {e}")

    # 4. Final Fallback: The 24-hour Temporary OAuth Login
    print("Falling back to temporary 24-hour OAuth Token Login...")
    client_secret_file = get_client_secret_file()
    with open(client_secret_file, "r") as f:
        client_config = json.load(f)
        PROJECT_ID = client_config.get("installed", {}).get("project_id", "gen-lang-client-0232437645")
    
    creds = authenticate()
    if creds and not creds.valid:
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
    return PROJECT_ID, creds

def init_vertex_ai():
    project_id, creds = get_vertex_credentials()
    vertexai.init(project=project_id, location="us-central1", credentials=creds)

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
    
    # Step 2: Use Gemini to blend them into distinct variations
    print("\nAsking Gemini to synthesize the final Phase 4 Vibe prompts...")
    legacy_genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    
    # Using the exact preview alias corresponding to Gemini 3 Pro on your account
    model = legacy_genai.GenerativeModel("models/gemini-3-pro-preview")
    
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
        raw_res = response.text if 'response' in locals() and hasattr(response, 'text') else "No response object"
        print(f"Failed to synthesize blended prompt JSON: {e}\nRaw Response: {raw_res}")
        return {"error": f"Gemini Prompt Synthesis Failed: {str(e)}"}
        
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
        return results if len(results) == 2 else {"error": "Imagen 3 returned partial results."}
    except Exception as e:
        print(f"Imagen 3 Generation failed: {e}")
        import traceback
        return {"error": f"Imagen 3 API Error: {str(e)}\nTraceback: {traceback.format_exc()}"}

def synthesize_garment(base_vibe_image, garment_image, category, garment_desc):
    """
    Executes Stage B: Google Vertex AI Native Virtual Try-On.
    Pipes the physical Vertex AI Base Vibe and User's Garment natively
    into the virtual-try-on-001 model for pristine photorealism.
    """
    try:
        print(f"Triggering virtual-try-on-001 with category: {category} | desc: {garment_desc}")
        
        project_id, creds = get_vertex_credentials()
            
        client = genai.Client(
            vertexai=True, 
            project=project_id, 
            location="us-central1", 
            credentials=creds
        )
        
        # Compress PIL images to bytes, then wrap in SDKImage
        human_img_bytes = io.BytesIO()
        base_vibe_image.save(human_img_bytes, format="JPEG")
        sdk_person = SDKImage(image_bytes=human_img_bytes.getvalue())
        
        garm_img_bytes = io.BytesIO()
        garment_image.convert("RGB").save(garm_img_bytes, format="JPEG")
        sdk_garment = SDKImage(image_bytes=garm_img_bytes.getvalue())

        response = client.models.recontext_image(
            model="virtual-try-on-001",
            source=RecontextImageSource(
                person_image=sdk_person,
                product_images=[
                    ProductImage(product_image=sdk_garment)
                ],
            ),
            config=RecontextImageConfig(
                output_mime_type="image/jpeg",
                number_of_images=1,
            )
        )
        
        print(f"Google Native VTO finished successfully.")
        if response.generated_images:
            return Image.open(io.BytesIO(response.generated_images[0].image.image_bytes)).convert("RGB")
        return base_vibe_image 
        
    except Exception as e:
        print(f"Error in Vertex VTO synthesis: {e}")
        import traceback
        return {"error": f"**Google Virtual Try-On Engine Failed:** {str(e)}\n\n*Traceback:* {traceback.format_exc()}"}
