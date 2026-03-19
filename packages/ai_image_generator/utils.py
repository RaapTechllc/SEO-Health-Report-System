"""Shared utilities for AI image generation."""

import os

GEMINI_TEXT_MODEL = os.environ.get('GOOGLE_MODEL', os.environ.get('GEMINI_MODEL', 'gemini-3.0-pro'))
GEMINI_IMAGE_MODEL = os.environ.get('GOOGLE_IMAGE_MODEL', os.environ.get('GEMINI_IMAGE_MODEL', 'imagen-4.0-fast-generate-001'))
OPENAI_IMAGE_MODEL = os.environ.get('OPENAI_IMAGE_MODEL', 'gpt-image-1-mini')
