"""
Video Assembler and Final Renderer
Concatenates parallel chunk segments, applies final audio multiplexing,
and generates ready-to-stream / ready-to-download MP4 output files.
"""

import os
import subprocess
import logging
from typing import List

logger = logging.getLogger("ai_video_translator.assembler")


class VideoAssembler:
    def __init__(self, ffmpeg_bin: str = "ffmpeg"):
        self.ffmpeg = ffmpeg_bin

    def assemble_final_video(
        self,
        video_input: str,
        audio_input: str,
        output_file: str,
        subtitles_srt: str = None
    ) -> str:
        """Merges video and audio with optimal encoding settings for web streaming and download."""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        cmd = [
            self.ffmpeg,
            "-y",
            "-i", video_input,
            "-i", audio_input,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            output_file
        ]
        logger.info("Assembling final video to: %s", output_file)
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return output_file
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
            logger.warning("Default encode failed (%s). Retrying with copy codec...", err_msg)
            
            fallback_cmd = [
                self.ffmpeg,
                "-y",
                "-i", video_input,
                "-i", audio_input,
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                output_file
            ]
            subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return output_file

    def concatenate_chunks(self, chunk_files: List[str], final_output: str) -> str:
        """Concatenates multiple video chunks into a single seamless output file."""
        os.makedirs(os.path.dirname(final_output), exist_ok=True)
        concat_list_file = os.path.join(os.path.dirname(final_output), "concat_list.txt")

        with open(concat_list_file, "w", encoding="utf-8") as f:
            for chunk in chunk_files:
                safe_path = chunk.replace("\\", "/")
                f.write(f"file '{safe_path}'\n")

        cmd = [
            self.ffmpeg,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list_file,
            "-c", "copy",
            "-movflags", "+faststart",
            final_output
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        finally:
            if os.path.exists(concat_list_file):
                try:
                    os.remove(concat_list_file)
                except Exception:
                    pass

        return final_output
