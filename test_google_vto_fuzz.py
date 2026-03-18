import io
import base64
import requests
from PIL import Image
import inference

PROJECT_ID = "gen-lang-client-0232437645"
LOCATION = "us-central1"

def test_payload_fuzz():
    creds = inference.authenticate()
    from google.auth.transport.requests import Request
    if not creds.token:
        creds.refresh(Request())
    
    url = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/virtual-try-on-001:predict"
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    img1 = Image.new('RGB', (100, 100), color = 'red')
    buf1 = io.BytesIO()
    img1.save(buf1, format="JPEG")
    b64_img = base64.b64encode(buf1.getvalue()).decode('utf-8')

    keys_to_test = [
        ("image", "productImage"),
        ("image", "garmentImage"),
        ("personImage", "productImage"),
        ("referenceImage", "productImage"),
        ("image", "clothingImage"),
        ("modelImage", "garmentImage"),
        ("imageBase64", "referenceImageBase64"),
        ("person", "clothing")
    ]

    for k1, k2 in keys_to_test:
        payload = {
            "instances": [
                {
                    k1: {"bytesBase64Encoded": b64_img},
                    k2: {"bytesBase64Encoded": b64_img}
                }
            ],
            "parameters": {"sampleCount": 1}
        }
        
        resp = requests.post(url, headers=headers, json=payload)
        print(f"Testing {k1} / {k2} -> Status: {resp.status_code}")
        if resp.status_code != 400 or "should be provided" not in resp.text:
            print("Response:", resp.text)
            break
        elif "A product image should be provided." in resp.text:
            print("  - Missing product image")
        elif "A person image should be provided" in resp.text:
            print("  - Missing person image")
        else:
            print("Response:", resp.text)

if __name__ == "__main__":
    test_payload_fuzz()
