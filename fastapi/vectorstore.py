# LangChain 기반 벡터스토어를 활용하여 벡터 검색을 수행하는 코드
# LangChain의 FAISS 벡터스토어를 사용하여 RAG(Retrieval-Augmented Generation) 검색을 구현함
# 사용자 질문을 임베딩하여 가장 관련성 높은 문서를 검색함
# LangChain의 FAISS 구현은 벡터와 함께 문서 내용과 메타데이터를 저장하므로 별도의 데이터베이스 조회가 필요 없음

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import os


# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
print(f"[DEBUG] api key 확인 : {OPENAI_API_KEY}")

# LangChain 임베딩 모델 초기화
embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY,
                                   model="text-embedding-3-small")
print("[DEBUG] embedding_model에 key 잘 들어갔는지 확인", embedding_model)

# LangChain FAISS 벡터스토어 로드
vectorstore = FAISS.load_local("faiss_index_langchain", embedding_model)
print("[DEBUG] 벡터스토어 로드 완료")


# FAISS를 사용하여 유사한 정보 검색
def search_faiss(query, k=3):
    """
    사용자 질문과 관련된 문서를 벡터스토어에서 검색
    
    Args:
        query (str): 사용자 질문
        k (int): 검색할 문서 개수
        
    Returns:
        list: 관련 문서 목록
    """
    # similarity_search_with_score는 (document, score) 형태의 튜플 리스트를 반환
    # similarity_search_with_score 함수가 입력받은 query도 알아서 embedding 해줌
    docs_and_scores = vectorstore.similarity_search_with_score(query, k=k)
   
    retrieved_docs = []
    # k개 정보를 하나씩 돌면서 판단
    for doc, score in docs_and_scores:
        # 점수가 낮을수록 유사도가 높음 (L2 거리 기준)
        print(f"[DEBUG] 문서 점수 : {score}")

        # Document 객체에서 내용 추출
        content = doc.page_content
        metadata = doc.metadata

        # 메타데이터 정보 추가
        retrieval_info = f"{content}\n검색 점수 : {score}"
        retrieved_docs.append(retrieval_info)


    return retrieved_docs