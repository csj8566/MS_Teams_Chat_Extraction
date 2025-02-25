package com.example.MS_Teams_chat_Extraction.DTO;

import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Getter
@NoArgsConstructor
public class ReplyMessageDTO {
    private String messageId;
    private String senderName;
    private String message;
    private LocalDateTime createdAt;

    public ReplyMessageDTO(String messageId, String senderName, String message, LocalDateTime createdAt) {
        this.messageId = messageId;
        this.senderName = senderName;
        this.message = message;
        this.createdAt = createdAt;
    }
}