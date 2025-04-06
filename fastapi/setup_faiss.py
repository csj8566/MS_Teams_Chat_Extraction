# 로컬 DB를 가져와 LangChain FAISS 벡터스토어에 저장할 수 있도록 하는 코드

import mysql.connector
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_progress import ProgressManager
from dotenv import load_dotenv
import os
from tqdm import tqdm

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
# print(f"[DEBUG] api key 확인 : {OPENAI_API_KEY}") # 보안 상 주석처리


db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("DB_PASSWORD"),
    database='ms_chats'
)

def fetch_documents():
    # mysql 에서 데이터를 가져와서 리스트로 반환
    cursor = db.cursor(dictionary=True)
    
    # chat_messages 테이블에서 "시간", "보낸 사람", "메시지"만 추출 + "id"도 추출하여 메타데이터 관리 용이하게 함
    # 사실 index 로 DB에서 데이터를 잘 찾아주기 때문에 id는 필요없기는 함
    cursor.execute("SELECT id, created_at, sender_name, message from chat_messages;")
    
    # LangChain Document 객체 리스트로 변환
    documents = []
    for row in cursor.fetchall():
        # 문서 내용
        content = f"created_at: {row['created_at']}\nsender_name: {row['sender_name']}\nmessage: {row['message']}"
        # 메타데이터 - 나중에 검색 시 유용하게 사용할 수 있음
        metadata = {
            "id": row['id'],
            "created_at": str(row['created_at']),
            "sender_name": row['sender_name']
        }
        # LangChain Document 객체 생성
        documents.append(Document(page_content=content, metadata=metadata))
    
    cursor.close()
    print(f"[DEBUG] 총 {len(documents)}개의 문서를 가져왔습니다.")
    return documents

# LangChain 임베딩 모델 초기화
embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY,
                                   model="text-embedding-3-small")

# 문서 가져오기
print("[DEBUG] 문서 로딩 중...")
documents = fetch_documents()

# LangChain FAISS 벡터스토어 생성 (tqdm 대신 ProgressManager로 진행 상태 표시)
print("[DEBUG] FAISS 인덱스 생성 중...")
with ProgressManager(embedding_model):
    vectorstore = FAISS.from_documents(documents, embedding_model)

# FAISS 인덱스 저장
print("[DEBUG] FAISS 인덱스 저장 중...")
vectorstore.save_local("faiss_index_langchain")
print("[DEBUG] FAISS 인덱스 저장 완료!")


