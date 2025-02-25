package com.example.MS_Teams_chat_Extraction.controller;

import com.example.MS_Teams_chat_Extraction.DTO.ReplyMessageDTO;
import com.example.MS_Teams_chat_Extraction.model.ChatMessages;
import com.example.MS_Teams_chat_Extraction.repository.ChatMessagesRepository;
import com.example.MS_Teams_chat_Extraction.dto.ChatMessagesDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.stream.Collectors;

@Controller
@RequiredArgsConstructor
public class ChatMessagesController {

    private final ChatMessagesRepository chatMessagesRepository;

    @GetMapping("/")
    public String index(Model model) {
        List<ChatMessages> messages = (List<ChatMessages>) chatMessagesRepository.findAll();

        // 메시지 ID로 쉽게 찾을 수 있도록 Map 생성
        Map<String, ChatMessages> messageMap = new HashMap<>();
        messages.forEach(msg -> messageMap.put(msg.getMessageId(), msg));

        // 메시지를 변환하여 Mustache에 전달 (CSS 클래스 부착)
        List<ChatMessagesDTO> messagesDTOs = messages.stream()
                // "보낸 사람이 알 수 없음"인 경우 제외
                .filter(msg -> msg.getSenderName() != null && !msg.getSenderName().equals("알 수 없음"))
                .map(msg -> {
                    // 답글인 경우 원본 메시지 정보 가져오기
                    ReplyMessageDTO replyTo = null;
                    if (msg.getReplyToId() != null && !msg.getReplyToId().isEmpty()) {
                        ChatMessages originalMsg = messageMap.get(msg.getReplyToId());
                        if (originalMsg != null) {
                            replyTo = new ReplyMessageDTO(
                                originalMsg.getMessageId(),
                                originalMsg.getSenderName(),
                                originalMsg.getMessage(),
                                originalMsg.getCreatedAt()
                            );
                        }
                    }

                    return new ChatMessagesDTO(
                            msg.getMessageId(),
                            msg.getReplyToId(),
                            msg.getSenderName(),
                            msg.getMessage(),
                            msg.getCreatedAt(),
                            msg.getSenderName().equals("고수현") ? "sent" : "received", // 여기 하드코딩 돼있는 부분 본인 이름으로 처리하는 로직 추가 필요!
                            convertReactions(msg.getReactions()),  // 여기서 reactions 변환
                            replyTo
                    );
                })
                .collect(Collectors.toList());

        model.addAttribute("messages", messagesDTOs);
        return "chatting";
    }

    private List<String> convertReactions(String rawReactions) {
        if (rawReactions == null || rawReactions.isEmpty()) {
            return List.of();
        }

        Map<String, String> emojiMap = Map.of(
                "like", "👍",
                "laugh", "😂",
                "surprised", "😲",
                "heart", "❤️",
                "🤘", "🤘",
                "✖️", "✖️",
                "angry", "😡"
        );

        return Arrays.stream(rawReactions.split(","))
                .map(reaction -> reaction.trim().replace("(None)", "").trim())
                .filter(reaction -> !reaction.isEmpty())
                .map(reaction -> emojiMap.getOrDefault(reaction, reaction))
                .collect(Collectors.toList());
    }
}