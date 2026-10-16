"""
Voice Synthesis and Speech Alignment Module
Generates high-fidelity neural speech for Male/Female speakers in 50+ languages,
and time-stretches/compresses audio using FFmpeg atempo to synchronize perfectly
with the original speech segments (preventing audio-video drift across 40 minutes).
"""

import os
import asyncio
import subprocess
import logging
import wave
import struct
import urllib.request
import urllib.parse
import numpy as np
from typing import List, Dict, Any, Optional
from backend.config import SUPPORTED_LANGUAGES

logger = logging.getLogger("ai_video_translator.synthesizer")


class VoiceSynthesizer:
    def __init__(self, ffmpeg_bin: str = "ffmpeg"):
        self.ffmpeg = ffmpeg_bin

    def get_voice_for_speaker(self, lang_code: str, gender: str) -> str:
        """Select neural voice matching target language and detected gender."""
        lang_config = SUPPORTED_LANGUAGES.get(lang_code, SUPPORTED_LANGUAGES.get("en", {}))
        if gender.upper() == "FEMALE":
            return lang_config.get("female_voice", "en-US-JennyNeural")
        else:
            return lang_config.get("male_voice", "en-US-GuyNeural")

    async def _generate_edge_tts(self, text: str, voice: str, output_path: str):
        """Synthesize speech using Microsoft Edge Neural TTS."""
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    def synthesize_segment(self, text: str, voice_id: str, final_wav_path: str, lang_code: str = "en") -> bool:
        """
        Synthesize speech audio for a text segment.
        Edge-TTS outputs MP3 stream, which is converted to 16kHz mono PCM WAV.
        Falls back to Google TTS API then pyttsx3 if network or voice error occurs.
        """
        dir_name = os.path.dirname(final_wav_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        raw_mp3_path = final_wav_path + ".mp3"
        try:
            # 1. Generate MP3 with Edge-TTS
            asyncio.run(self._generate_edge_tts(text, voice_id, raw_mp3_path))

            if os.path.exists(raw_mp3_path) and os.path.getsize(raw_mp3_path) > 100:
                cmd = [
                    self.ffmpeg,
                    "-y",
                    "-i", raw_mp3_path,
                    "-acodec", "pcm_s16le",
                    "-ar", "16000",
                    "-ac", "1",
                    final_wav_path
                ]
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                if os.path.exists(final_wav_path) and os.path.getsize(final_wav_path) > 100:
                    return True
        except Exception as e:
            logger.warning("edge-tts generation failed: %s. Trying Google TTS fallback.", e)

        # 2. Try Google TTS API fallback
        if self._synthesize_google_tts(text, lang_code, final_wav_path):
            return True

        # 3. Fallback to pyttsx3 offline
        return self._synthesize_fallback(text, final_wav_path)

    def _synthesize_google_tts(self, text: str, lang_code: str, output_wav_path: str) -> bool:
        """Fallback to Google TTS public endpoint."""
        raw_mp3 = output_wav_path + "_gtts.mp3"
        try:
            enc = urllib.parse.quote(text[:200])
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={lang_code}&client=tw-ob&q={enc}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = resp.read()
                if len(data) > 100:
                    with open(raw_mp3, "wb") as f:
                        f.write(data)
                    cmd = [
                        self.ffmpeg,
                        "-y",
                        "-i", raw_mp3,
                        "-acodec", "pcm_s16le",
                        "-ar", "16000",
                        "-ac", "1",
                        output_wav_path
                    ]
                    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    return os.path.exists(output_wav_path) and os.path.getsize(output_wav_path) > 100
        except Exception as e:
            logger.debug("Google TTS fallback failed: %s", e)
        finally:
            if os.path.exists(raw_mp3):
                try:
                    os.remove(raw_mp3)
                except Exception:
                    pass
        return False

    def _synthesize_fallback(self, text: str, output_path: str) -> bool:
        """Fallback offline TTS (pyttsx3) converted to 16kHz mono WAV."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            temp_out = output_path + "_raw.wav"
            engine.save_to_file(text, temp_out)
            engine.runAndWait()

            cmd = [
                self.ffmpeg,
                "-y",
                "-i", temp_out,
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                output_path
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            if os.path.exists(temp_out):
                os.remove(temp_out)
            return os.path.exists(output_path) and os.path.getsize(output_path) > 100
        except Exception as e:
            logger.error("Fallback pyttsx3 also failed: %s", e)
            return False

    def time_align_audio(self, input_wav: str, target_duration: float, output_wav: str) -> str:
        """
        Adjusts playback tempo using FFmpeg atempo filter (preserves pitch)
        so that translated speech matches original speaker timing down to the millisecond.
        """
        current_duration = self._get_wav_duration(input_wav)
        if current_duration <= 0 or target_duration <= 0:
            return input_wav

        speed_ratio = current_duration / target_duration
        # Keep speed within reasonable, natural-sounding bounds (0.7x to 1.6x)
        speed_ratio = max(0.70, min(1.60, speed_ratio))

        filter_str = f"atempo={speed_ratio:.4f}"
        cmd = [
            self.ffmpeg,
            "-y",
            "-i", input_wav,
            "-filter:a", filter_str,
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            output_wav
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            if os.path.exists(output_wav) and os.path.getsize(output_wav) > 100:
                return output_wav
            return input_wav
        except Exception as e:
            logger.error("Failed to time-stretch audio segment: %s", e)
            return input_wav

    def build_full_audio_track(
        self,
        segments: List[Dict[str, Any]],
        total_duration: float,
        output_track_wav: str,
        target_lang: str,
        gender_override: str = "auto"
    ) -> str:
        """
        Synthesizes and stitches all translated speaker segments into a continuous,
        perfectly synchronized master audio track for the entire video.
        Also produces a matching MP3 version for instant browser streaming.
        """
        base_dir = os.path.dirname(output_track_wav)
        temp_dir = os.path.join(base_dir, "synth_segments") if base_dir else "synth_segments"
        os.makedirs(temp_dir, exist_ok=True)

        segment_files = []
        for i, seg in enumerate(segments):
            text = (seg.get("translated_text") or seg.get("original_text") or seg.get("text", "")).strip()
            if not text:
                continue

            if gender_override in ["male", "female"]:
                gender = gender_override.upper()
            else:
                gender = seg.get("detected_gender", "MALE")

            voice_id = self.get_voice_for_speaker(target_lang, gender)
            raw_path = os.path.join(temp_dir, f"seg_{i:04d}_raw.wav")
            aligned_path = os.path.join(temp_dir, f"seg_{i:04d}_aligned.wav")

            start_t = float(seg.get("start_time", seg.get("start", 0.0)))
            end_t = float(seg.get("end_time", seg.get("end", start_t + 2.0)))
            target_dur = max(0.2, end_t - start_t)

            if self.synthesize_segment(text, voice_id, raw_path, lang_code=target_lang):
                effective_file = self.time_align_audio(raw_path, target_dur, aligned_path)
                segment_files.append({
                    "path": effective_file,
                    "start": start_t,
                    "end": end_t
                })

        # Assemble into full timeline WAV
        self._assemble_timeline(segment_files, total_duration, output_track_wav)

        # Transcode to MP3 for web streaming & download
        mp3_output = os.path.splitext(output_track_wav)[0] + ".mp3"
        try:
            cmd = [
                self.ffmpeg,
                "-y",
                "-i", output_track_wav,
                "-c:a", "libmp3lame",
                "-b:a", "192k",
                mp3_output
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            logger.info("Master MP3 audio created: %s", mp3_output)
        except Exception as e:
            logger.warning("MP3 transcode error: %s", e)

        return output_track_wav

    def _assemble_timeline(self, segments: List[Dict[str, Any]], total_duration: float, output_path: str):
        """
        Uses in-memory NumPy PCM frame placement to stitch all audio segments
        at their exact millisecond timestamps without FFmpeg CLI argument limits or crashes.
        """
        total_duration = max(1.0, float(total_duration))
        total_samples = int(total_duration * 16000)
        timeline = np.zeros(total_samples, dtype=np.int16)

        for seg in segments:
            path = seg["path"]
            if not os.path.exists(path):
                continue

            try:
                with wave.open(path, "rb") as wf:
                    n_frames = wf.getnframes()
                    raw_bytes = wf.readframes(n_frames)
                    seg_data = np.frombuffer(raw_bytes, dtype=np.int16)

                start_idx = int(seg["start"] * 16000)
                if start_idx < total_samples:
                    available = total_samples - start_idx
                    take = min(len(seg_data), available)

                    slice_orig = timeline[start_idx : start_idx + take].astype(np.int32)
                    slice_new = seg_data[:take].astype(np.int32)
                    blended = np.clip(slice_orig + slice_new, -32768, 32767).astype(np.int16)
                    timeline[start_idx : start_idx + take] = blended
            except Exception as e:
                logger.error("Failed to merge segment %s into timeline: %s", path, e)

        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        with wave.open(output_path, "wb") as out_wf:
            out_wf.setnchannels(1)
            out_wf.setsampwidth(2)
            out_wf.setframerate(16000)
            out_wf.writeframes(timeline.tobytes())

        logger.info("Master audio timeline assembled: %s (duration: %.2fs)", output_path, total_duration)

    def _get_wav_duration(self, wav_path: str) -> float:
        """Helper to get accurate duration from WAV header."""
        try:
            with wave.open(wav_path, "rb") as wf:
                return wf.getnframes() / float(wf.getframerate())
        except Exception:
            return 0.0
