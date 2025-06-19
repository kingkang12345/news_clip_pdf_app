import os
from typing import Dict, Optional, Any
import logging

class ModelConfig:
    def __init__(self):
        # 고정된 모델 설정 (환경변수는 API 키와 Base URL만)
        self.config = {
            'api_key': os.getenv('api_key', 'your-api-key'),
            'base_url': os.getenv('api_base', 'https://api.openai.com/v1'),
            "pwc_model": {
                "openai_gpt4o": "openai.gpt-4o",  # OpenAI 최신, 최고 품질
                "azure_gpt4o": "azure.gpt-4o",    # Azure용 GPT-4o
                "openai_gpt4_1": "openai.gpt-4.1",  # OpenAI GPT-4.1
                "azure_gpt4_turbo": "azure.gpt-4-turbo-2024-04-09",  # Azure GPT-4 Turbo
                "claude3_5_sonnet": "bedrock.anthropic.claude-3-5-sonnet",  # Anthropic Claude 3.5 Sonnet
                "claude3_5_haiku": "bedrock.anthropic.claude-3-5-haiku",    # Anthropic Claude 3.5 Haiku (빠르고 저렴)
                "gemini_1_5_pro": "vertex_ai.gemini-1.5-pro",  # Google Gemini 1.5 Pro
                "gemini_2_0_flash": "vertex_ai.gemini-2.0-flash",  # Google Gemini 2.0 Flash
                "claude3_7_sonnet": "bedrock.anthropic.claude-3-7-sonnet-v1", # Anthropic Claude 3.7 Sonnet
                "openai_ai": "gpt-4o"
            }
        }
        logging.info("모델 설정 로드 완료 (하드코딩)")
    
    def get_api_key(self) -> str:
        """API 키 반환"""
        return os.getenv('api_key') or self.config.get('api_key', '')
    
    def get_base_url(self) -> str:
        """Base URL 반환"""
        return os.getenv('api_base') or self.config.get('base_url', 'https://api.openai.com/v1')
    
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
            "openai_gpt4o": "OpenAI GPT-4o (최신, 최고 품질, 추천)",
            "azure_gpt4o": "Azure GPT-4o (Azure용, 최고 품질)",
            "openai_gpt4_1": "OpenAI GPT-4.1 (긴 입력, 안정적)",
            "azure_gpt4_turbo": "Azure GPT-4 Turbo (긴 입력, 비용 효율)",
            "claude3_5_sonnet": "Anthropic Claude 3.5 Sonnet (긴 문서 요약 특화)",
            "claude3_5_haiku": "Anthropic Claude 3.5 Haiku (빠르고 저렴)",
            "gemini_1_5_pro": "Google Gemini 1.5 Pro (멀티모달, 긴 문서)",
            "gemini_2_0_flash": "Google Gemini 2.0 Flash (빠른 처리)",
            "claude3_7_sonnet": "Anthropic Claude 3.7 Sonnet (최신, 고성능)",
            "openai_ai": "OpenAI GPT-4o (최신, 최고 품질, 추천)"
        }
        
        return {k: v for k, v in model_descriptions.items() if k in model_mapping}
    
    def get_openai_config(self) -> Dict[str, str]:
        """OpenAI 호환 설정 반환"""
        return {
            'api_key': self.get_api_key(),
            'base_url': self.get_base_url()
        }

    def debug_model_config(self) -> Dict[str, Any]:
        """디버깅용: 모델 설정 상태 확인"""
        model_mapping = self.config.get('pwc_model', {})
        available_models = self.get_available_models()
        
        return {
            'config_loaded': True,
            'total_models_in_config': len(model_mapping),
            'models_in_config': list(model_mapping.keys()),
            'available_models_count': len(available_models),
            'available_models': list(available_models.keys()),
            'azure_env_vars': {
                'api_key': bool(os.getenv('api_key')),
                'api_base': bool(os.getenv('api_base'))
            },
            'current_api_key_set': bool(self.get_api_key()),
            'current_base_url': self.get_base_url()
        }

# 전역 설정 인스턴스
model_config = ModelConfig() 