"""
Audio and Video Extraction Pipeline
Handles URL downloads, FFmpeg audio extraction, video metadata analysis,
and parallel segment slicing for up to 40-minute videos.
"""

import os
import sys
import json
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List

logger = logging.getLogger("ai_video_translator.extractor")


class AudioVideoExtractor:
    def __init__(self, ffmpeg_bin: str = "ffmpeg", ffprobe_bin: str = "ffprobe"):
        self.ffmpeg = ffmpeg_bin
        self.ffprobe = ffprobe_bin

    def _get_ytdlp_cmd(self) -> List[str]:
        """Finds the most capable yt-dlp executable installed on the system."""
        candidates = [
            r"C:\Users\DELL\AppData\Local\Programs\Python\Python311\Scripts\yt-dlp.exe",
            shutil.which("yt-dlp"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python311\Scripts\yt-dlp.exe"),
        ]
        for c in candidates:
            if c and os.path.exists(c):
                return [c]
        return [sys.executable, "-m", "yt_dlp"]

    def get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Extract duration, resolution, frame rate, and audio stream details."""
        cmd = [
            self.ffprobe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            stdout_str = result.stdout.decode('utf-8', errors='ignore')
            info = json.loads(stdout_str)

            format_dict = info.get("format", {})
            duration = float(format_dict.get("duration", 0.0))
            video_streams = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
            audio_streams = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]

            if duration <= 0.0 and video_streams:
                duration = float(video_streams[0].get("duration", 0.0))
            if duration <= 0.0 and audio_streams:
                duration = float(audio_streams[0].get("duration", 0.0))

            width = int(video_streams[0].get("width", 1280)) if video_streams else 1280
            height = int(video_streams[0].get("height", 720)) if video_streams else 720
            fps_eval = video_streams[0].get("r_frame_rate", "30/1") if video_streams else "30/1"

            try:
                num, den = map(float, fps_eval.split('/'))
                fps = num / den if den != 0 else 30.0
            except Exception:
                fps = 30.0

            return {
                "duration": duration,
                "width": width,
                "height": height,
                "fps": fps,
                "has_audio": len(audio_streams) > 0,
                "has_video": len(video_streams) > 0,
                "size_bytes": os.path.getsize(video_path) if os.path.exists(video_path) else 0
            }
        except Exception as e:
            logger.error("Failed to extract video metadata: %s", e)
            return {"duration": 15.0, "width": 1280, "height": 720, "fps": 30.0, "has_audio": True, "has_video": True, "size_bytes": 0}

    def extract_audio(self, video_path: str, output_wav_path: str, sample_rate: int = 16000) -> bool:
        """Extract high-fidelity 16kHz mono WAV audio track for transcription."""
        os.makedirs(os.path.dirname(output_wav_path), exist_ok=True)
        cmd = [
            self.ffmpeg,
            "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
            "-ac", "1",
            output_wav_path
        ]
        try:
            logger.info("Extracting audio from %s to %s", video_path, output_wav_path)
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return os.path.exists(output_wav_path) and os.path.getsize(output_wav_path) > 0
        except subprocess.CalledProcessError as e:
            logger.error("FFmpeg audio extraction error: %s", e.stderr.decode('utf-8', errors='ignore'))
            return False

    def download_url_video(self, url: str, output_folder: str, job_id: str) -> str:
        """Download video/audio from YouTube or any direct video link using yt-dlp or ffmpeg."""
        os.makedirs(output_folder, exist_ok=True)
        output_template = os.path.join(output_folder, f"{job_id}_raw.%(ext)s")
        ytdlp_bin = self._get_ytdlp_cmd()

        cmd = ytdlp_bin + [
            "-f", "best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "--output", output_template,
            "--no-playlist",
            "--no-warnings",
            "--max-filesize", "1500M",
            url
        ]

        try:
            logger.info("Executing yt-dlp download for URL: %s", url)
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

            # Find the downloaded file
            final_mp4 = os.path.join(output_folder, f"{job_id}_input.mp4")
            for ext in ["mp4", "mkv", "webm", "m4a", "mp3"]:
                candidate = os.path.join(output_folder, f"{job_id}_raw.{ext}")
                if os.path.exists(candidate):
                    if ext == "mp4":
                        shutil.copyfile(candidate, final_mp4)
                        return final_mp4
                    else:
                        self.normalize_to_mp4(candidate, final_mp4)
                        return final_mp4

            raise FileNotFoundError("Downloaded file was not found on disk")
        except Exception as e:
            logger.warning("yt-dlp failed (%s). Attempting direct FFmpeg stream download...", e)
            return self._download_direct_stream(url, os.path.join(output_folder, f"{job_id}_input.mp4"))

    def _download_direct_stream(self, url: str, output_path: str) -> str:
        """Direct stream download using ffmpeg."""
        cmd = [
            self.ffmpeg,
            "-y",
            "-i", url,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            output_path
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return output_path
        except Exception as e:
            logger.error("Direct stream download failed: %s", e)
            raise RuntimeError(f"Could not download video from provided URL: {url}")

    def normalize_to_mp4(self, input_path: str, output_path: str):
        """Ensure standard H.264/AAC MP4 format for consistent processing."""
        cmd = [
            self.ffmpeg,
            "-y",
            "-i", input_path,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except subprocess.CalledProcessError:
            # If input is audio only, create a video with black frame
            cmd_audio = [
                self.ffmpeg,
                "-y",
                "-f", "lavfi", "-i", "color=c=black:s=1280x720:r=25",
                "-i", input_path,
                "-c:v", "libx264",
                "-tune", "stillimage",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                output_path
            ]
            subprocess.run(cmd_audio, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    def slice_into_chunks(self, video_path: str, chunk_duration_sec: int, temp_dir: str) -> List[Tuple[str, float, float]]:
        """Slice long video (up to 40 mins) into parallel chunks."""
        meta = self.get_video_metadata(video_path)
        total_duration = meta["duration"]
        chunks = []
        start = 0.0
        idx = 0

        while start < total_duration:
            end = min(start + chunk_duration_sec, total_duration)
            chunk_file = os.path.join(temp_dir, f"chunk_{idx:03d}.mp4")
            duration = end - start

            cmd = [
                self.ffmpeg,
                "-y",
                "-ss", str(start),
                "-i", video_path,
                "-t", str(duration),
                "-c", "copy",
                chunk_file
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            chunks.append((chunk_file, start, end))
            start = end
            idx += 1

        return chunks
