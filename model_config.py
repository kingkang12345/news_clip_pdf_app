import yaml
import os
from typing import Dict, Optional
import logging
from pathlib import Path

class ModelConfig:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(__file__).parent / config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """config.yaml에서 설정 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logging.info("설정 파일 로드 완료")
            return config
        except Exception as e:
            logging.error(f"설정 파일 로드 실패: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """기본 설정"""
        return {
            'api_key': 'your-api-key',
            'base_url': 'https://api.example.com/v1',
            'pwc_model': {
                'openai': 'azure.gpt-4o',
                'claude': 'bedrock.anthropic.claude3-sonnet',
                'google': 'vertex_ai.gemini-1.5-pro'
            }
        }
    
    def get_api_key(self) -> str:
        """통합 API 키 반환"""
        return self.config.get('api_key', '')
    
    def get_base_url(self) -> str:
        """Base URL 반환 (환경변수에서 우선 확인)"""
        # api_base 또는 base_url 키 모두 지원
        base_url = self.config.get('api_base') or self.config.get('base_url')
        return os.getenv('BASE_URL', base_url or 'https://api.openai.com/v1')
    
    def get_actual_model(self, user_model: str) -> str:
        """사용자 모델명을 실제 모델명으로 변환"""
        model_mapping = self.config.get('pwc_model', {})
        actual_model = model_mapping.get(user_model, user_model)
        logging.info(f"모델 매핑: {user_model} -> {actual_model}")
        return actual_model
    
    def get_available_models(self) -> Dict[str, str]:
        """사용 가능한 모델 목록 반환"""
        model_mapping = self.config.get('pwc_model', {})
        
        model_descriptions = {
            "openai": "OpenAI GPT-4o (추천)",
            "claude3_5": "Anthropic Claude 3.5 Sonnet",
            "google": "Google Gemini 1.5 Pro",
            "openai_o1": "OpenAI o1 (고급 추론)",
            "openai_o1-mini": "OpenAI o1-mini (빠른 추론)",
            "claude3_5_v2": "Claude 3.5 Sonnet v2",
            "openai_o3_mini": "OpenAI o3-mini (최신)",
            "gemini_2.0_flash": "Gemini 2.0 Flash",
            "claude3_7": "Claude 3.7 Sonnet"
        }
        
        return {k: v for k, v in model_descriptions.items() if k in model_mapping}
    
    def get_openai_config(self) -> Dict[str, str]:
        """OpenAI 호환 설정 반환"""
        return {
            'api_key': self.get_api_key(),
            'base_url': self.get_base_url()
        }

# 전역 설정 인스턴스
model_config = ModelConfig() 