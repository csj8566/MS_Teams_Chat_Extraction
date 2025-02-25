from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv

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

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        messages = [
            {
                "role": "system",
                "content": "당신은 데이터 분석 전문가입니다. 챗봇 데이터를 분석하고 인사이트를 제공하는 것이 전문입니다."
            },
            {
                "role": "user",
                "content": request.question
            }
        ]

        response = client.chat.completions.create(
            model="sonar",
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        print(f"[DEBUG] API 응답 확인: {response}") 
        
        answer = response.choices[0].message.content
        return ChatResponse(answer=answer)
        
    except Exception as e:
        print(f"[DEBUG] 예상치 못한 오류: {str(e)}") 
        raise HTTPException(status_code=500, detail=f"챗봇 응답 생성 실패: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
