import io
import os
import inference
from PIL import Image

try:
    from google import genai
    from google.genai.types import RecontextImageSource, ProductImage, RecontextImageConfig, Image as SDKImage
except ImportError as e:
    print(f"Import Error: {e}")
    exit(1)

PROJECT_ID = "gen-lang-client-0232437645"
LOCATION = "us-central1"

def test_vto_sdk():
    # Make sure we have credentials
    creds = inference.authenticate()
    from google.auth.transport.requests import Request
    if not creds.token:
        creds.refresh(Request())
        
    print("Initializing genai client...")
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION, credentials=creds)
    
    # Create valid synthetic images for person and garment
    person_img = Image.new('RGB', (300, 400), color='white')
    garment_img = Image.new('RGB', (300, 400), color='red')
    
    buf1 = io.BytesIO()
    person_img.save(buf1, format="JPEG")
    sdk_person = SDKImage(image_bytes=buf1.getvalue())
    
    buf2 = io.BytesIO()
    garment_img.save(buf2, format="JPEG")
    sdk_garment = SDKImage(image_bytes=buf2.getvalue())
    
    print("Calling recontext_image...")
    try:
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
        print("Success! SDK VTO Generated.")
        if response.generated_images:
            print("Successfully extracted generated image.")
    except Exception as e:
        print(f"Virtual Try-On SDK Error: {e}")

if __name__ == "__main__":
    test_vto_sdk()
