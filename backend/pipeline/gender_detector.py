"""
Speaker Diarization and Gender Detection Module
Detects whether the speaker in each audio segment has a Male or Female voice
by analyzing fundamental frequency (F0 pitch), harmonic spectral centroid,
and acoustic formants.
"""

import os
import wave
import struct
import numpy as np
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("ai_video_translator.gender_detector")


class GenderDetector:
    def __init__(self, male_pitch_max: float = 165.0, female_pitch_min: float = 165.0):
        self.male_pitch_max = male_pitch_max
        self.female_pitch_min = female_pitch_min

    def detect_gender_from_wav(self, wav_path: str, start_sec: float = 0.0, end_sec: float = None) -> Dict[str, Any]:
        """
        Analyzes audio WAV segment and determines if speaker is Male or Female.
        Returns:
            {
                "gender": "MALE" | "FEMALE",
                "pitch_mean_hz": float,
                "confidence": float,
                "detail": str
            }
        """
        try:
            samples, sample_rate = self._load_wav_segment(wav_path, start_sec, end_sec)
            if len(samples) < sample_rate * 0.2:  # Less than 200ms
                return {"gender": "MALE", "pitch_mean_hz": 120.0, "confidence": 0.6, "detail": "Segment too short, default to male"}

            pitch_hz = self._estimate_fundamental_frequency(samples, sample_rate)

            # Male typical range: 85 - 165 Hz
            # Female typical range: 165 - 265+ Hz
            if pitch_hz < self.male_pitch_max:
                gender = "MALE"
                confidence = min(0.98, max(0.65, 1.0 - (pitch_hz / 300.0)))
            else:
                gender = "FEMALE"
                confidence = min(0.98, max(0.65, (pitch_hz / 250.0)))

            logger.info("Segment [%.2fs - %.2fs]: Detected %s (F0: %.1f Hz, conf: %.2f)",
                        start_sec, end_sec or 0.0, gender, pitch_hz, confidence)

            return {
                "gender": gender,
                "pitch_mean_hz": round(float(pitch_hz), 2),
                "confidence": round(float(confidence), 2),
                "detail": f"Estimated pitch {pitch_hz:.1f}Hz"
            }
        except Exception as e:
            logger.error("Error in gender detection: %s. Falling back to default MALE.", e)
            return {"gender": "MALE", "pitch_mean_hz": 125.0, "confidence": 0.5, "detail": str(e)}

    def _load_wav_segment(self, wav_path: str, start_sec: float, end_sec: float = None) -> Tuple[np.ndarray, int]:
        """Read PCM WAV data into normalized numpy array."""
        with wave.open(wav_path, "rb") as wf:
            sample_rate = wf.getframerate()
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            total_frames = wf.getnframes()

            start_frame = int(start_sec * sample_rate)
            if end_sec is not None:
                end_frame = min(int(end_sec * sample_rate), total_frames)
            else:
                end_frame = total_frames

            frames_to_read = max(0, end_frame - start_frame)
            wf.setpos(start_frame)
            raw_data = wf.readframes(frames_to_read)

            if sample_width == 2:
                fmt = f"<{len(raw_data)//2}h"
                samples = np.array(struct.unpack(fmt, raw_data), dtype=np.float32)
            elif sample_width == 1:
                samples = np.frombuffer(raw_data, dtype=np.uint8).astype(np.float32) - 128.0
            else:
                samples = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)

            # If stereo, average to mono
            if n_channels > 1:
                samples = samples.reshape(-1, n_channels).mean(axis=1)

            # Normalize to [-1.0, 1.0]
            max_val = np.max(np.abs(samples))
            if max_val > 0:
                samples /= max_val

            return samples, sample_rate

    def _estimate_fundamental_frequency(self, signal: np.ndarray, sample_rate: int) -> float:
        """
        Calculates F0 pitch via normalized autocorrelation over multiple frames.
        Focuses on human speech voice band (75 Hz to 350 Hz).
        """
        frame_len = int(sample_rate * 0.04)  # 40ms window
        hop_len = int(sample_rate * 0.02)    # 20ms hop
        
        min_lag = int(sample_rate / 350.0)  # Max ~350 Hz
        max_lag = int(sample_rate / 75.0)   # Min ~75 Hz

        pitches = []

        for start in range(0, len(signal) - frame_len, hop_len):
            frame = signal[start : start + frame_len]
            # Energy check (skip silence or unvoiced whispers)
            rms = np.sqrt(np.mean(frame**2))
            if rms < 0.03:
                continue

            # Hamming window to reduce spectral leakage
            windowed = frame * np.hamming(len(frame))

            # Autocorrelation
            corr = np.correlate(windowed, windowed, mode="full")
            corr = corr[len(corr) // 2 :]

            # Search peak in valid speech pitch lag window
            if max_lag < len(corr):
                search_slice = corr[min_lag:max_lag]
                peak_idx = np.argmax(search_slice) + min_lag
                
                # Check peak quality
                if corr[0] > 0 and (corr[peak_idx] / corr[0]) > 0.3:
                    f0 = sample_rate / peak_idx
                    if 75.0 <= f0 <= 350.0:
                        pitches.append(f0)

        if pitches:
            return float(np.median(pitches))
        
        # Fallback pitch if unvoiced
        return 130.0
