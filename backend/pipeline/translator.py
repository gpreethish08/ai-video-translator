"""
Neural Machine Translation Module
Translates transcribed text segments into target languages accurately
while preserving context, punctuation, and timing constraints.
"""

import logging
import urllib.parse
import urllib.request
import json
from typing import List, Dict, Any

logger = logging.getLogger("ai_video_translator.translator")


class TranslationEngine:
    def __init__(self):
        self._deep_translator_available = None

    def translate_text(self, text: str, source_lang: str = "auto", target_lang: str = "en") -> str:
        """Translates a single string from source language to target language."""
        if not text or not text.strip():
            return ""

        if source_lang == target_lang and source_lang != "auto":
            return text

        # 1. Try deep-translator (Google, Libre, MyMemory)
        try:
            from deep_translator import GoogleTranslator
            translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
            if translated:
                return translated
        except Exception as e:
            logger.debug("deep_translator failed: %s, falling back to public endpoint", e)

        # 2. Fast public translation fallback via Google Translate API
        try:
            encoded_text = urllib.parse.quote(text)
            src = "auto" if source_lang == "auto" else source_lang
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src}&tl={target_lang}&dt=t&q={encoded_text}"
            
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                translated_parts = [part[0] for part in result[0] if part[0]]
                return "".join(translated_parts)
        except Exception as e:
            logger.warning("Public Google API translation error: %s. Returning original.", e)
            return text

    def translate_segments(self, segments: List[Dict[str, Any]], source_lang: str, target_lang: str) -> List[Dict[str, Any]]:
        """
        Translates all transcription segments in batch, preserving timing and metadata.
        """
        translated_segments = []
        for seg in segments:
            orig = seg.get("text", "")
            trans = self.translate_text(orig, source_lang=source_lang, target_lang=target_lang)
            new_seg = dict(seg)
            new_seg["original_text"] = orig
            new_seg["translated_text"] = trans
            translated_segments.append(new_seg)

        return translated_segments
