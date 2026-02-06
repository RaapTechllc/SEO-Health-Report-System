"""Gemini/Imagen image and text generation functions."""

import base64
import os
from io import BytesIO
from typing import Optional

import httpx
from PIL import Image as PILImage

from .openai import generate_openai_image
from .utils import GEMINI_IMAGE_MODEL, GEMINI_TEXT_MODEL, OPENAI_IMAGE_MODEL


def generate_gemini_summary(company_name: str, score: int, grade: str,
                            tech_score: int, content_score: int, ai_score: int,
                            industry: str) -> Optional[str]:
    """Generate executive summary using Gemini."""
    api_key = os.environ.get('GOOGLE_GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        return None

    prompt = f"""Write a brief, professional executive summary (3-4 sentences) for an SEO health report.

Company: {company_name}
Industry: {industry}
Overall Score: {score}/100 (Grade: {grade})
Technical SEO: {tech_score}/100
Content & Authority: {content_score}/100
AI Visibility: {ai_score}/100

Use appropriate emojis (✅, ⚠️, 🚨, 📈, 🎯) sparingly.
Be specific about what's working and what needs attention.
End with an encouraging but actionable statement.
Keep it professional and suitable for a C-level executive."""

    try:
        model = GEMINI_TEXT_MODEL
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
        response = httpx.post(url, json={
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.7}
        }, timeout=30)

        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"Gemini text API ({model}) returned {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"Gemini summary generation failed: {e}")

    return None


def generate_gemini_score_badge(score: int, grade: str, company_name: str, output_path: str) -> Optional[str]:
    """Generate a premium score badge using Gemini Imagen."""
    api_key = os.environ.get('GOOGLE_GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        return None

    if score >= 80:
        color_desc = "green, success, healthy"
    elif score >= 60:
        color_desc = "yellow-orange, caution, warning"
    else:
        color_desc = "red-orange, alert, critical"

    prompt = f"""Create a premium circular score gauge visualization for a business report:

DESIGN REQUIREMENTS:
- Clean circular progress ring showing {score}% filled
- Large "{score}" number in center (bold)
- "out of 100" smaller text below the number
- Grade letter "{grade}" in a colored badge below
- Color theme: {color_desc} gradient for the filled portion
- Unfilled portion in light gray
- White background
- Subtle drop shadow for depth
- Modern, flat design aesthetic
- Professional consulting report quality (McKinsey/Deloitte style)
- 1:1 square aspect ratio
- NO company name or extra text"""

    try:
        model = GEMINI_IMAGE_MODEL

        def decode_and_save(img_b64, path):
            if img_b64:
                with open(path, 'wb') as f:
                    f.write(base64.b64decode(img_b64))
                print(f"[OK] Generated Gemini score badge using {model}")
                return path
            return None

        if "gemini" in model.lower():
            url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
            response = httpx.post(url, json={
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'response_mime_type': 'image/jpeg'}
            }, timeout=60)

            if response.status_code == 200:
                data = response.json()
                try:
                    candidates = data.get('candidates', [])
                    if candidates:
                        parts = candidates[0].get('content', {}).get('parts', [])
                        for part in parts:
                            if 'inline_data' in part:
                                if decode_and_save(part['inline_data'].get('data'), output_path):
                                    return output_path
                except Exception:
                    pass
        else:
            url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={api_key}'
            response = httpx.post(url, json={
                'instances': [{'prompt': prompt}],
                'parameters': {'sampleCount': 1, 'aspectRatio': '1:1'}
            }, timeout=60)

            if response.status_code == 200:
                data = response.json()
                if 'predictions' in data and data['predictions']:
                    if decode_and_save(data['predictions'][0].get('bytesBase64Encoded'), output_path):
                        return output_path

        if response.status_code != 200:
            print(f"Gemini badge API ({model}) returned {response.status_code}")
    except Exception as e:
        print(f"Gemini badge generation failed: {e}")

    print(f"Trying OpenAI {OPENAI_IMAGE_MODEL} fallback for badge...")
    return generate_openai_image(prompt, output_path, "1024x1024")


