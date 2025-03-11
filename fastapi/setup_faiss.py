# 로컬 DB를 가져와 FAISS 에 저장할 수 있도록 하는 코드

import mysql.connector
import faiss
import numpy as np
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import os
from tqdm import tqdm

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
print(f"[DEBUG] api key 확인 : {OPENAI_API_KEY}")


db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("DB_PASSWORD"),
    database='ms_chats'
)

def fetch_documents():
    # mysql 에서 데이터를 가져와서 리스트로 반환
    cursor = db.cursor(dictionary=True)
    
    # chat_messages 테이블에서 "시간", "보낸 사람", "메시지"만 추출
    cursor.execute("SELECT created_at, sender_name, message from chat_messages;")
    documents = [
        f"created_at: {row['created_at']}\nsender_name: {row['sender_name']}\nmessage: {row['message']}"
        for row in cursor.fetchall()
    ]
    cursor.close()
    print(f"[DEBUG] 총 {len(documents)}개의 문서를 가져왔습니다.")
    return documents

# FAISS 벡터화 및 저장
documents = fetch_documents()
embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY,
                                   model="text-embedding-3-small")

# tqdm을 사용하여 진행 상태 표시
print("[DEBUG] 문서 벡터화 시작...")
vectors = []
for doc in tqdm(documents, desc="문서 벡터화 진행 중"):
    vector = embedding_model.embed_query(doc)
    vectors.append(vector)


dimension = len(vectors[0])
print(f"[DEBUG] 벡터 차원: {dimension}")


# FAISS 인덱스 생성 (벡터 데이터를 효율적으로 저장하고 검색하기 위한 구조를 의미)
# L2 거리 기반 유사도를 통해 RAG 진행
print("[DEBUG] FAISS 인덱스 생성 중...")
index = faiss.IndexFlatL2(dimension) # L2 거리 기반의 인덱스를 생성, dimension 만큼의 차원을 가지는 벡터를 저장할 공간을 만듦

print("[DEBUG] 벡터 추가 중...")
index.add(np.array(vectors).astype('float32')) # flaot32 로 변환해야 사용 가능

# FAISS 인덱스 저장
print("[DEBUG] FAISS 인덱스 저장 중...")
faiss.write_index(index, "faiss_index")
print("[DEBUG] FAISS 인덱스 저장 완료!")


