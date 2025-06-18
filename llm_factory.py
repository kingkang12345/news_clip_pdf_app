from langchain_openai import ChatOpenAI
from model_config import model_config
import logging
from typing import Optional, Dict, Any

class LLMFactory:
    """통합 API를 사용하는 LLM 팩토리"""
    
    @staticmethod
    def create_llm(user_model: str, temperature: float = 0, streaming: bool = False, **kwargs) -> ChatOpenAI:
        """
        사용자 모델명으로 LLM 인스턴스 생성
        통합 API를 사용하므로 모든 모델이 OpenAI 호환 인터페이스로 접근됨
        """
        try:
            # 실제 모델명 매핑
            actual_model = model_config.get_actual_model(user_model)
            
            # OpenAI 호환 설정
            openai_config = model_config.get_openai_config()
            
            # ChatOpenAI 인스턴스 생성 (통합 API 사용)
            llm = ChatOpenAI(
                model=actual_model,
                temperature=temperature,
                streaming=streaming,
                api_key=openai_config['api_key'],
                base_url=openai_config['base_url'],
                **kwargs
            )
            
            logging.info(f"LLM 생성 완료: {user_model} -> {actual_model}")
            return llm
            
        except Exception as e:
            logging.error(f"LLM 생성 실패: {e}")
            # 폴백으로 기본 OpenAI 모델 사용
            return LLMFactory._create_fallback_llm(temperature, streaming, **kwargs)
    
    @staticmethod
    def _create_fallback_llm(temperature: float, streaming: bool, **kwargs) -> ChatOpenAI:
        """폴백 LLM 생성"""
        logging.warning("폴백 모델 사용: azure.gpt-4o")
        
        openai_config = model_config.get_openai_config()
        
        return ChatOpenAI(
            model="azure.gpt-4o",
            temperature=temperature,
            streaming=streaming,
            api_key=openai_config['api_key'],
            base_url=openai_config['base_url'],
            **kwargs
        )
    
    @staticmethod
    def get_model_info(user_model: str) -> Dict[str, str]:
        """모델 정보 반환"""
        actual_model = model_config.get_actual_model(user_model)
        openai_config = model_config.get_openai_config()
        
        return {
            'user_model': user_model,
            'actual_model': actual_model,
            'api_key_preview': f"{openai_config['api_key'][:10]}...",
            'base_url': openai_config['base_url']
        }
    
    @staticmethod
    def test_connection(user_model: str) -> bool:
        """연결 테스트"""
        try:
            llm = LLMFactory.create_llm(user_model, temperature=0)
            # 간단한 테스트 메시지
            response = llm.invoke("Hello, this is a test.")
            logging.info(f"연결 테스트 성공: {user_model}")
            return True
        except Exception as e:
            logging.error(f"연결 테스트 실패: {user_model}, 오류: {e}")
            return False 