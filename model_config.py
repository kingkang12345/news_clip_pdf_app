import os
from typing import Dict, Optional, Any
import logging

class ModelConfig:
    def __init__(self):
        # 고정된 모델 설정 (환경변수는 API 키와 Base URL만)
        self.config = {
            'api_key': os.getenv('api_key', 'your-api-key'),
            'base_url': os.getenv('api_base', 'https://api.openai.com/v1'),
            'pwc_model': {
                "openai": "azure.gpt-4o",
                "claude": "bedrock.anthropic.claude3-sonnet",
                "claude3_5": "bedrock.anthropic.claude-3-5-sonnet",
                "google": "vertex_ai.gemini-1.5-pro",
                "openai_o1": "openai.o1-2024-12-17",
                "openai_o1-mini": "azure.o1-mini",
                "claude3_5_v2": "bedrock.anthropic.claude-3-5-sonnet-v2",
                "openai_o3_mini": "openai.o3-mini-2025-01-31",
                "gemini_2.0_flash": "vertex_ai.gemini-2.0-flash",
                "claude3_7": "bedrock.anthropic.claude-3-7-sonnet-v1",
                "openai_ai": "gpt-4o-mini"
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
            "openai": "OpenAI GPT-4o (추천)",
            "claude": "Anthropic Claude 3 Sonnet",
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