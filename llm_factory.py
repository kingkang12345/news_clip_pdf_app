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
            
            # 디버깅: 전달된 kwargs 확인
            if kwargs:
                logging.info(f"create_llm에 전달된 kwargs: {kwargs}")
            
            # ChatOpenAI에서 지원하지 않는 인자들 완전히 제거
            # 지원되는 인자만 명시적으로 허용
            allowed_args = {
                'timeout', 'max_retries', 'default_headers', 'default_query',
                'http_client', 'request_timeout', 'max_tokens', 'top_p',
                'frequency_penalty', 'presence_penalty', 'logit_bias',
                'user', 'response_format', 'seed', 'tools', 'tool_choice',
                'parallel_tool_calls', 'stop', 'stream_options'
            }
            
            supported_kwargs = {}
            for key, value in kwargs.items():
                if key in allowed_args:
                    supported_kwargs[key] = value
                else:
                    logging.warning(f"지원하지 않는 인자 제거됨: {key}={value}")
            
            # ChatOpenAI 인스턴스 생성 (통합 API 사용) - kwargs 없이 안전하게
            llm = ChatOpenAI(
                model=actual_model,
                temperature=temperature,
                streaming=streaming,
                api_key=openai_config['api_key'],
                base_url=openai_config['base_url']
                # kwargs는 의도적으로 제거 - proxies 에러 방지
            )
            
            logging.info(f"LLM 생성 완료: {user_model} -> {actual_model}")
            return llm
            
        except Exception as e:
            logging.error(f"LLM 생성 실패: {e}")
            # 폴백으로 기본 OpenAI 모델 사용 (kwargs 없이)
            return LLMFactory._create_fallback_llm(temperature, streaming)
    
    @staticmethod
    def _create_fallback_llm(temperature: float, streaming: bool) -> ChatOpenAI:
        """폴백 LLM 생성 - kwargs 없이 안전하게"""
        logging.warning("폴백 모델 사용: gpt-4o-mini")
        
        openai_config = model_config.get_openai_config()
        
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
            streaming=streaming,
            api_key=openai_config['api_key'],
            base_url=openai_config['base_url']
            # kwargs 완전히 제거 - proxies 에러 방지
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