"""
JARVIS Core — NVIDIA NIM API Client
Handles all communication with free NVIDIA NIM models.
OpenAI-compatible endpoint: https://integrate.api.nvidia.com/v1
"""

import os
import json
import base64
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class NIMClient:
    """OpenAI-compatible client for NVIDIA NIM free API."""

    def __init__(self):
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key or api_key == "nvapi-DEIN_KEY_HIER":
            raise ValueError(
                "⚠️  NVIDIA API Key fehlt!\n"
                "1. Gehe zu https://build.nvidia.com/settings/api-keys\n"
                "2. Erstelle einen kostenlosen API Key\n"
                "3. Trage ihn in .env ein: NVIDIA_API_KEY=nvapi-xxx"
            )

        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
        )
        self.model = os.getenv("JARVIS_MODEL", "moonshotai/kimi-k2.5")
        self.vision_model = os.getenv("JARVIS_VISION_MODEL", "qwen/qwen2.5-vl-72b-instruct")

    def ask(self, prompt: str, system: str = None, temperature: float = 0.3, max_tokens: int = 2048) -> str:
        """Simple text query to the LLM."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[NIM Error] {e}"

    def ask_with_context(self, messages: list, temperature: float = 0.3, max_tokens: int = 2048) -> str:
        """Multi-turn conversation with full message history."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[NIM Error] {e}"

    def analyze_image(self, image_path: str, prompt: str = "Analyze this trading chart.") -> str:
        """Send an image (chart screenshot) to the vision model."""
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        ext = image_path.split(".")[-1].lower()
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")

        try:
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                        {"type": "text", "text": prompt},
                    ],
                }],
                max_tokens=2048,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[Vision Error] {e}"

    def structured_ask(self, prompt: str, system: str = None) -> dict:
        """Ask LLM and try to parse JSON from response."""
        if system:
            system += "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no backticks, no explanation."
        else:
            system = "Respond ONLY with valid JSON. No markdown, no backticks, no explanation."

        raw = self.ask(prompt, system=system, temperature=0.1)

        # Try to extract JSON from response
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw": raw}
