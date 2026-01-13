"""
Google Gemini Integration for Visual Report Generation.

Uses Gemini for:
- Image generation (charts, infographics, icons)
- Visual asset creation with emojis/icons
- Document formatting and styling
- Multi-modal report enhancement

Writing/analysis stays with Anthropic Claude.
"""

import os
import base64
import asyncio
import httpx
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class GeminiConfig:
    """Configuration for Gemini API."""
    api_key: str
    model: str = "gemini-2.0-flash"
    pro_model: str = "gemini-1.5-pro"
    imagen_model: str = "imagen-3.0-generate-002"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    timeout: int = 60


def get_gemini_config() -> Optional[GeminiConfig]:
    """Get Gemini configuration from environment."""
    api_key = os.environ.get("GOOGLE_GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("No Gemini API key found (GOOGLE_GEMINI_API_KEY or GOOGLE_API_KEY)")
        return None
    return GeminiConfig(api_key=api_key)


class GeminiClient:
    """Client for Google Gemini API interactions."""
    
    def __init__(self, config: Optional[GeminiConfig] = None):
        self.config = config or get_gemini_config()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        if self.config:
            self._client = httpx.AsyncClient(timeout=self.config.timeout)
        return self
    
    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()
    
    @property
    def available(self) -> bool:
        return self.config is not None

    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Optional[str]:
        """Generate text using Gemini Flash/Pro."""
        if not self.available or not self._client:
            return None
        
        model = model or self.config.model
        url = f"{self.config.base_url}/models/{model}:generateContent"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        
        try:
            response = await self._client.post(
                url,
                params={"key": self.config.api_key},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (httpx.HTTPError, KeyError, IndexError) as e:
            logger.error(f"Gemini text generation failed: {e}")
            return None

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
    ) -> Optional[bytes]:
        """Generate image using Imagen 3."""
        if not self.available or not self._client:
            return None
        
        url = f"{self.config.base_url}/models/{self.config.imagen_model}:predict"
        
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": aspect_ratio,
            },
        }
        
        try:
            response = await self._client.post(
                url,
                params={"key": self.config.api_key},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            image_b64 = data["predictions"][0]["bytesBase64Encoded"]
            return base64.b64decode(image_b64)
        except (httpx.HTTPError, KeyError, IndexError) as e:
            logger.error(f"Gemini image generation failed: {e}")
            return None

    async def format_with_emojis(self, text: str, style: str = "professional") -> str:
        """Add appropriate emojis and formatting to text."""
        if not self.available:
            return text
        
        prompt = f"""Add appropriate emojis and visual formatting to this text.
Style: {style}
Keep it professional but visually engaging.
Use emojis sparingly - only where they add value.

Text:
{text}

Return only the formatted text, no explanations."""
        
        result = await self.generate_text(prompt, temperature=0.3)
        return result or text


async def generate_report_visuals(
    audit_data: Dict[str, Any],
    output_dir: str,
) -> Dict[str, str]:
    """
    Generate visual assets for report using Gemini.
    
    Returns dict mapping asset names to file paths.
    """
    assets = {}
    
    async with GeminiClient() as client:
        if not client.available:
            logger.info("Gemini not available, skipping visual generation")
            return assets
        
        # Generate score visualization prompt
        overall_score = audit_data.get("overall_score", 0)
        grade = audit_data.get("overall_grade", "N/A")
        
        # Generate infographic for overall score
        score_prompt = f"""Create a clean, professional infographic showing:
- SEO Health Score: {overall_score}/100
- Grade: {grade}
- Use blue and green colors
- Modern, minimal design
- Include a circular progress indicator"""
        
        score_image = await client.generate_image(score_prompt, "16:9")
        if score_image:
            score_path = os.path.join(output_dir, "score_infographic.png")
            with open(score_path, "wb") as f:
                f.write(score_image)
            assets["score_infographic"] = score_path
    
    return assets


async def enhance_executive_summary(
    summary: str,
    company_name: str,
) -> str:
    """Enhance executive summary with visual formatting."""
    async with GeminiClient() as client:
        if not client.available:
            return summary
        
        prompt = f"""Enhance this executive summary for {company_name} with:
- Strategic use of emojis (checkmarks, arrows, stars)
- Clear section headers
- Bullet points for key findings
- Professional but engaging tone

Summary:
{summary}

Return the enhanced summary only."""
        
        result = await client.generate_text(prompt, temperature=0.4)
        return result or summary


# Sync wrappers
def generate_report_visuals_sync(
    audit_data: Dict[str, Any],
    output_dir: str,
) -> Dict[str, str]:
    """Sync wrapper for generate_report_visuals."""
    return asyncio.run(generate_report_visuals(audit_data, output_dir))


def enhance_executive_summary_sync(summary: str, company_name: str) -> str:
    """Sync wrapper for enhance_executive_summary."""
    return asyncio.run(enhance_executive_summary(summary, company_name))


__all__ = [
    "GeminiConfig",
    "GeminiClient",
    "generate_report_visuals",
    "generate_report_visuals_sync",
    "enhance_executive_summary",
    "enhance_executive_summary_sync",
]
