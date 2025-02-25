# Redis 를 사용하여 최근 5개의 질문과 그에 대한 답변을 챗봇이 기억하도록 합니다.
# 챗봇이 과거 대화를 기억하지 못하는 문제를 해결하기 위한 코드입니다.

import redis
import json
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

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30
    )
    # 연결 테스트
    if redis_client.ping():
        print("[DEBUG] Redis 연결 성공")
    else:
        print("[ERROR] Redis 연결 실패: ping 응답 없음")
        raise redis.ConnectionError("Redis server did not respond to ping")
except redis.ConnectionError as e:
    print(f"[ERROR] Redis 연결 실패: {str(e)}")
    raise
except Exception as e:
    print(f"[ERROR] 예상치 못한 Redis 오류: {str(e)}")
    raise

# Redis 에 사용자 질문과 챗봇 응답 저장
def save_chat_history(session_id, user_message, bot_response, max_history=5): # 챗봇이 최대 최근 5개의 질문과 답변을 기억하도록 함
    history_key = f"chat_history:{session_id}"
    
    chat_entry = {"user": user_message, "bot": bot_response}
    history = redis_client.get(history_key)
    history_list = json.loads(history) if history else []
    
    # 최대 max_history 개만 유지, 넘어가는 내용은 과거 것부터 삭제
    if len(history_list) > max_history:
        history_list.pop(0)
        
    history_list.append(chat_entry)
    redis_client.set(history_key, json.dumps(history_list), ex=3600) # 세션 만료 1시간
    
    
# Reids 에서 최근 대화 히스토리 가져오기
def get_chat_history(session_id):
    history_key = f"chat_history:{session_id}"
    history = redis_client.get(history_key)
    return json.loads(history) if history else []

print("[DEBUG] 별문제없쥬?")