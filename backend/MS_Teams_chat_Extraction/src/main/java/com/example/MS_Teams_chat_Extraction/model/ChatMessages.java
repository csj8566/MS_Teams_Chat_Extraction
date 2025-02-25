package com.example.MS_Teams_chat_Extraction.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Entity
@Table(name = "chat_messages")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ChatMessages {

    @Id
    @Column(name = "message_id", length = 50)
    private String messageId;

    @Column(name = "reply_to_id", length = 50)
    private String replyToId;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "sender_name", nullable = false, length = 255)
    private String senderName;

    @Column(name = "message", nullable = false, columnDefinition = "TEXT")
    private String message;

    @Column(name = "reactions", columnDefinition = "TEXT")
    private String reactions;

}