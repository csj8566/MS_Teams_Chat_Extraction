package com.example.MS_Teams_chat_Extraction.repository;

import com.example.MS_Teams_chat_Extraction.model.ChatMessages;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ChatMessagesRepository extends CrudRepository<ChatMessages, String> {
}
