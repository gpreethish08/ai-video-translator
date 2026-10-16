package com.aivideo.translator.database;

import java.sql.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Enterprise Database Service for AI Video Translator.
 * Handles JDBC operations for SQLite and PostgreSQL databases.
 */
public class DatabaseService {

    private final String dbUrl;

    public DatabaseService() {
        this.dbUrl = "jdbc:sqlite:database/translator.db";
    }

    public DatabaseService(String customDbUrl) {
        this.dbUrl = customDbUrl;
    }

    private Connection connect() throws SQLException {
        return DriverManager.getConnection(this.dbUrl);
    }

    /**
     * Get a translation job by ID
     */
    public Map<String, Object> getJobById(String jobId) {
        String sql = "SELECT * FROM translation_jobs WHERE id = ?";
        Map<String, Object> job = new HashMap<>();

        try (Connection conn = this.connect();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {
            
            pstmt.setString(1, jobId);
            ResultSet rs = pstmt.executeQuery();

            if (rs.next()) {
                job.put("id", rs.getString("id"));
                job.put("title", rs.getString("title"));
                job.put("status", rs.getString("status"));
                job.put("progress_percentage", rs.getInt("progress_percentage"));
                job.put("target_language", rs.getString("target_language"));
                job.put("output_video_path", rs.getString("output_video_path"));
            }
        } catch (SQLException e) {
            System.err.println("Database query error: " + e.getMessage());
        }
        return job;
    }

    /**
     * Update job status and progress
     */
    public void updateJobProgress(String jobId, String status, int progress, String step) {
        String sql = "UPDATE translation_jobs SET status = ?, progress_percentage = ?, current_step = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?";

        try (Connection conn = this.connect();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {

            pstmt.setString(1, status);
            pstmt.setInt(2, progress);
            pstmt.setString(3, step);
            pstmt.setString(4, jobId);
            pstmt.executeUpdate();

        } catch (SQLException e) {
            System.err.println("Database update error: " + e.getMessage());
        }
    }

    /**
     * Retrieve supported languages list
     */
    public List<Map<String, String>> getSupportedLanguages() {
        List<Map<String, String>> languages = new ArrayList<>();
        String sql = "SELECT code, name, native_name, default_male_voice, default_female_voice FROM supported_languages WHERE is_active = 1";

        try (Connection conn = this.connect();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {

            while (rs.next()) {
                Map<String, String> lang = new HashMap<>();
                lang.put("code", rs.getString("code"));
                lang.put("name", rs.getString("name"));
                lang.put("native_name", rs.getString("native_name"));
                lang.put("male_voice", rs.getString("default_male_voice"));
                lang.put("female_voice", rs.getString("default_female_voice"));
                languages.add(lang);
            }
        } catch (SQLException e) {
            System.err.println("Failed to fetch languages: " + e.getMessage());
        }
        return languages;
    }
}
