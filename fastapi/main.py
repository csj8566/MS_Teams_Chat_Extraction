from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv
from vectorstore import search_faiss
from memory import get_chat_history, save_chat_history


load_dotenv()
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

app = FastAPI(title="AI 챗봇")

# OpenAI 클라이언트 초기화
client = OpenAI(
    api_key=PERPLEXITY_API_KEY,
    base_url="https://api.perplexity.ai"
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
        messages = [
            {
                "role": "system",
                "content": "당신은 대화 기록을 분석하여 질문에 대한 정확한 답변을 제공하는 AI입니다. "
                   "제공된 데이터(RAG 검색 결과)와 현재 대화 내용을 기반으로만 답변하세요. "
                   "추측하거나 사실이 아닌 내용을 생성하지 마세요. "
                   "만약 주어진 정보에서 답을 찾을 수 없다면, '현재 대화 내용에서는 알 수 없는 정보입니다.'라고 답변하세요."
            }
        ]
        
        # 최근 대화 기록 추가 (기본값 : 5개)
        for entry in chat_history:
            messages.append({"role": "user", "content": entry["user"]})
            messages.append({"role": "assistant", "content": entry["bot"]})
            
        # FAISS 검색 결과를 컨텍스트로 추가
        if context:
            messages.append({"role": "system", "content": f"Relevant contenxt:\n{context}"})
            
        # 사용자 질문 추가
        messages.append({"role": "user", "content": user_question})

        # LLM API 호출
        response = client.chat.completions.create(
            model="sonar",
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
