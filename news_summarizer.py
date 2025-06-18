"""
뉴스 기사 전용 요약 시스템
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional
from langchain.prompts import PromptTemplate
from filename_parser import FilenameParser

class NewsArticleSummarizer:
    """뉴스 기사 전용 요약 클래스"""
    
    # 뉴스 기사 전용 프롬프트 (파일명에서 메타데이터 추출하므로 단순화)
    NEWS_SUMMARY_PROMPT = PromptTemplate(
        input_variables=["article_text"],
        template="""
다음은 한국 기업 관련 뉴스 기사입니다. 다음 형식으로 요약해주세요:

기사 내용:
{article_text}

요약 형식 (JSON):
{{
  "핵심_요약": "1문장으로 임팩트 있게 요약",
  "주요_내용": "문단 구분 없이 7-10줄 분량으로 요약 (리더십이 빠르게 파악할 수 있도록 구성)"
}}

중요사항:
- 핵심_요약은 한 문장으로 핵심만 임팩트 있게 작성
- 주요_내용은 문단 구분 없이 연속된 한 블록으로 작성 (7-10줄)
- 리더십이 빠르게 파악할 수 있도록 핵심 내용 위주로 구성
- **말투 통일**: 반드시 "~함", "~했음", "~있음", "~중임" 등의 '-음' 체로 일관되게 작성
- 예시와 동일한 말투를 유지하세요 (예: "가능성이 부각되고 있음", "운영 중임")
- JSON 형식을 정확히 지켜주세요
"""
    )
    
    def __init__(self, llm, custom_prompt=None):
        """초기화"""
        self.llm = llm
        self.custom_prompt = custom_prompt
        
    def extract_date_from_text(self, text: str) -> str:
        """텍스트에서 날짜 추출"""
        # 다양한 날짜 패턴 매칭
        date_patterns = [
            r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일',  # 2024년 6월 2일
            r'(\d{4})-(\d{1,2})-(\d{1,2})',           # 2024-06-02
            r'(\d{4})\.(\d{1,2})\.(\d{1,2})',         # 2024.06.02
            r'(\d{1,2})/(\d{1,2})/(\d{4})',           # 06/02/2024
            r'(\d{1,2})월\s*(\d{1,2})일',              # 6월 2일
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    if len(groups[0]) == 4:  # 년이 첫 번째
                        year, month, day = groups
                    else:  # 년이 마지막
                        month, day, year = groups
                    return f"{int(month):02d}/{int(day):02d}"
                elif len(groups) == 2:  # 월/일만
                    month, day = groups
                    return f"{int(month):02d}/{int(day):02d}"
        
        # 날짜를 찾지 못한 경우 오늘 날짜
        today = datetime.now()
        return f"{today.month:02d}/{today.day:02d}"
    
    def summarize_article(self, article_text: str, filename: str = "") -> Dict[str, Any]:
        """뉴스 기사 요약 (파일명에서 메타데이터 추출)"""
        try:
            # 1. 파일명에서 메타데이터 추출
            file_info = FilenameParser.parse_filename(filename)
            
            # 2. LLM으로 요약 생성
            if self.custom_prompt:
                # 사용자 정의 프롬프트 사용
                from langchain.prompts import PromptTemplate
                custom_template = PromptTemplate.from_template(self.custom_prompt)
                chain = custom_template | self.llm
                result = chain.invoke({"article_text": article_text})
            else:
                # 기본 프롬프트 사용
                chain = self.NEWS_SUMMARY_PROMPT | self.llm
                result = chain.invoke({"article_text": article_text})
            
            # 3. JSON 파싱 시도
            import json
            try:
                # JSON 부분만 추출
                json_start = result.content.find('{')
                json_end = result.content.rfind('}') + 1
                json_str = result.content[json_start:json_end]
                llm_summary = json.loads(json_str)
            except:
                # JSON 파싱 실패 시 기본 요약
                llm_summary = {
                    "핵심_요약": "요약 처리 중 오류가 발생했습니다.",
                    "주요_내용": "기사 내용을 처리할 수 없습니다."
                }
            
            # 4. 파일명 정보와 LLM 요약 결합
            final_result = {
                "일자": file_info["일자"],
                "GSP": file_info["GSP"],
                "제목": file_info["제목"],
                "핵심_요약": llm_summary.get("핵심_요약", "요약 없음"),
                "주요_내용": llm_summary.get("주요_내용", "내용 없음"),
                "매체": file_info["매체"],
                "원본_파일": filename,
                "처리_일시": datetime.now().isoformat(),
                "파일명_파싱_성공": file_info["파싱_성공"],
                "상태": "성공"
            }
            
            return final_result
            
        except Exception as e:
            # 오류 시 파일명 파싱이라도 시도
            file_info = FilenameParser.parse_filename(filename)
            return {
                "일자": file_info["일자"],
                "GSP": file_info["GSP"],
                "제목": file_info["제목"],
                "핵심_요약": f"요약 처리 중 오류가 발생했습니다: {str(e)}",
                "주요_내용": "기사 내용을 처리할 수 없습니다.",
                "매체": file_info["매체"],
                "원본_파일": filename,
                "처리_일시": datetime.now().isoformat(),
                "파일명_파싱_성공": file_info["파싱_성공"],
                "상태": "오류"
            }
    
    def _create_fallback_summary(self, text: str, filename: str) -> Dict[str, Any]:
        """LLM 요약 실패 시 기본 요약 생성"""
        # 제목 추출 (첫 번째 줄 또는 파일명 기반)
        lines = text.strip().split('\n')
        title = lines[0] if lines else filename
        if len(title) > 100:
            title = title[:100] + "..."
            
        # 간단한 요약 (앞 200자)
        content_preview = text.replace('\n', ' ')[:200] + "..."
        
        return {
            "일자": self.extract_date_from_text(text),
            "GSP": "기타",  # fallback 시 기타로 분류
            "제목": title,
            "핵심_요약": f"{title}에 관한 기사입니다.",
            "주요_내용": content_preview
        }
    
    def summarize_multiple_articles(self, articles: list) -> list:
        """여러 기사 배치 요약"""
        results = []
        
        for i, article in enumerate(articles):
            article_text = article.get('content', '')
            filename = article.get('name', f'article_{i+1}.pdf')
            
            print(f"처리 중: {filename} ({i+1}/{len(articles)})")
            
            try:
                summary = self.summarize_article(article_text, filename)
                results.append(summary)
            except Exception as e:
                results.append({
                    "일자": "00/00",
                    "GSP": "기타",
                    "제목": f"오류: {filename}",
                    "핵심_요약": f"처리 실패: {str(e)}",
                    "주요_내용": "기사를 처리할 수 없습니다.",
                    "상태": "실패"
                })
        
        return results 