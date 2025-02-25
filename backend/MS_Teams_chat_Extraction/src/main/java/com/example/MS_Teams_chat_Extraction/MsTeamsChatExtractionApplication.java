package com.example.MS_Teams_chat_Extraction;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.PropertySource;

@SpringBootApplication
@PropertySource("classpath:env.properties")
public class MsTeamsChatExtractionApplication {

	public static void main(String[] args) {
		SpringApplication.run(MsTeamsChatExtractionApplication.class, args);
	}

}
