from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagePlaceHolder
from langchain_core.output_parsers import StrOutputParser
from langcahin.schema import AIMessage, HumanMessage, SystemMessage
from memory import get_langchain_memory, save_chat_history, get_chat_history
from vectorstore import search_faiss



load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="LangChain 기반 AI 챗봇")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

# 요청 데이터 모델
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
        
        # LangChain 메모리에서 대화 기록 가져오기 (디버깅용이라 없애도 될 듯?)
        chat_history = get_chat_history(session_id)
        print(f"[DEBUG] 대화 기록 : {chat_history}")
        
        # LangChain 벡터스토어에서 관련 문서 검색 (RAG 실행)
        retrieved_docs = search_faiss(user_question)
        context = "\n".join(retrieved_docs)
        print(f"[DEBUG] 검색된 문서 수 : {len(retrieved_docs)}")
        
        # LangChain LLM 초기화
        llm = ChatOpenAI(
            api_key = OPENAI_API_KEY,
            model = "gpt-4o-mini",
            temperature=0.7,
            max_tokens=150
        )

        # LangChain 메모리 객체 가져오기
        memory = get_langchain_memory(session_id)

        # LangChain 프롬프트 템플릿 정의
        system_prompt = (
            "당신은 대화 기록을 기반으로 질문에 대한 정확한 답변을 제공하는 AI입니다. "
                "제공된 데이터(RAG 검색 결과) 및 최근 대화 기록을 기반으로 최대한 정확한 답변을 제공하세요. "
                "정보의 신뢰도를 판단하여 다음과 같이 응답해야 합니다:\n\n"
                "1️⃣ 신뢰도가 높은 경우 → '대화 기록에 따르면 ...' 형태로 구체적으로 응답\n"
                "2️⃣ 신뢰도가 중간인 경우 → '대화 내용에서 단서가 있지만 확실하지 않습니다.' 라고 설명\n"
                "3️⃣ 신뢰도가 낮은 경우 → '현재 대화 내용만으로는 확신할 수 없습니다.' 라고 응답\n"
                "4️⃣ 대화에 해당 내용이 없는 경우 → '현재 대화 내용에서는 확인할 수 없습니다.'\n\n"
                "절대로 정보를 조작하거나 임의로 생성하지 마세요."
        )

        # 검색 결과가 있는 경우 컨텍스트 추가
        if context:
            system_prompt += f"\n\n관련 컨텍스트:\n{context}"

        # LangChain 체인 구성
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagePlaceHolder(variable_name="chat_history"), # 나중에 실제 대화 기록이 들어갈 자리를 미리 확보 ("여기에 chat_history라는 이름의 값이 들어갈 거야!")
            ("human", "{input}") # LangChain만의 특별한 템플릿 문법, 나중에 실제 사용자 질문이 들어갈 자리를 표시
        ])

        chain = (
            prompt | llm | StrOutputParser()
        )

        # LangChain 체인 실행
        print("[DEBUG] LangChain 체인 실행 중...")
        answer = chain.invoke({
            "input" : user_question,
            "chat_history" : memory.load_memory_variables({})["chat_history"]
        })

        # LangChain 메모리에 대화 저장
        save_chat_history(session_id, user_question, answer)

        return ChatResponse(answer=answer)
    
    except Exception as e:
        print(f"[Error] 예상치 못한 오류 : {str(e)}")
        raise HTTPException(status_code=500, detail=f"챗봇 응답 생성 실패 : {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)