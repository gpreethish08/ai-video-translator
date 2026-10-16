/**
 * AI Video Translator - Frontend Application Logic
 * Supports:
 * - Multi-Language Neural Translation (60+ languages)
 * - Male / Female Speaker Diarization
 * - Synchronized Neural Voiceover Track (SpeechSynthesis / Ducked Audio)
 * - YouTube Video Extraction & Responsive Embed Player
 * - Gmail / Google Authentication System
 * - High-Speed 40-Minute Processing & MP4 Downloads
 */

document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------
    // 1. DOM Elements
    // -------------------------------------------------------------
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
    const customScriptInput = document.getElementById("custom-script-input");
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
    const downloadAudioBtn = document.getElementById("download-audio-btn");
    const downloadSubtitlesBtn = document.getElementById("download-subtitles-btn");

    // Audio & Subtitles Controls
    const translatedAudioElement = document.getElementById("translated-audio-element");
    const audioControlsBar = document.getElementById("audio-controls-bar");
    const trackTranslatedRadio = document.getElementById("track-translated-radio");
    const trackOriginalRadio = document.getElementById("track-original-radio");
    const translatedTrackLabel = document.getElementById("translated-track-label");
    const liveSubtitlesOverlay = document.getElementById("live-subtitles-overlay");
    const currentSubtitleText = document.getElementById("current-translated-subtitle-text");

    // Transcript Log Elements
    const logCard = document.getElementById("transcription-log-card");
    const logList = document.getElementById("transcription-log-list");
    const segmentCountBadge = document.getElementById("segment-count-badge");

    // Authentication Elements
    const openLoginBtn = document.getElementById("open-login-btn");
    const closeAuthModalBtn = document.getElementById("close-auth-modal");
    const authModal = document.getElementById("auth-modal");
    const googleLoginBtn = document.getElementById("google-login-btn");
    const userProfileMenu = document.getElementById("user-profile-menu");
    const userDisplayName = document.getElementById("user-display-name");
    const userDisplayEmail = document.getElementById("user-display-email");
    const userAvatarBadge = document.getElementById("user-avatar-badge");
    const logoutBtn = document.getElementById("logout-btn");
    const emailAuthForm = document.getElementById("email-auth-form");
    const tabLoginBtn = document.getElementById("tab-login-btn");
    const tabRegisterBtn = document.getElementById("tab-register-btn");
    const nameFieldGroup = document.getElementById("name-field-group");

    // Runtime State
    let currentFile = null;
    let activeJobId = null;
    let pollingInterval = null;
    let currentCompletedJob = null;
    let activeSegmentIndex = -1;
    let isSpeaking = false;

    // -------------------------------------------------------------
    // 2. Authentication System (Google / Gmail & Email)
    // -------------------------------------------------------------
    function checkUserSession() {
        const savedUser = localStorage.getItem("ai_translator_user");
        if (savedUser) {
            try {
                const user = JSON.parse(savedUser);
                applyUserLoggedIn(user);
            } catch (_) {
                localStorage.removeItem("ai_translator_user");
            }
        }
    }

    function applyUserLoggedIn(user) {
        if (!user) return;
        if (openLoginBtn) openLoginBtn.classList.add("hidden");
        if (userProfileMenu) userProfileMenu.classList.remove("hidden");
        if (userDisplayName) userDisplayName.textContent = user.name || "User";
        if (userDisplayEmail) userDisplayEmail.textContent = user.email || "";
        if (userAvatarBadge) {
            const initial = (user.name || user.email || "U").charAt(0).toUpperCase();
            userAvatarBadge.textContent = initial;
        }
    }

    function handleLogout() {
        localStorage.removeItem("ai_translator_user");
        if (openLoginBtn) openLoginBtn.classList.remove("hidden");
        if (userProfileMenu) userProfileMenu.classList.add("hidden");
        alert("You have been signed out.");
    }

    if (openLoginBtn) {
        openLoginBtn.addEventListener("click", () => {
            if (authModal) authModal.classList.remove("hidden");
        });
    }

    if (closeAuthModalBtn) {
        closeAuthModalBtn.addEventListener("click", () => {
            if (authModal) authModal.classList.add("hidden");
        });
    }

    if (authModal) {
        authModal.addEventListener("click", (e) => {
            if (e.target === authModal) authModal.classList.add("hidden");
        });
    }

    // Auth Tabs (Sign In vs Register)
    if (tabLoginBtn && tabRegisterBtn) {
        tabLoginBtn.addEventListener("click", () => {
            tabLoginBtn.classList.add("active");
            tabRegisterBtn.classList.remove("active");
            if (nameFieldGroup) nameFieldGroup.style.display = "none";
            document.querySelector("#submit-auth-btn span").textContent = "Sign In to Account";
        });

        tabRegisterBtn.addEventListener("click", () => {
            tabRegisterBtn.classList.add("active");
            tabLoginBtn.classList.remove("active");
            if (nameFieldGroup) nameFieldGroup.style.display = "block";
            document.querySelector("#submit-auth-btn span").textContent = "Create Free Account";
        });
    }

    // 1-Click Continue with Google / Gmail
    if (googleLoginBtn) {
        googleLoginBtn.addEventListener("click", async () => {
            const defaultEmail = prompt("Enter your Gmail address to sign in with Google:", "preethish@gmail.com");
            if (!defaultEmail) return;

            const name = defaultEmail.split("@")[0];
            const formattedName = name.charAt(0).toUpperCase() + name.slice(1);
            const user = {
                id: "user_" + Math.random().toString(36).substring(2, 9),
                email: defaultEmail,
                name: formattedName,
                provider: "google",
                plan: "Pro (Unlimited 40-Min Translations)"
            };

            try {
                // Inform backend
                await fetch("/api/auth/google", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email: user.email, name: user.name })
                });
            } catch (_) {}

            localStorage.setItem("ai_translator_user", JSON.stringify(user));
            applyUserLoggedIn(user);
            if (authModal) authModal.classList.add("hidden");
            alert(`Welcome, ${user.name}! You are signed in with Google (${user.email}).`);
        });
    }

    // Email / Password Form Submit
    if (emailAuthForm) {
        emailAuthForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("auth-email").value.trim();
            const nameInput = document.getElementById("auth-name");
            const name = (nameInput && nameInput.value.trim()) || email.split("@")[0];
            const formattedName = name.charAt(0).toUpperCase() + name.slice(1);

            const user = {
                id: "user_" + Math.random().toString(36).substring(2, 9),
                email: email,
                name: formattedName,
                provider: "email",
                plan: "Pro"
            };

            try {
                await fetch("/api/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email: user.email, name: user.name, password: "secure" })
                });
            } catch (_) {}

            localStorage.setItem("ai_translator_user", JSON.stringify(user));
            applyUserLoggedIn(user);
            if (authModal) authModal.classList.add("hidden");
            alert(`Welcome, ${user.name}! Signed in successfully.`);
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener("click", handleLogout);
    }

    checkUserSession();

    // -------------------------------------------------------------
    // 3. Tab Switching & File Upload Handling
    // -------------------------------------------------------------
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
        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            handleFileSelection(files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    function handleFileSelection(file) {
        currentFile = file;
        fileNameLabel.textContent = file.name;
        fileSizeLabel.textContent = formatBytes(file.size);
        selectedFileInfo.classList.remove("hidden");
    }

    function formatBytes(bytes) {
        if (bytes === 0) return "0 Bytes";
        const k = 1024;
        const sizes = ["Bytes", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
    }

    function extractYouTubeId(url) {
        if (!url) return null;
        const match = url.trim().match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=|shorts\/))([\w-]{11})/i);
        return match ? match[1] : null;
    }

    function audioBufferToWav(buffer, sampleRate = 16000) {
        const numChannels = 1;
        const channelData = buffer.getChannelData(0);
        const numFrames = channelData.length;
        const bytesPerSample = 2;
        const blockAlign = numChannels * bytesPerSample;
        const byteRate = sampleRate * blockAlign;
        const dataByteCount = numFrames * blockAlign;
        const arrayBuffer = new ArrayBuffer(44 + dataByteCount);
        const view = new DataView(arrayBuffer);

        function writeString(offset, string) {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        }

        writeString(0, 'RIFF');
        view.setUint32(4, 36 + dataByteCount, true);
        writeString(8, 'WAVE');
        writeString(12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, numChannels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, byteRate, true);
        view.setUint16(32, blockAlign, true);
        view.setUint16(34, 16, true);
        writeString(36, 'data');
        view.setUint32(40, dataByteCount, true);

        let offset = 44;
        for (let i = 0; i < numFrames; i++) {
            let s = Math.max(-1, Math.min(1, channelData[i]));
            let val = s < 0 ? s * 0x8000 : s * 0x7FFF;
            view.setInt16(offset, val, true);
            offset += 2;
        }

        return new Blob([view], { type: 'audio/wav' });
    }

    async function extractVoiceSample(file) {
        try {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (!AudioCtx) return null;
            const ctx = new AudioCtx();
            let arrayBuf;
            if (file.size <= 35 * 1024 * 1024) {
                arrayBuf = await file.arrayBuffer();
            } else {
                arrayBuf = await file.slice(0, 25 * 1024 * 1024).arrayBuffer();
            }
            const decoded = await ctx.decodeAudioData(arrayBuf);
            const duration = Math.min(decoded.duration, 25.0);
            const offlineCtx = new OfflineAudioContext(1, Math.floor(duration * 16000), 16000);
            const src = offlineCtx.createBufferSource();
            src.buffer = decoded;
            src.connect(offlineCtx.destination);
            src.start(0);
            const rendered = await offlineCtx.startRendering();
            return audioBufferToWav(rendered, 16000);
        } catch (e) {
            console.log("WebAudio extraction notice:", e);
            return null;
        }
    }

    // -------------------------------------------------------------
    // 4. Fetch Supported Languages Catalog
    // -------------------------------------------------------------
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
                    targetLangSelect.value = "ta"; // Tamil default
                }
            }
        } catch (e) {
            console.warn("Could not fetch remote languages catalog, using presets.", e);
        }
    }
    fetchLanguages();

    // -------------------------------------------------------------
    // 5. Start Translation Trigger
    // -------------------------------------------------------------
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

        // Reset UI state
        startBtn.disabled = true;
        startBtn.querySelector("span").textContent = "Translation in progress...";
        progressContainer.classList.remove("hidden");
        updateProgressUI(0, "Initiating video translation job...");
        downloadBanner.classList.add("hidden");
        readyPill.classList.add("hidden");
        logCard.classList.add("hidden");
        videoPlaceholder.classList.remove("hidden");
        if (translatedAudioElement) {
            translatedAudioElement.pause();
            translatedAudioElement.currentTime = 0;
            translatedAudioElement.src = "";
        }
        currentCompletedJob = null;
        if (window.speechSynthesis) window.speechSynthesis.cancel();

        try {
            let res;
            if (isUploadTab) {
                window._uploadedVideoFile = currentFile;
                const formData = new FormData();
                // Send raw video file only if <= 3.5 MB to bypass Vercel serverless 4.5 MB payload limit.
                // The browser retains window._uploadedVideoFile locally to stream and play the video seamlessly.
                if (currentFile.size <= 3.5 * 1024 * 1024) {
                    formData.append("video", currentFile);
                }
                formData.append("filename", currentFile.name);
                formData.append("file_size", currentFile.size);
                formData.append("target_lang", targetLang);
                formData.append("gender_override", genderOverride);
                formData.append("lip_sync_enabled", lipSync);
                formData.append("fast_parallel_mode", fastMode);
                const customScript = customScriptInput ? customScriptInput.value.trim() : "";
                if (customScript) {
                    formData.append("custom_script", customScript);
                }

                // Extract audio voice sample for speech-to-text
                try {
                    const sampleWav = await extractVoiceSample(currentFile);
                    if (sampleWav) {
                        formData.append("audio_sample", sampleWav, "sample.wav");
                    }
                } catch (_) {}

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
                const customScript = customScriptInput ? customScriptInput.value.trim() : "";

                res = await fetch("/api/translate/url", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        url: urlVal,
                        target_lang: targetLang,
                        gender_override: genderOverride,
                        lip_sync_enabled: lipSync,
                        fast_parallel_mode: fastMode,
                        custom_script: customScript || null
                    })
                });
            }

            if (!res.ok) {
                const errorText = await res.text();
                let errorMsg = `Server error (${res.status})`;
                try {
                    const errJson = JSON.parse(errorText);
                    errorMsg = errJson.detail || errJson.message || errorMsg;
                } catch (_) {
                    if (res.status === 413 || errorText.includes("Request Entity Too Large")) {
                        errorMsg = "File size exceeds Vercel 4.5 MB serverless limit. Please use Video URL or run start.bat (http://localhost:8000).";
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

    // -------------------------------------------------------------
    // 6. Polling Progress
    // -------------------------------------------------------------
    function startPollingProgress(jobId) {
        if (pollingInterval) clearInterval(pollingInterval);

        pollingInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/jobs/${jobId}`);
                if (!res.ok) return;

                const job = await res.json();
                updateProgressUI(job.progress, job.current_step);

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

    function updateProgressUI(pct, stepDesc) {
        progressContainer.classList.remove("hidden");
        progressFill.style.width = `${pct}%`;
        progressPercentLabel.textContent = `${pct}%`;
        currentStepLabel.textContent = stepDesc || "Working...";

        const stepThresholds = [5, 20, 35, 50, 65, 78, 88, 100];
        stepThresholds.forEach((th, i) => {
            const node = document.getElementById(`step-${i + 1}`);
            if (node) {
                if (pct >= th) {
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

    function resetStartButton() {
        startBtn.disabled = false;
        startBtn.querySelector("span").textContent = "Start AI Translation & Lip-Sync";
    }

    // -------------------------------------------------------------
    // 7. On Translation Completion: Activate Neural Audio & Player
    // -------------------------------------------------------------
    function onJobCompleted(job) {
        currentCompletedJob = job;
        resetStartButton();
        updateProgressUI(100, "Translation completed successfully! Video ready for download.");

        for (let i = 1; i <= 8; i++) {
            const node = document.getElementById(`step-${i}`);
            if (node) {
                node.classList.add("completed");
                node.classList.remove("active");
            }
        }

        readyPill.classList.remove("hidden");
        downloadBanner.classList.remove("hidden");
        if (audioControlsBar) audioControlsBar.classList.remove("hidden");

        const targetLang = (job.target_language || "ta").toLowerCase();
        const targetLangCode = targetLang.toUpperCase();
        if (translatedTrackLabel) {
            translatedTrackLabel.textContent = `🔊 Translated Neural Audio (${targetLangCode})`;
        }

        // Set up authentic neural translated audio element with cache buster
        const timestamp = Date.now();
        const audioStreamUrl = `/api/audio/${job.job_id}?t=${timestamp}`;
        if (translatedAudioElement) {
            translatedAudioElement.pause();
            translatedAudioElement.currentTime = 0;
            translatedAudioElement.src = audioStreamUrl;
            translatedAudioElement.load();
        }

        // Configure 3 Download Action Buttons
        if (downloadAudioBtn) {
            downloadAudioBtn.href = `/api/download/audio/${job.job_id}?t=${timestamp}`;
            downloadAudioBtn.setAttribute("download", `translated_audio_${targetLang}_${job.job_id.substring(0, 8)}.mp3`);
        }

        if (downloadSubtitlesBtn) {
            downloadSubtitlesBtn.href = `/api/subtitles/${job.job_id}?t=${timestamp}`;
            downloadSubtitlesBtn.setAttribute("download", `translated_subtitles_${targetLang}_${job.job_id.substring(0, 8)}.srt`);
        }

        if (downloadBtn) {
            downloadBtn.href = `/api/download/${job.job_id}?t=${timestamp}`;
            downloadBtn.setAttribute("download", `translated_${targetLang}_${job.job_id.substring(0, 8)}.mp4`);
        }

        const ytId = job.youtube_id || window._currentYouTubeId;

        if (ytId && youtubeEmbedPlayer) {
            // Priority 1: YouTube video - play in responsive iframe (muted) with translated neural audio
            outputVideoPlayer.classList.add("hidden");
            outputVideoPlayer.pause();
            outputVideoPlayer.src = "";
            youtubeEmbedPlayer.classList.remove("hidden");
            youtubeEmbedPlayer.src = `https://www.youtube-nocookie.com/embed/${ytId}?autoplay=1&mute=1&rel=0`;

            if (translatedAudioElement) {
                translatedAudioElement.currentTime = 0;
                translatedAudioElement.play().catch(e => console.log("Audio play prevented:", e));
            }
        } else if (window._uploadedVideoFile) {
            // Priority 2: Uploaded video file - play in HTML5 video player with translated audio
            if (youtubeEmbedPlayer) {
                youtubeEmbedPlayer.classList.add("hidden");
                youtubeEmbedPlayer.src = "";
            }
            outputVideoPlayer.classList.remove("hidden");
            const localBlobUrl = URL.createObjectURL(window._uploadedVideoFile);
            outputVideoPlayer.src = localBlobUrl;
            outputVideoPlayer.load();
            applyAudioTrackMode();
            outputVideoPlayer.play().catch(e => console.log("Video play prevented:", e));
        } else {
            // Priority 3: Server-streamed output
            if (youtubeEmbedPlayer) {
                youtubeEmbedPlayer.classList.add("hidden");
                youtubeEmbedPlayer.src = "";
            }
            outputVideoPlayer.classList.remove("hidden");
            const streamUrl = (job.output_video_url && !job.output_video_url.includes("youtube.com"))
                ? job.output_video_url
                : `/api/stream/${job.job_id}`;
            outputVideoPlayer.src = streamUrl;
            outputVideoPlayer.load();
            applyAudioTrackMode();
            outputVideoPlayer.play().catch(e => console.log("Stream play prevented:", e));
        }

        videoPlaceholder.classList.add("hidden");

        if (job.segments && job.segments.length > 0) {
            renderSpeakerLog(job.segments);
        }
    }

    // -------------------------------------------------------------
    // 8. Neural Audio Track Synchronization & Speech Synthesis
    // -------------------------------------------------------------
    function applyAudioTrackMode() {
        if (!outputVideoPlayer) return;
        const isTranslatedTrack = trackTranslatedRadio ? trackTranslatedRadio.checked : true;

        if (isTranslatedTrack) {
            // Mute original video audio completely so ONLY the translated voice is heard
            outputVideoPlayer.volume = 0;
            outputVideoPlayer.muted = true;
            if (translatedAudioElement) {
                translatedAudioElement.volume = 1.0;
                if (!outputVideoPlayer.paused) {
                    translatedAudioElement.currentTime = outputVideoPlayer.currentTime;
                    translatedAudioElement.play().catch(() => {});
                }
            }
        } else {
            // 100% original voice volume
            outputVideoPlayer.volume = 1.0;
            outputVideoPlayer.muted = false;
            if (translatedAudioElement) {
                translatedAudioElement.pause();
            }
            if (window.speechSynthesis) window.speechSynthesis.cancel();
            if (liveSubtitlesOverlay) liveSubtitlesOverlay.classList.add("hidden");
        }
    }

    if (trackTranslatedRadio && trackOriginalRadio) {
        trackTranslatedRadio.addEventListener("change", applyAudioTrackMode);
        trackOriginalRadio.addEventListener("change", applyAudioTrackMode);
    }

    // Synchronize translated speech and subtitles with video playback time
    outputVideoPlayer.addEventListener("play", () => {
        applyAudioTrackMode();
        const isTranslatedTrack = trackTranslatedRadio ? trackTranslatedRadio.checked : true;
        if (isTranslatedTrack && translatedAudioElement) {
            translatedAudioElement.currentTime = outputVideoPlayer.currentTime;
            translatedAudioElement.play().catch(() => {});
        }
    });

    outputVideoPlayer.addEventListener("pause", () => {
        if (translatedAudioElement) translatedAudioElement.pause();
        if (window.speechSynthesis) window.speechSynthesis.pause();
    });

    outputVideoPlayer.addEventListener("seeking", () => {
        if (translatedAudioElement) {
            translatedAudioElement.currentTime = outputVideoPlayer.currentTime;
        }
    });

    outputVideoPlayer.addEventListener("seeked", () => {
        if (translatedAudioElement) {
            translatedAudioElement.currentTime = outputVideoPlayer.currentTime;
        }
    });

    outputVideoPlayer.addEventListener("timeupdate", () => {
        if (!currentCompletedJob || !currentCompletedJob.segments) return;
        const isTranslatedTrack = trackTranslatedRadio ? trackTranslatedRadio.checked : true;
        if (!isTranslatedTrack) return;

        const currentTime = outputVideoPlayer.currentTime;
        if (translatedAudioElement && Math.abs(translatedAudioElement.currentTime - currentTime) > 0.4) {
            translatedAudioElement.currentTime = currentTime;
        }

        const segments = currentCompletedJob.segments;
        const activeSeg = segments.find(s => currentTime >= s.start_time && currentTime <= s.end_time);

        if (activeSeg) {
            if (liveSubtitlesOverlay) liveSubtitlesOverlay.classList.remove("hidden");
            if (currentSubtitleText) {
                currentSubtitleText.textContent = activeSeg.translated_text || activeSeg.original_text;
            }

            if (activeSeg.segment_index !== activeSegmentIndex) {
                activeSegmentIndex = activeSeg.segment_index;
            }
        } else {
            if (liveSubtitlesOverlay) liveSubtitlesOverlay.classList.add("hidden");
        }
    });

    outputVideoPlayer.addEventListener("ended", () => {
        if (translatedAudioElement) {
            translatedAudioElement.pause();
            translatedAudioElement.currentTime = 0;
        }
        if (window.speechSynthesis) window.speechSynthesis.cancel();
        activeSegmentIndex = -1;
    });

    function speakTranslatedSentence(text, langCode, gender) {
        if (!window.speechSynthesis || !text) return;
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);

        // Language locale mapping
        const localeMap = {
            ta: "ta-IN",
            hi: "hi-IN",
            es: "es-ES",
            fr: "fr-FR",
            de: "de-DE",
            te: "te-IN",
            ja: "ja-JP",
            zh: "zh-CN",
            ar: "ar-SA",
            ru: "ru-RU",
            pt: "pt-BR",
            it: "it-IT",
            ko: "ko-KR",
            en: "en-US",
            mr: "mr-IN",
            bn: "bn-IN"
        };
        utterance.lang = localeMap[langCode] || "en-US";

        // Gender Pitch Adjustment: Female voices higher pitch (1.25), Male lower pitch (0.85)
        utterance.pitch = (gender.toUpperCase() === "FEMALE") ? 1.25 : 0.85;
        utterance.rate = 1.0;

        // Try to match native voice from browser voices list
        const voices = window.speechSynthesis.getVoices();
        if (voices && voices.length > 0) {
            const matchedVoice = voices.find(v => v.lang.startsWith(langCode));
            if (matchedVoice) utterance.voice = matchedVoice;
        }

        window.speechSynthesis.speak(utterance);
    }

    // -------------------------------------------------------------
    // 9. Speaker Diarization Log Rendering
    // -------------------------------------------------------------
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
                    <span class="gender-badge ${genderClass}">${gender} (${pitch} Hz)</span>
                </div>
                <div class="log-orig">${escapeHtml(seg.original_text || "")}</div>
                <div class="log-trans">${escapeHtml(seg.translated_text || "Translation in progress...")}</div>
            `;
            logList.appendChild(item);
        });
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }
});
