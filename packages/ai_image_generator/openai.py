"""OpenAI GPT-Image generation functions."""

import base64
import os
from typing import Optional

import requests

from .utils import OPENAI_IMAGE_MODEL


def generate_openai_image(prompt: str, output_path: str, size: str = "1024x1024") -> Optional[str]:
    """Generate image using OpenAI GPT-Image API (gpt-image-1-mini by default for cost efficiency)."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("No OpenAI API key found for fallback.")
        return None

    model = OPENAI_IMAGE_MODEL

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": size
        }

        print(f"Requesting OpenAI {model} image...")
        response = requests.post("https://api.openai.com/v1/images/generations", json=data, headers=headers, timeout=60)

        if response.status_code == 200:
            result = response.json()
            if 'data' in result and result['data']:
                img_item = result['data'][0]

                if 'b64_json' in img_item and img_item['b64_json']:
                    with open(output_path, 'wb') as f:
                        f.write(base64.b64decode(img_item['b64_json']))
                    print(f"[OK] Generated image using OpenAI {model} (base64)")
                    return output_path
                elif 'url' in img_item and img_item['url']:
                    img_response = requests.get(img_item['url'], timeout=30)
                    if img_response.status_code == 200:
                        with open(output_path, 'wb') as f:
                            f.write(img_response.content)
                        print(f"[OK] Generated image using OpenAI {model} (URL)")
                        return output_path
        else:
            error_text = response.text[:200] if response.text else "No error message"
            print(f"OpenAI {model} returned {response.status_code}: {error_text}")
    except Exception as e:
        print(f"OpenAI image generation failed: {e}")

    return None
