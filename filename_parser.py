"""
PDF 파일명 파싱 시스템
파일명 형식: 매체_MMDD_GSP_기사제목.pdf
"""

import re
from typing import Dict, Optional
from pathlib import Path

class FilenameParser:
    """PDF 파일명 파싱 클래스"""
    
    @classmethod
    def parse_filename(cls, filename: str) -> Dict[str, str]:
        """
        파일명에서 뉴스 정보 추출
        
        Args:
            filename: PDF 파일명 (예: 더벨_0602_현대차_현대건설SMR상상은현실이된다.pdf)
            
        Returns:
            dict: 파싱된 정보
        """
        # 파일 확장자 제거
        name_without_ext = Path(filename).stem
        
        # 언더스코어로 분할
        parts = name_without_ext.split('_')
        
        result = {
            "매체": "",
            "일자": "",
            "GSP": "",
            "제목": "",
            "원본_파일명": filename,
            "파싱_성공": False
        }
        
        try:
            if len(parts) >= 4:
                result["매체"] = parts[0]
                result["일자"] = cls._format_date(parts[1])
                result["GSP"] = parts[2]
                result["제목"] = '_'.join(parts[3:])  # 나머지 부분을 제목으로
                result["파싱_성공"] = True
            else:
                # 파싱 실패 시 기본값
                result["제목"] = name_without_ext
                result["일자"] = cls._get_today_mmdd()
                result["GSP"] = "기타"
                
        except Exception as e:
            # 오류 시 기본값
            result["제목"] = name_without_ext
            result["일자"] = cls._get_today_mmdd()
            result["GSP"] = "기타"
            result["오류"] = str(e)
        
        return result
    
    @classmethod
    def _format_date(cls, date_str: str) -> str:
        """
        날짜 문자열을 MM/DD 형식으로 변환
        
        Args:
            date_str: MMDD 형식 문자열 (예: "0602")
            
        Returns:
            str: MM/DD 형식 (예: "06/02")
        """
        try:
            if len(date_str) == 4 and date_str.isdigit():
                month = date_str[:2]
                day = date_str[2:]
                return f"{month}/{day}"
            else:
                return cls._get_today_mmdd()
        except:
            return cls._get_today_mmdd()
    
    @classmethod
    def _get_today_mmdd(cls) -> str:
        """오늘 날짜를 MM/DD 형식으로 반환"""
        from datetime import datetime
        today = datetime.now()
        return f"{today.month:02d}/{today.day:02d}"
    
    @classmethod
    def validate_gsp(cls, gsp: str) -> str:
        """GSP가 유효한지 확인하고 정규화"""
        valid_groups = ["삼성", "현대차", "SK", "LG", "한화", "롯데", "포스코"]
        
        # 대소문자 무관하게 매칭
        gsp_upper = gsp.upper()
        for group in valid_groups:
            if group.upper() == gsp_upper or group in gsp:
                return group
        
        return "기타"
    
    @classmethod
    def parse_multiple_files(cls, filenames: list) -> list:
        """여러 파일명 배치 파싱"""
        results = []
        
        for filename in filenames:
            parsed = cls.parse_filename(filename)
            results.append(parsed)
        
        return results

# 테스트 함수
def test_filename_parser():
    """파일명 파싱 테스트"""
    test_files = [
        "더벨_0602_현대차_현대건설SMR상상은현실이된다.pdf",
        "조선일보_1215_삼성_삼성전자3분기실적발표.pdf", 
        "한경_0303_SK_SK하이닉스신공장착공.pdf",
        "잘못된파일명.pdf"
    ]
    
    for filename in test_files:
        result = FilenameParser.parse_filename(filename)
        print(f"\n파일명: {filename}")
        print(f"매체: {result['매체']}")
        print(f"일자: {result['일자']}")
        print(f"GSP: {result['GSP']}")
        print(f"제목: {result['제목']}")
        print(f"파싱 성공: {result['파싱_성공']}")

if __name__ == "__main__":
    test_filename_parser() 