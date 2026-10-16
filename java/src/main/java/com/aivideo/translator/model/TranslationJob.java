package com.aivideo.translator.model;

public class TranslationJob {
    private String id;
    private String title;
    private String inputSourceType;
    private String inputUrl;
    private String originalVideoPath;
    private String targetLanguage;
    private String status;
    private int progressPercentage;
    private String outputVideoPath;
    private boolean lipSyncEnabled;

    public TranslationJob() {}

    public TranslationJob(String id, String title, String inputSourceType, String targetLanguage) {
        this.id = id;
        this.title = title;
        this.inputSourceType = inputSourceType;
        this.targetLanguage = targetLanguage;
        this.status = "QUEUED";
        this.progressPercentage = 0;
        this.lipSyncEnabled = true;
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getInputSourceType() { return inputSourceType; }
    public void setInputSourceType(String inputSourceType) { this.inputSourceType = inputSourceType; }

    public String getInputUrl() { return inputUrl; }
    public void setInputUrl(String inputUrl) { this.inputUrl = inputUrl; }

    public String getOriginalVideoPath() { return originalVideoPath; }
    public void setOriginalVideoPath(String originalVideoPath) { this.originalVideoPath = originalVideoPath; }

    public String getTargetLanguage() { return targetLanguage; }
    public void setTargetLanguage(String targetLanguage) { this.targetLanguage = targetLanguage; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public int getProgressPercentage() { return progressPercentage; }
    public void setProgressPercentage(int progressPercentage) { this.progressPercentage = progressPercentage; }

    public String getOutputVideoPath() { return outputVideoPath; }
    public void setOutputVideoPath(String outputVideoPath) { this.outputVideoPath = outputVideoPath; }

    public boolean isLipSyncEnabled() { return lipSyncEnabled; }
    public void setLipSyncEnabled(boolean lipSyncEnabled) { this.lipSyncEnabled = lipSyncEnabled; }
}
