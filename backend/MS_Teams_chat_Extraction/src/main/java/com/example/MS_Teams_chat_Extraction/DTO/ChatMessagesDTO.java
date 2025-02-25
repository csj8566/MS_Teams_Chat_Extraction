package com.example.MS_Teams_chat_Extraction.dto;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

import com.example.MS_Teams_chat_Extraction.DTO.ReplyMessageDTO;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
public class ChatMessagesDTO {
    private static final DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private String messageId;        // 메시지 고유 ID
    private String replyToId;        // 답글인 경우 원본 메시지 ID
    private String senderName;
    private String message;
    private String createdAt;
    private String cssClass;
    private List<String> reactions;
    private ReplyMessageDTO replyTo; // 답글인 경우 원본 메시지 정보

    // 단일 생성자만 유지
    public ChatMessagesDTO(String messageId, String replyToId, String senderName, String message, LocalDateTime createdAt, String cssClass, List<String> reactions, ReplyMessageDTO replyTo) {
        this.messageId = messageId;
        this.senderName = senderName;
        this.message = message;
        this.createdAt = createdAt.format(formatter);
        this.cssClass = cssClass;
        this.reactions = reactions;
        this.replyTo = replyTo;
    }
}