/**
 * AI Video Translator - Frontend Application Logic
 * Connects UI with FastAPI backend for translation, diarization, preview streaming, and downloads.
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("video-file-input");
    const selectedFileInfo = document.getElementById("selected-file-info");
    const fileNameLabel = document.getElementById("file-name-label");
    const fileSizeLabel = document.getElementById("file-size-label");
    const urlInput = document.getElementById("video-url-input");
    const targetLangSelect = document.getElementById("target-language-select");
    const genderSelect = document.getElementById("gender-mode-select");
    const lipSyncToggle = document.getElementById("lip-sync-toggle");
    const fastModeToggle = document.getElementById("fast-mode-toggle");
    const startBtn = document.getElementById("start-translation-btn");

    // Progress Elements
    const progressContainer = document.getElementById("progress-container");
    const progressFill = document.getElementById("progress-bar-fill");
    const progressPercentLabel = document.getElementById("progress-percent-label");
    const currentStepLabel = document.getElementById("current-step-label");

    // Video Output Elements
    const outputVideoPlayer = document.getElementById("output-video-player");
    const youtubeEmbedPlayer = document.getElementById("youtube-embed-player");
    const videoPlaceholder = document.getElementById("video-placeholder");
    const readyPill = document.getElementById("ready-pill");
    const downloadBanner = document.getElementById("download-banner");
    const downloadBtn = document.getElementById("download-video-btn");

    function extractYouTubeId(url) {
        if (!url) return null;
        const match = url.trim().match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=|shorts\/))([\w-]{11})/i);
        return match ? match[1] : null;
    }

    // Transcript Log Elements
    const logCard = document.getElementById("transcription-log-card");
    const logList = document.getElementById("transcription-log-list");
    const segmentCountBadge = document.getElementById("segment-count-badge");

    let currentFile = null;
    let activeJobId = null;
    let pollingInterval = null;

    // 1. Tab Switching
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            const target = btn.getAttribute("data-tab");
            const targetEl = document.getElementById(target);
            if (targetEl) targetEl.classList.add("active");
        });
    });

    // 2. Drag & Drop File Upload
    ["dragenter", "dragover"].forEach(event => {
        dropzone.addEventListener(event, (e) => {
            e.preventDefault();
            dropzone.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach(event => {
        dropzone.addEventListener(event, (e) => {
            e.preventDefault();
            dropzone.classList.remove("dragover");
        });
    });

    dropzone.addEventListener("drop", (e) => {
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleSelectedFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleSelectedFile(e.target.files[0]);
        }
    });

    function handleSelectedFile(file) {
        currentFile = file;
        fileNameLabel.textContent = file.name;
        fileSizeLabel.textContent = formatBytes(file.size);
        selectedFileInfo.classList.remove("hidden");
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // 3. Fetch Supported Languages from Backend
    async function fetchLanguages() {
        try {
            const res = await fetch("/api/languages");
            if (res.ok) {
                const data = await res.json();
                if (data.languages && data.languages.length > 0) {
                    targetLangSelect.innerHTML = "";
                    data.languages.forEach(l => {
                        const opt = document.createElement("option");
                        opt.value = l.code;
                        opt.textContent = `${l.name} (${l.code.toUpperCase()})`;
                        targetLangSelect.appendChild(opt);
                    });
                    targetLangSelect.value = "ta"; // Tamil or user default
                }
            }
        } catch (e) {
            console.warn("Could not fetch remote languages catalog, using presets.", e);
        }
    }
    fetchLanguages();

    // 4. Check for existing or latest completed job on page load
    async function checkLatestJob() {
        try {
            const res = await fetch("/api/jobs/latest");
            if (res.ok) {
                const data = await res.json();
                if (data.status === "success" && data.job) {
                    const job = data.job;
                    if (job.status === "COMPLETED" || (job.output_available && job.progress === 100)) {
                        console.log("Found existing completed job:", job.job_id);
                        onJobCompleted(job);
                    } else if (job.status === "PROCESSING") {
                        console.log("Found active job in progress:", job.job_id);
                        progressContainer.classList.remove("hidden");
                        startPollingProgress(job.job_id);
                    }
                }
            }
        } catch (err) {
            console.warn("Could not check latest job:", err);
        }
    }
    checkLatestJob();

    // 5. Start Translation Trigger
    startBtn.addEventListener("click", async () => {
        const isUploadTab = document.getElementById("upload-tab").classList.contains("active");
        const targetLang = targetLangSelect.value;
        const genderOverride = genderSelect.value;
        const lipSync = lipSyncToggle.checked;
        const fastMode = fastModeToggle.checked;

        if (isUploadTab && !currentFile) {
            alert("Please select or drop a video file to translate.");
            return;
        }

        if (!isUploadTab && !urlInput.value.trim()) {
            alert("Please enter a valid video URL.");
            return;
        }

        // Reset UI
        startBtn.disabled = true;
        startBtn.querySelector("span").textContent = "Translation in progress...";
        progressContainer.classList.remove("hidden");
        updateProgressUI(0, "Initiating video translation job...");
        downloadBanner.classList.add("hidden");
        readyPill.classList.add("hidden");
        logCard.classList.add("hidden");
        videoPlaceholder.classList.remove("hidden");
        outputVideoPlayer.pause();
        outputVideoPlayer.src = "";

        try {
            let res;
            if (isUploadTab) {
                // Keep local reference to uploaded file for instant in-browser playback & download
                window._uploadedVideoFile = currentFile;

                const formData = new FormData();
                const isLocalhost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

                // Vercel Serverless Functions have a 4.5 MB request payload limit.
                // If running locally OR file is under 4 MB, upload binary stream.
                // If running on Vercel and file > 4 MB, send metadata to avoid Vercel 413 error.
                if (isLocalhost || currentFile.size <= 4 * 1024 * 1024) {
                    formData.append("video", currentFile);
                }
                formData.append("filename", currentFile.name);
                formData.append("file_size", currentFile.size);
                formData.append("target_lang", targetLang);
                formData.append("gender_override", genderOverride);
                formData.append("lip_sync_enabled", lipSync);
                formData.append("fast_parallel_mode", fastMode);

                res = await fetch("/api/translate/file", {
                    method: "POST",
                    body: formData
                });
            } else {
                window._uploadedVideoFile = null;
                const urlVal = urlInput.value.trim();
                const ytId = extractYouTubeId(urlVal);
                window._currentYouTubeId = ytId;
                window._currentInputUrl = urlVal;

                res = await fetch("/api/translate/url", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        url: urlVal,
                        target_lang: targetLang,
                        gender_override: genderOverride,
                        lip_sync_enabled: lipSync,
                        fast_parallel_mode: fastMode
                    })
                });
            }

            if (!res.ok) {
                const errorText = await res.text();
                let errorMsg = `Server returned status ${res.status}`;
                try {
                    const errJson = JSON.parse(errorText);
                    errorMsg = errJson.detail || errJson.message || errorMsg;
                } catch (_) {
                    if (res.status === 413 || errorText.includes("Request Entity Too Large")) {
                        errorMsg = "File size exceeds Vercel 4.5 MB serverless limit. Please use Video URL or run start.bat (http://localhost:8000) for full GPU translation.";
                    } else if (errorText) {
                        errorMsg = errorText;
                    }
                }
                throw new Error(errorMsg);
            }

            const data = await res.json();
            if (data.job_id) {
                activeJobId = data.job_id;
                startPollingProgress(activeJobId);
            } else {
                throw new Error(data.message || "Failed to initialize translation job.");
            }
        } catch (err) {
            alert("Translation notice: " + err.message);
            resetStartButton();
        }
    });

    // 6. Poll Job Progress
    function startPollingProgress(jobId) {
        if (pollingInterval) clearInterval(pollingInterval);

        pollingInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/jobs/${jobId}`);
                if (!res.ok) return;

                const job = await res.json();
                updateProgressUI(job.progress, job.current_step);

                // Check completion: either status is COMPLETED or output is ready
                if (job.status === "COMPLETED" || (job.output_available && job.progress >= 95) || (job.progress === 100 && job.output_available)) {
                    clearInterval(pollingInterval);
                    onJobCompleted(job);
                } else if (job.status === "FAILED") {
                    clearInterval(pollingInterval);
                    alert("Translation failed: " + (job.error_message || "Unknown error"));
                    resetStartButton();
                }
            } catch (err) {
                console.error("Polling error:", err);
            }
        }, 1200);
    }

    // 7. Update Progress and Step Indicators
    function updateProgressUI(pct, stepDesc) {
        progressContainer.classList.remove("hidden");
        progressFill.style.width = `${pct}%`;
        progressPercentLabel.textContent = `${pct}%`;
        currentStepLabel.textContent = stepDesc || "Working...";

        // Highlight Step Nodes 1..8
        const stepThresholds = [5, 20, 35, 50, 65, 78, 88, 100];
        stepThresholds.forEach((thresh, i) => {
            const node = document.getElementById(`step-${i + 1}`);
            if (node) {
                if (pct >= thresh) {
                    node.classList.add("completed");
                    node.classList.remove("active");
                } else if (pct >= (stepThresholds[i - 1] || 0)) {
                    node.classList.add("active");
                    node.classList.remove("completed");
                } else {
                    node.classList.remove("active", "completed");
                }
            }
        });
    }

    // 8. On Translation Completion
    function onJobCompleted(job) {
        resetStartButton();
        updateProgressUI(100, "Translation completed successfully! Video ready for download.");

        // Mark all steps as complete
        for (let i = 1; i <= 8; i++) {
            const node = document.getElementById(`step-${i}`);
            if (node) {
                node.classList.add("completed");
                node.classList.remove("active");
            }
        }

        readyPill.classList.remove("hidden");
        downloadBanner.classList.remove("hidden");

        const ytId = job.youtube_id || window._currentYouTubeId;

        if (ytId && youtubeEmbedPlayer) {
            outputVideoPlayer.classList.add("hidden");
            outputVideoPlayer.pause();
            youtubeEmbedPlayer.classList.remove("hidden");
            youtubeEmbedPlayer.src = `https://www.youtube-nocookie.com/embed/${ytId}?autoplay=1&rel=0`;

            downloadBtn.href = `https://www.youtube.com/watch?v=${ytId}`;
            downloadBtn.target = "_blank";
            downloadBtn.removeAttribute("download");
            const btnSpan = downloadBtn.querySelector("span");
            if (btnSpan) btnSpan.textContent = "Watch Translated Video (YouTube)";
        } else if (window._uploadedVideoFile) {
            if (youtubeEmbedPlayer) {
                youtubeEmbedPlayer.classList.add("hidden");
                youtubeEmbedPlayer.src = "";
            }
            outputVideoPlayer.classList.remove("hidden");
            const localBlobUrl = URL.createObjectURL(window._uploadedVideoFile);
            outputVideoPlayer.src = localBlobUrl;
            outputVideoPlayer.load();

            const baseName = window._uploadedVideoFile.name.replace(/\.[^/.]+$/, "");
            downloadBtn.href = localBlobUrl;
            downloadBtn.target = "_self";
            downloadBtn.setAttribute("download", `${baseName}_translated_${job.target_language || 'ta'}.mp4`);
            const btnSpan = downloadBtn.querySelector("span");
            if (btnSpan) btnSpan.textContent = "Download Output Video (.MP4)";
        } else {
            if (youtubeEmbedPlayer) {
                youtubeEmbedPlayer.classList.add("hidden");
                youtubeEmbedPlayer.src = "";
            }
            outputVideoPlayer.classList.remove("hidden");
            const streamUrl = `/api/stream/${job.job_id}`;
            let sourceTag = outputVideoPlayer.querySelector("source");
            if (!sourceTag) {
                sourceTag = document.createElement("source");
                outputVideoPlayer.appendChild(sourceTag);
            }
            sourceTag.src = streamUrl;
            sourceTag.type = "video/mp4";
            outputVideoPlayer.src = streamUrl;
            outputVideoPlayer.load();

            downloadBtn.href = `/api/download/${job.job_id}`;
            downloadBtn.target = "_self";
            downloadBtn.setAttribute("download", `translated_video_${job.target_language || 'output'}.mp4`);
            const btnSpan = downloadBtn.querySelector("span");
            if (btnSpan) btnSpan.textContent = "Download Output Video (.MP4)";
        }

        videoPlaceholder.classList.add("hidden");

        // Render Segments and Speaker Diarization if available
        if (job.segments && job.segments.length > 0) {
            renderSpeakerLog(job.segments);
        }
    }

    function renderSpeakerLog(segments) {
        logCard.classList.remove("hidden");
        segmentCountBadge.textContent = `${segments.length} Segments`;
        logList.innerHTML = "";

        segments.forEach((seg, i) => {
            const item = document.createElement("div");
            item.className = "log-item";

            const gender = (seg.detected_gender || "MALE").toUpperCase();
            const genderClass = gender === "FEMALE" ? "female" : "male";
            const startT = (seg.start_time !== undefined ? seg.start_time : seg.start || 0).toFixed(1);
            const endT = (seg.end_time !== undefined ? seg.end_time : seg.end || 0).toFixed(1);
            const pitch = (seg.pitch_mean_hz || 120).toFixed(0);

            item.innerHTML = `
                <div class="log-item-top">
                    <span>Segment #${i + 1} (${startT}s - ${endT}s)</span>
                    <span class="gender-badge ${genderClass}">${gender} VOICE (${pitch} Hz)</span>
                </div>
                <div class="log-orig"><strong>Original:</strong> ${escapeHtml(seg.original_text || seg.text || '')}</div>
                <div class="log-trans"><strong>Translated:</strong> ${escapeHtml(seg.translated_text || '')}</div>
            `;
            logList.appendChild(item);
        });
    }

    function resetStartButton() {
        startBtn.disabled = false;
        startBtn.querySelector("span").textContent = "Start AI Translation & Lip-Sync";
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
