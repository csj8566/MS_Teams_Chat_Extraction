from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv
from vectorstore import search_faiss
from memory import get_chat_history, save_chat_history


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="AI 챗봇")

# OpenAI 클라이언트 초기화
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://api.openai.com/v1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

# 요청 데이터 모델델
class ChatRequest(BaseModel):
    session_id: str
    question: str


class ChatResponse(BaseModel):
    answer: str


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        session_id = request.session_id
        user_question = request.question
        
        # Redis에서 세션별 대화 기록 가져오기
        chat_history = get_chat_history(session_id)
        
        # FAISS 에서 관련 문서 검색 (RAG 실행)
        retrieved_docs = search_faiss(user_question)
        context = "\n".join(retrieved_docs)
        
        # LLM 에 전달할 메시지 구성
        messages = []
        
        # 시스템 메시지 추가
        messages.append({
            "role": "system",
            "content": ("당신은 대화 기록을 기반으로 질문에 대한 정확한 답변을 제공하는 AI입니다. "
                "제공된 데이터(RAG 검색 결과) 및 최근 대화 기록을 기반으로 최대한 정확한 답변을 제공하세요. "
                "정보의 신뢰도를 판단하여 다음과 같이 응답해야 합니다:\n\n"
                "1️⃣ 신뢰도가 높은 경우 → '대화 기록에 따르면 ...' 형태로 구체적으로 응답\n"
                "2️⃣ 신뢰도가 중간인 경우 → '대화 내용에서 단서가 있지만 확실하지 않습니다.' 라고 설명\n"
                "3️⃣ 신뢰도가 낮은 경우 → '현재 대화 내용만으로는 확신할 수 없습니다.' 라고 응답\n"
                "4️⃣ 대화에 해당 내용이 없는 경우 → '현재 대화 내용에서는 확인할 수 없습니다.'\n\n"
                "절대로 정보를 조작하거나 임의로 생성하지 마세요.")
        })
        
        # FAISS 검색 결과를 컨텍스트로 추가
        if context:
            messages.append({
                "role": "system",
                "content": f"Relevant context:\n{context}"
            })
            
        # 최근 대화 기록 추가 (기본값 : 5개)
        for entry in chat_history:
            messages.append({"role": "user", "content": entry["user"]})
            messages.append({"role": "assistant", "content": entry["bot"]})
            
        # 현재 사용자 질문 추가
        messages.append({"role": "user", "content": user_question})

        print("[DEBUG] 전송할 메시지:", messages)

        # LLM API 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        print(f"[DEBUG] API 응답 확인: {response}") 
        
        answer = response.choices[0].message.content
        
        # Redis 에 새로운 대화 기록 저장
        save_chat_history(session_id, user_question, answer)
        
        return ChatResponse(answer=answer)
        
    except Exception as e:
        print(f"[DEBUG] 예상치 못한 오류: {str(e)}") 
        raise HTTPException(status_code=500, detail=f"챗봇 응답 생성 실패: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