def generate_gemini_header_image(company_name: str, industry: str, output_path: str) -> Optional[str]:
    """Generate a professional header banner using Gemini Imagen."""
    api_key = os.environ.get('GOOGLE_GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        return None

    prompt = f"""Create a subtle professional header banner for a business report:

DESIGN:
- Abstract geometric pattern with flowing lines
- {industry} industry aesthetic (subtle visual cues)
- Primary colors: deep blue (#1a73e8) and dark gray (#202124)
- Gradient flowing from left to right
- Modern, minimal, corporate style
- NO text, logos, or words
- Suitable as PDF report header decoration
- 16:9 wide aspect ratio
- Premium consulting firm report cover style"""

    try:
        model = GEMINI_IMAGE_MODEL

        def decode_and_save(img_b64, path):
            if img_b64:
                with open(path, 'wb') as f:
                    f.write(base64.b64decode(img_b64))
                print(f"[OK] Generated Gemini header image using {model}")
                return path
            return None

        if "gemini" in model.lower():
            url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
            response = httpx.post(url, json={
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'response_mime_type': 'image/jpeg'}
            }, timeout=60)

            if response.status_code == 200:
                data = response.json()
                try:
                    candidates = data.get('candidates', [])
                    if candidates:
                        parts = candidates[0].get('content', {}).get('parts', [])
                        for part in parts:
                            if 'inline_data' in part:
                                if decode_and_save(part['inline_data'].get('data'), output_path):
                                    return output_path
                except Exception:
                    pass
        else:
            url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={api_key}'
            response = httpx.post(url, json={
                'instances': [{'prompt': prompt}],
                'parameters': {'sampleCount': 1, 'aspectRatio': '16:9'}
            }, timeout=60)

            if response.status_code == 200:
                data = response.json()
                if 'predictions' in data and data['predictions']:
                    if decode_and_save(data['predictions'][0].get('bytesBase64Encoded'), output_path):
                        return output_path

        if response.status_code != 200:
            print(f"Gemini header API ({model}) returned {response.status_code}")
    except Exception as e:
        print(f"Gemini header generation failed: {e}")

    print(f"Trying OpenAI {OPENAI_IMAGE_MODEL} fallback for header...")
    return generate_openai_image(prompt, output_path, "1024x1024")


def generate_gemini_logo(company_name: str, industry: str, output_path: str) -> Optional[str]:
    """Generate a minimal company logo using Gemini Imagen as fallback."""
    api_key = os.environ.get('GOOGLE_GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        return None

    prompt = f"""Design a clean, modern, compliant minimalist logo for a company named "{company_name}".

    INDUSTRY: {industry}
    STYLE: Professional, vector-style, flat design, icon + text
    COLORS: Professional corporate colors (Navy, Blue, or Dark Grey)
    BACKGROUND: White (clean)

    REQUIREMENTS:
    - High contrast
    - Legible text
    - No photographic elements
    - 1:1 square aspect ratio"""

    try:
        model = GEMINI_IMAGE_MODEL

        def save_b64_image(b64_str, path):
            if not b64_str:
                return False
            try:
                img_bytes = base64.b64decode(b64_str)
                img = PILImage.open(BytesIO(img_bytes))
                img.verify()

                img = PILImage.open(BytesIO(img_bytes))
                img.save(path, 'PNG')
                print(f"[OK] Generated Gemini logo using {model}")
                return True
            except Exception as e:
                print(f"Gemini logo validation failed: {e}")
                return False

        if "gemini" in model.lower():
            url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
            response = httpx.post(url, json={
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'response_mime_type': 'image/jpeg'}
            }, timeout=60)

            if response.status_code == 200:
                data = response.json()
                try:
                    candidates = data.get('candidates', [])
                    if candidates:
                        parts = candidates[0].get('content', {}).get('parts', [])
                        for part in parts:
                            if 'inline_data' in part:
                                if save_b64_image(part['inline_data'].get('data'), output_path):
                                    return output_path
                except Exception:
                    pass
        else:
            url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={api_key}'
            response = httpx.post(url, json={
                'instances': [{'prompt': prompt}],
                'parameters': {'sampleCount': 1, 'aspectRatio': '1:1'}
            }, timeout=60)

            if response.status_code == 200:
                data = response.json()
                if 'predictions' in data and data['predictions']:
                    if save_b64_image(data['predictions'][0].get('bytesBase64Encoded'), output_path):
                        return output_path

        if response.status_code != 200:
            print(f"Gemini logo API ({model}) returned {response.status_code}")
    except Exception as e:
        print(f"Gemini logo generation failed: {e}")

    print(f"Trying OpenAI {OPENAI_IMAGE_MODEL} fallback for logo...")
    return generate_openai_image(prompt, output_path, "1024x1024")
