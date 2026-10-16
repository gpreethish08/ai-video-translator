package com.aivideo.translator;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class VideoTranslatorApplication {

    public static void main(String[] args) {
        System.out.println("Starting Enterprise Java AI Video Translator Service...");
        SpringApplication.run(VideoTranslatorApplication.class, args);
    }
}
