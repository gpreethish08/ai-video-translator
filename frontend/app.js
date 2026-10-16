/**
 * AI Video Translator - Frontend Application Logic
 * Connects UI with FastAPI backend for translation, diarization, and downloads.
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
    const videoPlaceholder = document.getElementById("video-placeholder");
    const readyPill = document.getElementById("ready-pill");
    const downloadBanner = document.getElementById("download-banner");
    const downloadBtn = document.getElementById("download-video-btn");

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
            document.getElementById(target).classList.add("active");
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
                    targetLangSelect.value = "es"; // Default to Spanish
                }
            }
        } catch (e) {
            console.warn("Could not fetch remote languages catalog, using presets.", e);
        }
    }
    fetchLanguages();

    // 4. Start Translation Trigger
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
                const formData = new FormData();
                formData.append("video", currentFile);
                formData.append("target_lang", targetLang);
                formData.append("gender_override", genderOverride);
                formData.append("lip_sync_enabled", lipSync);
                formData.append("fast_parallel_mode", fastMode);

                res = await fetch("/api/translate/file", {
                    method: "POST",
                    body: formData
                });
            } else {
                res = await fetch("/api/translate/url", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        url: urlInput.value.trim(),
                        target_lang: targetLang,
                        gender_override: genderOverride,
                        lip_sync_enabled: lipSync,
                        fast_parallel_mode: fastMode
                    })
                });
            }

            const data = await res.json();
            if (res.ok && data.job_id) {
                activeJobId = data.job_id;
                startPollingProgress(activeJobId);
            } else {
                throw new Error(data.detail || "Failed to initialize translation job.");
            }
        } catch (err) {
            alert("Error starting translation: " + err.message);
            resetStartButton();
        }
    });

    // 5. Poll Job Progress
    function startPollingProgress(jobId) {
        if (pollingInterval) clearInterval(pollingInterval);

        pollingInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/jobs/${jobId}`);
                if (!res.ok) return;

                const job = await res.json();
                updateProgressUI(job.progress, job.current_step);

                if (job.status === "COMPLETED") {
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
        }, 1500);
    }

    // 6. Update Progress and Step Indicators
    function updateProgressUI(pct, stepDesc) {
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

    // 7. On Translation Completion
    function onJobCompleted(job) {
        resetStartButton();
        readyPill.classList.remove("hidden");
        downloadBanner.classList.remove("hidden");

        // Set video source for preview
        const streamUrl = `/api/stream/${job.job_id}`;
        outputVideoPlayer.src = streamUrl;
        outputVideoPlayer.load();
        videoPlaceholder.classList.add("hidden");

        // Set download link
        downloadBtn.href = `/api/download/${job.job_id}`;
        downloadBtn.setAttribute("download", `translated_video_${job.target_language}.mp4`);

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

            item.innerHTML = `
                <div class="log-item-top">
                    <span>Segment #${i + 1} (${seg.start_time.toFixed(1)}s - ${seg.end_time.toFixed(1)}s)</span>
                    <span class="gender-badge ${genderClass}">${gender} VOICE (${seg.pitch_mean_hz.toFixed(0)} Hz)</span>
                </div>
                <div class="log-orig"><strong>Original:</strong> ${escapeHtml(seg.original_text)}</div>
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
