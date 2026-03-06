import os
from dotenv import load_dotenv
load_dotenv()
import replicate

try:
    models = replicate.models.search('ip-adapter')
    for m in models[:15]:
        try:
            schema = m.versions.list()[0].openapi_schema['components']['schemas']['Input']['properties']
            keys = list(schema.keys())
            if 'image' in keys or 'image_prompt' in keys or 'ip_adapter_image' in keys or 'image_1' in keys:
                print(f"FOUND: {m.owner}/{m.name}")
                print(f"Keys: {keys}")
        except Exception as e:
            continue
except Exception as e:
    print(f"Search failed: {e}")
