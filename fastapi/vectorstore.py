# FAISS라는 벡터스토어를 활용하여 벡터 검색을 수행하는 코드
# 사용자의 질문을 벡터로 변환하여, FAISS에서 유사한 벡터를 검색함
# 단, FAISS는 벡터만 저장하므로, 검색된 벡터의 원본 데이터(문서)는 MySQL에서 다시 조회해야 함
# 이를 통해 RAG(Retrieval-Augmented Generation) 기반 답변을 생성함

import faiss
import numpy as np
import mysql.connector
from langchain_openai import OpenAIEmbeddings
import openai
from dotenv import load_dotenv
import os


# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
print(f"[DEBUG] api key 확인 : {OPENAI_API_KEY}")

# open ai 임베딩 모델 : 벡터화 진행
embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY,
                                   model="text-embedding-3-small")
print("[DEBUG] embedding_model에 key 잘 들어갔는지 확인", embedding_model)

# setup_faiss.py 에서 만든 FAISS 인덱스를 불러옴
index = faiss.read_index("faiss_index")

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="ms_chats"
)

# OpenAI 를 사용하여 텍스트를 벡터로 변환
def get_embedding(text):
    """OpenAI를 사용하여 텍스트를 벡터로 변환"""
    response = embedding_model.embed_query(text)
    return np.array(response)


# FAISS를 사용하여 유사한 정보 검색
def search_faiss(query, k=3):
    query_vector = get_embedding(query).astype('float32').reshape(1, -1) # 입력 받은 쿼리를 벡터화
    
    # 각 벡터와의 유사도(거리값), FAISS 내부에서 저장된 벡터들의 인덱스 번호(저장 순서)를 반환
    distances, indicies = index.search(query_vector, k) # 인덱스를 사용해서 입력 쿼리와 유사한 정보를 k개 찾음
    
    retrieved_docs = []
    # k개 정보를 하나씩 돌면서 판단
    for idx in indicies[0]:
        if idx != -1:
            cursor = db.cursor(dictionary=True)
            
            # numpy.int64를 Python int로 변환
            idx_int = int(idx)
            
            # 벡터 유사도가 가장 높은 k개의 정보들이 원본 데이터베이스에서는 어디에 있는지 찾아냄
            cursor.execute(
                "SELECT created_at, sender_name, message FROM chat_messages LIMIT 1 OFFSET %s", (idx_int,)
            )
            result = cursor.fetchone()
            cursor.close()
            
            # 원본 데이터베이스에서 정보를 성공적으로 찾아냈다면
            if result:
                doc = f"created_at: {result['created_at']}\nsender_name: {result['sender_name']}\nmessage: {result['message']}"
                retrieved_docs.append(doc)
                
    return retrieved_docs
    

