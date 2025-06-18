import logging
import tempfile
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser, SimpleJsonOutputParser
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import PromptTemplate

from llm_factory import LLMFactory
from model_config import model_config

class PDFSummarizer:
    """PDF 문서 요약 클래스"""
    
    def __init__(self, user_model: str = "openai"):
        self.user_model = user_model
        self.llm = LLMFactory.create_llm(user_model, temperature=0)
        self.streaming_llm = LLMFactory.create_llm(user_model, temperature=0, streaming=True)
        
    def summarize_pdf_file(self, pdf_path: str, method: str = "stuff", custom_prompt: str = None) -> Dict[str, Any]:
        """PDF 파일을 요약"""
        try:
            # PDF 로드
            loader = PyMuPDFLoader(pdf_path)
            docs = loader.load()
            
            return self.summarize_documents(docs, method, pdf_path, custom_prompt)
            
        except Exception as e:
            logging.error(f"PDF 파일 요약 실패: {e}")
            raise
    
    def summarize_pdf_content(self, pdf_content: str, method: str = "stuff", filename: str = "document.pdf", custom_prompt: str = None) -> Dict[str, Any]:
        """base64 인코딩된 PDF 내용을 요약"""
        try:
            # 임시 파일로 PDF 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                pdf_data = base64.b64decode(pdf_content)
                tmp_file.write(pdf_data)
                tmp_file_path = tmp_file.name
            
            result = self.summarize_pdf_file(tmp_file_path, method, custom_prompt)
            
            # 임시 파일 삭제
            Path(tmp_file_path).unlink()
            
            return result
            
        except Exception as e:
            logging.error(f"PDF 내용 요약 실패: {e}")
            raise
    
    def summarize_documents(self, docs: List[Document], method: str = "stuff", source: str = "document", custom_prompt: str = None) -> Dict[str, Any]:
        """문서 리스트를 요약"""
        try:
            logging.info(f"요약 시작: {method} 방식, 총 {len(docs)}페이지")
            
            if method == "stuff":
                summary = self._summarize_stuff(docs, custom_prompt)
            elif method == "map_reduce":
                summary = self._summarize_map_reduce(docs, custom_prompt)
            elif method == "map_refine":
                summary = self._summarize_map_refine(docs, custom_prompt)
            elif method == "chain_of_density":
                summary = self._summarize_chain_of_density(docs, custom_prompt)
            else:
                logging.warning(f"알 수 없는 요약 방법: {method}, stuff 방식 사용")
                summary = self._summarize_stuff(docs, custom_prompt)
            
            # 결과 포맷팅
            result = {
                "summary": summary,
                "method": method,
                "user_model": self.user_model,
                "actual_model": model_config.get_actual_model(self.user_model),
                "pages": len(docs),
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
            logging.info(f"요약 완료: {len(summary)} 글자")
            return result
            
        except Exception as e:
            logging.error(f"문서 요약 실패: {e}")
            raise
    
    def _summarize_stuff(self, docs: List[Document], custom_prompt: str = None) -> str:
        """Stuff 방식 요약 - 모든 문서를 한 번에 처리"""
        logging.info("Stuff 방식 요약 시작")
        
        if custom_prompt:
            # 사용자 정의 프롬프트 사용
            prompt_template = custom_prompt
        else:
            # 기본 JSON 구조화 요약 프롬프트
            prompt_template = """다음 PDF 문서를 분석하여 JSON 형식으로 구조화된 요약을 제공해주세요.

문서 내용:
{context}

JSON 형식으로 응답해주세요:
{{
  "document_type": "문서 유형 (예: 뉴스 기사, 보고서, 계약서 등)",
  "main_topic": "주요 주제 한 줄 요약",
  "key_points": [
    {{
      "category": "분야/카테고리",
      "title": "핵심 포인트 제목",
      "summary": "상세 설명",
      "importance": "높음/보통/낮음"
    }}
  ],
  "key_figures": [
    {{
      "type": "수치 유형 (매출, 투자금액, 날짜 등)",
      "value": "구체적 수치",
      "context": "수치 관련 설명"
    }}
  ],
  "timeline": [
    {{
      "date": "YYYY-MM-DD 또는 기간",
      "event": "주요 사건/일정"
    }}
  ],
  "companies_mentioned": ["언급된 회사명들"],
  "conclusion": "전체 문서의 결론 또는 시사점"
}}

중요: 반드시 유효한 JSON 형식으로만 응답하세요."""
        
        prompt = PromptTemplate.from_template(prompt_template)
        stuff_chain = create_stuff_documents_chain(self.llm, prompt)
        
        result = stuff_chain.invoke({"context": docs})
        return result
    
    def _summarize_map_reduce(self, docs: List[Document], custom_prompt: str = None) -> str:
        """Map-Reduce 방식 요약"""
        logging.info("Map-Reduce 방식 요약 시작")
        
        # Map 단계 - 각 문서의 핵심 내용 추출
        map_template = """다음 문서 페이지에서 핵심 정보를 JSON 형식으로 추출해주세요:

{page_content}

JSON 형식으로 응답:
{{
  "key_info": "이 페이지의 가장 중요한 정보",
  "details": ["세부 사항들"],
  "figures": ["언급된 숫자나 날짜"],
  "entities": ["회사명, 인명, 지명 등"]
}}"""
        
        map_prompt = PromptTemplate.from_template(map_template)
        map_chain = map_prompt | self.llm | StrOutputParser()
        
        # 각 문서별로 핵심 내용 추출
        doc_summaries = []
        for doc in docs:
            summary = map_chain.invoke({"page_content": doc.page_content})
            doc_summaries.append(summary)
        
        # Reduce 단계 - 최종 JSON 요약 생성
        reduce_template = """다음은 문서의 각 페이지별 핵심 정보입니다. 이를 종합하여 전체 문서의 구조화된 요약을 JSON 형식으로 작성해주세요.

페이지별 정보:
{doc_summaries}

최종 JSON 형식 요약:
{{
  "document_type": "문서 유형",
  "main_topic": "주요 주제",
  "key_points": [
    {{
      "category": "분야",
      "title": "제목",
      "summary": "요약",
      "importance": "중요도"
    }}
  ],
  "key_figures": [
    {{
      "type": "유형",
      "value": "값",
      "context": "설명"
    }}
  ],
  "timeline": [
    {{
      "date": "날짜",
      "event": "사건"
    }}
  ],
  "companies_mentioned": ["회사들"],
  "conclusion": "결론"
}}"""
        
        reduce_prompt = PromptTemplate.from_template(reduce_template)
        reduce_chain = reduce_prompt | self.llm | StrOutputParser()
        
        final_summary = reduce_chain.invoke({
            "doc_summaries": "\n\n".join(f"페이지 {i+1}: {summary}" for i, summary in enumerate(doc_summaries))
        })
        
        return final_summary
    
    def _summarize_map_refine(self, docs: List[Document], custom_prompt: str = None) -> str:
        """Map-Refine 방식 요약"""
        logging.info("Map-Refine 방식 요약 시작")
        
        # 첫 번째 문서로 초기 요약 생성
        if not docs:
            return "문서가 없습니다."
        
        # 초기 요약 생성
        initial_template = """다음 문서의 첫 번째 페이지를 분석하여 JSON 형식으로 초기 요약을 생성해주세요:

{page_content}

JSON 형식으로 응답:
{{
  "document_type": "문서 유형 추정",
  "main_topic": "주요 주제",
  "key_points": [
    {{
      "category": "분야",
      "title": "제목",
      "summary": "요약",
      "importance": "높음/보통/낮음"
    }}
  ],
  "key_figures": [
    {{
      "type": "유형",
      "value": "값",
      "context": "설명"
    }}
  ],
  "timeline": [
    {{
      "date": "날짜",
      "event": "사건"
    }}
  ],
  "companies_mentioned": ["회사들"],
  "conclusion": "임시 결론"
}}"""
        
        initial_prompt = PromptTemplate.from_template(initial_template)
        initial_chain = initial_prompt | self.llm | StrOutputParser()
        
        current_summary = initial_chain.invoke({"page_content": docs[0].page_content})
        
        # 남은 문서들로 요약을 점진적으로 개선
        refine_template = """기존 요약을 새로운 페이지 정보로 개선해주세요.

기존 요약:
{existing_summary}

새로운 페이지 내용:
{page_content}

기존 요약을 새로운 정보로 보완하여 개선된 JSON 요약을 생성해주세요:
{{
  "document_type": "문서 유형",
  "main_topic": "주요 주제",
  "key_points": [
    {{
      "category": "분야",
      "title": "제목",
      "summary": "요약",
      "importance": "높음/보통/낮음"
    }}
  ],
  "key_figures": [
    {{
      "type": "유형",
      "value": "값",
      "context": "설명"
    }}
  ],
  "timeline": [
    {{
      "date": "날짜",
      "event": "사건"
    }}
  ],
  "companies_mentioned": ["회사들"],
  "conclusion": "전체 결론"
}}

중요: 기존 정보를 유지하면서 새로운 정보를 추가하고 더 정확하게 개선해주세요."""
        
        refine_prompt = PromptTemplate.from_template(refine_template)
        refine_chain = refine_prompt | self.llm | StrOutputParser()
        
        # 남은 문서들로 점진적 개선
        for doc in docs[1:]:
            current_summary = refine_chain.invoke({
                "existing_summary": current_summary,
                "page_content": doc.page_content
            })
        
        return current_summary
    
    def _summarize_chain_of_density(self, docs: List[Document], custom_prompt: str = None) -> str:
        """Chain of Density 방식 요약 - 반복적으로 밀도를 높여가며 요약"""
        logging.info("Chain of Density 방식 요약 시작")
        
        # 전체 문서 내용 결합
        full_content = "\n\n".join([doc.page_content for doc in docs])
        
        # 1단계: 기본 요약 생성
        basic_template = """다음 문서를 분석하여 기본적인 JSON 요약을 생성해주세요:

{content}

JSON 형식으로 응답:
{{
  "document_type": "문서 유형",
  "main_topic": "주요 주제",
  "key_points": [
    {{
      "category": "분야",
      "title": "제목",
      "summary": "요약",
      "importance": "높음/보통/낮음"
    }}
  ],
  "key_figures": [
    {{
      "type": "유형",
      "value": "값",
      "context": "설명"
    }}
  ],
  "timeline": [
    {{
      "date": "날짜",
      "event": "사건"
    }}
  ],
  "companies_mentioned": ["회사들"],
  "conclusion": "기본 결론"
}}"""
        
        basic_prompt = PromptTemplate.from_template(basic_template)
        basic_chain = basic_prompt | self.llm | StrOutputParser()
        
        current_summary = basic_chain.invoke({"content": full_content})
        
        # 2단계: 밀도 높은 요약으로 개선
        dense_template = """기존 요약을 더 밀도 높고 상세하게 개선해주세요.

원본 문서:
{content}

기존 요약:
{existing_summary}

다음 조건으로 개선된 JSON 요약을 생성해주세요:
1. 더 많은 핵심 포인트 추가
2. 수치와 날짜를 더 정확하게 포함
3. 세부사항을 더 풍부하게 설명
4. 결론을 더 구체적으로 작성

개선된 JSON 형식:
{{
  "document_type": "문서 유형",
  "main_topic": "주요 주제",
  "key_points": [
    {{
      "category": "분야",
      "title": "제목",
      "summary": "상세 요약",
      "importance": "높음/보통/낮음"
    }}
  ],
  "key_figures": [
    {{
      "type": "유형",
      "value": "정확한 값",
      "context": "상세 설명"
    }}
  ],
  "timeline": [
    {{
      "date": "정확한 날짜",
      "event": "구체적 사건"
    }}
  ],
  "companies_mentioned": ["모든 관련 회사들"],
  "conclusion": "종합적이고 구체적인 결론"
}}"""
        
        dense_prompt = PromptTemplate.from_template(dense_template)
        dense_chain = dense_prompt | self.llm | StrOutputParser()
        
        # 밀도 높은 요약 생성
        final_summary = dense_chain.invoke({
            "content": full_content,
            "existing_summary": current_summary
        })
        
        return final_summary
    
    def get_model_info(self) -> Dict[str, str]:
        """현재 사용 중인 모델 정보"""
        return LLMFactory.get_model_info(self.user_model) 