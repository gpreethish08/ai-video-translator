package com.aivideo.translator.controller;

import com.aivideo.translator.model.TranslationJob;
import com.aivideo.translator.database.DatabaseService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/translate")
@CrossOrigin(origins = "*")
public class TranslationController {

    private final DatabaseService dbService = new DatabaseService();

    @GetMapping("/languages")
    public ResponseEntity<List<Map<String, String>>> getSupportedLanguages() {
        return ResponseEntity.ok(dbService.getSupportedLanguages());
    }

    @GetMapping("/jobs/{id}")
    public ResponseEntity<Map<String, Object>> getJobStatus(@PathVariable String id) {
        Map<String, Object> job = dbService.getJobById(id);
        if (job.isEmpty()) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(job);
    }

    @PostMapping("/jobs")
    public ResponseEntity<Map<String, String>> createJob(@RequestBody TranslationJob job) {
        Map<String, String> response = new HashMap<>();
        response.put("status", "QUEUED");
        response.put("job_id", job.getId());
        response.put("message", "Job registered with Java backend service");
        return ResponseEntity.ok(response);
    }
}
