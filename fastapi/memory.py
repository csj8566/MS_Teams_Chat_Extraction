# Redis 를 사용하여 최근 5개의 질문과 그에 대한 답변을 챗봇이 기억하도록 함
# 챗봇이 과거 대화를 기억하지 못하는 문제를 해결하기 위한 코드
# LangChain의 메모리 시스템을 사용하여 챗봇 대화 기록을 관리하는 코드
# Redis를 사용하여 대화 기록을 저장하고, LangChain의 ConversationBufferMemory를 활용하여 대화 컨텍스트 유지

from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
import os
from dotenv import load_dotenv

load_dotenv()

# Redis 연결
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"

print("[DEBUG] Redis 설정 확인:")
print(f"[DEBUG] - Host: {REDIS_HOST}")
print(f"[DEBUG] - Port: {REDIS_PORT}")
print(f"[DEBUG] - URL: {REDIS_URL}")




# 세션별 메모리 객체를 캐싱하기 위한 딕셔너리
# 같은 session_id 하에서는 새로운 메모리 객체 만들지 않게 하기 위함
memory_cache = {}              

def get_langchain_memory(session_id, max_history=3):
    '''
    특정 세션에 대한 LangChain 메모리 객체를 반환

    Args:
        session_id(str) : 세션 ID
        max_history (int) : 유지할 최대 메시지 수

    Returns:
        ConversationBufferMemory : LangChain 메모리 객체
    '''

    # 이미 생성된 메모리 객체가 있으면 재사용
    if session_id in memory_cache:
        return memory_cache[session_id]
    
    try:
        '''
        ConversationBufferMemory (메모리 관리 : RedisChatMessageHistory를 사용하여 대화 컨텍스트를 관리(입력을 처리해 RedisChatMessageHistory에 전달))
        ↓
        RedisChatMessageHistory (메시지 저장소 : Redis 서버와 직접 통신하여 메시지를 저장하고 불러옴, 메시지를 Redis 서버에 저장)
        ↓
        Redis (데이터베이스 : 실제 데이터가 물리적으로 저장장)
        '''

        # Redis 기반 메시지 저장소 생성
        message_history = RedisChatMessageHistory(
            url=REDIS_URL,
            session_id=session_id,
            ttl=3600 # 1시간 후 만료
        )

        # LangChain 메모리 객체 생성
        memory = ConversationBufferMemory(
            chat_memory=message_history,
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )

        # 캐시에 메모리 저장
        memory_cache[session_id] = memory
        print(f"[DEBUG] 세션 {session_id}에 대한 새 메모리 객체 생성")
        return memory
    
    except Exception as e:
        print(f"[ERROR] 메모리 생성 중 오류: {str(e)}")
        raise


def save_chat_history(session_id, user_message, bot_response):
    '''
    대화 내용을 LangChain 메모리에 저장

    Args:
        session_id(str) : 세션 id
        user_messgae (str) : 사용자 메시지
        bot_response (str) : 챗봇의 응답
    '''

    # 현재 session_id 에 대한 메모리 객체가 존재하면 가져오고 없으면 새로 만듦
    memory = get_langchain_memory(session_id)

    # 사용자 메시지와 챗봇 응답을 메모리에 저장
    # input_key의 value를 HumanMessage로, output_key의 value를 AIMessage로 저장
    memory.save_context(
        {"input" : user_message}, # ConversationBufferMemory의 input_key 인자가 default로 "input"임
        {"answer" : bot_response} # output_key 와 일치해야 함
    )

    print(f"[DEBUG] 세션 {session_id}에 대화 내용 저장됨")


def get_chat_history(session_id):
    '''
    특정 세션의 대화 기록을 가져옴

    Args:
        session_id (str) : 세션 ID

    Returns:
        list: 대화 기록 목록
    '''

    # 메모리 객체 가져오기
    # 현재 session_id 에 대한 메모리 객체가 존재하면 가져오고 없으면 새로 만듦
    memory = get_langchain_memory(session_id)

    # LangChain 메모리에서 메시지 가져오기
    '''
    [예시]

        {
        "chat_history": [
            HumanMessage(content="안녕하세요!"),
            AIMessage(content="안녕하세요, 무엇을 도와드릴까요?"),
            HumanMessage(content="오늘 날씨 어때요?"),
            AIMessage(content="오늘은 맑고 화창한 날씨입니다.")
        ]
    }
    '''

    # ConversationBufferMemory는 RedisChatMessageHistory에 메시지 요청
    # RedisChatMessageHistory는 Redis 서버에서 데이터를 가져옴
    # 데이터는 ConversationBufferMemory를 통해 처리되어 반환됨
    messages = memory.load_memory_variables({}) # 빈 딕셔너리는 기본적으로 "추가 조건 없이 현재 저장된 모든 대화 기록을 가져오라"는 의미

    # 메시지 형식이 비어있으면 빈 리스트 반환
    if not messages or "chat_history" not in messages:
        return []
    
    # LangChain 메시지 객체를 사용자/봇 형식으로 변환
    history = []
    chat_messages = messages["chat_history"]

    # 메시지 쌍으로 변환
    for i in range(0, len(chat_messages), 2):
        if i + 1 < len(chat_messages): # 짝이 맞는지 확인, 만약 마지막 질문에 대한 답변이 없다면 if 문 이하 생략
            history.append({
                "user" : chat_messages[i].content,
                "bot" : chat_messages[i+1].content
            })

    return history

print("[DEBUG] LangChain 메모리 모듈 초기화 완료")