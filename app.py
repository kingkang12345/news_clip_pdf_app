import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="PDF AI 요약",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)
import tempfile
import os
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
import traceback

from pdf_summarizer import PDFSummarizer
from news_summarizer import NewsArticleSummarizer
from html_formatter import HTMLFormatter
from model_config import model_config
from llm_factory import LLMFactory


# 사용자 정의 CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .summary-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #e03a3e;
        margin: 1rem 0;
    }
    .file-info {
        background: #e7f3ff;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .model-info {
        background: #f0f8f0;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """세션 상태 초기화"""
    if 'summaries' not in st.session_state:
        st.session_state.summaries = []
    if 'processing' not in st.session_state:
        st.session_state.processing = False

def get_default_date_range():
    """기본 날짜 범위 계산: 저번주 월요일 ~ 이번주 화요일"""
    today = datetime.now()
    
    # 오늘이 몇 요일인지 계산 (월요일=0, 일요일=6)
    today_weekday = today.weekday()
    
    # 저번주 월요일 계산
    days_since_last_monday = today_weekday + 7  # 저번주 월요일까지의 일수
    last_monday = today - timedelta(days=days_since_last_monday)
    
    # 이번주 화요일 계산 (화요일이 지났어도 이번주 화요일)
    days_to_this_tuesday = 1 - today_weekday  # 이번주 화요일까지의 일수
    this_tuesday = today + timedelta(days=days_to_this_tuesday)
    
    return last_monday.date(), this_tuesday.date()

def display_header():
    """헤더 표시"""
    st.title("📰 뉴스 AI 요약 시스템")
    st.markdown("""
    <div style="background: #fff; color: #222; padding: 1.2rem 1rem 1rem 1rem; border-radius: 10px; margin-bottom: 2rem; border: 1px solid #e0e0e0;">
        <h3 style="margin: 0; color: #222; font-weight: 700; letter-spacing: -1px;">PwC News Intelligence</h3>
        <p style="margin: 0.5rem 0 0 0; color: #444; font-size: 1.05rem;">AI를 통해 뉴스 PDF를 체계적으로 분석하고 요약합니다</p>
    </div>
    """, unsafe_allow_html=True)

def setup_sidebar():
    """사이드바 설정"""
    st.sidebar.title("⚙️ 설정")
    
    # 모델 선택
    available_models = model_config.get_available_models()
    model_names = list(available_models.keys())
    model_descriptions = list(available_models.values())
    
    # 1단계: Single vs Multi 선택
    mode_selection = st.sidebar.selectbox(
        "🤖 AI 모델 모드 선택",
        ["Single", "Multi"],
        format_func=lambda x: {
            "Single": "Single - 단일 모델 선택",
            "Multi": "Multi - 여러 모델 비교"
        }[x],
        index=0
    )
    
    selected_models = []
    
    # 2단계: 모드에 따른 모델 선택
    if mode_selection == "Single":
        # 단일 모델 선택
        selected_model_idx = st.sidebar.selectbox(
            "📋 모델 선택",
            range(len(model_names)),
            format_func=lambda x: f"{model_names[x]}: {model_descriptions[x]}",
            index=0
        )
        selected_models = [model_names[selected_model_idx]]
        
    elif mode_selection == "Multi":
        # 다중 모델 선택
        selected_models = st.sidebar.multiselect(
            "📋 비교할 모델들 선택 (최대 3개 권장)",
            model_names,
            default=model_names[:2] if len(model_names) >= 2 else model_names,
            help="너무 많은 모델을 선택하면 처리 시간이 오래 걸립니다",
            format_func=lambda x: f"{x}: {available_models[x]}"
        )
        
        if len(selected_models) > 4:
            st.sidebar.warning("⚠️ 4개 이상의 모델 선택 시 처리 시간이 매우 오래 걸릴 수 있습니다.")
        
        if not selected_models:
            st.sidebar.error("❌ 최소 1개 이상의 모델을 선택해주세요.")
            selected_models = [model_names[0]]  # 기본값
    
    # 뉴스는 항상 동일한 방식으로 처리
    selected_method = "news_summary"
    
    # 요약 유형은 뉴스 기사로 고정
    summary_type = "뉴스 기사"
    
    # 날짜 범위 설정 섹션
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 보고서 기간 설정")
    
    # 기본 날짜 범위 계산
    default_start, default_end = get_default_date_range()
    
    # 날짜 범위 선택
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "시작일",
            value=default_start,
            help="뉴스 보고서 시작 날짜"
        )
    with col2:
        end_date = st.date_input(
            "종료일",
            value=default_end,
            help="뉴스 보고서 종료 날짜"
        )
    
    # 날짜 검증
    if start_date > end_date:
        st.sidebar.error("❌ 시작일이 종료일보다 늦을 수 없습니다.")
        # 기본값으로 리셋
        start_date, end_date = default_start, default_end
    
    # 날짜 범위 표시
    date_range_str = f"{start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')}"
    st.sidebar.info(f"📋 선택된 기간: {date_range_str}")
    
    # 프롬프트 커스터마이징 섹션
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 프롬프트 설정")
    
    # 뉴스 기사용 기본 프롬프트 (예시 포함)
    default_news_prompt = """다음은 한국 기업 관련 뉴스 기사입니다. 다음 형식으로 요약해주세요:

[요약 예시]
핵심_요약: 삼성전자가 보유 현금을 바탕으로 벳팅에 나서며, 배터리·반도체 등 전략 산업 중심의 M&A 가능성이 주목받고 있음.

주요_내용: 국내 기업들이 비효율 자산을 정리하고 신사업에 투자하는 흐름이 뚜렷해지는 가운데, 삼성전자가 12조 원 이상의 현금을 바탕으로 전략적 투자에 나설 가능성이 부각되고 있음. 삼성전자의 유동성 자산은 여전히 높은 수준이며, 자금 집행은 보수적으로 운영 중임. 그러나 최근 배터리, 반도체 등 전략 산업을 중심으로 M&A 가능성이 다시 주목받고 있음. 코웨이 등 일부 기업이 밸류업을 위해 대규모 투자를 단행한 사례도 참고되고 있음. 시장에서는 삼성전자가 보유 현금을 활용해 기업가치 제고와 주주환원을 동시에 노릴 수 있다는 기대가 커지고 있음. 애플의 자사주 매입 사례처럼, 삼성전자도 유사한 전략을 통해 글로벌 경쟁력을 강화할 수 있을지 관심이 집중되고 있음.

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
- JSON 형식을 정확히 지켜주세요"""
    
    # 프롬프트 편집 여부 선택
    customize_prompt = st.sidebar.checkbox("📝 프롬프트 커스터마이징", value=False)
    
    user_prompt = None
    if customize_prompt:
        user_prompt = st.sidebar.text_area(
            "뉴스 요약 AI 프롬프트 (수정 가능)",
            value=default_news_prompt,
            height=400,
            help="AI가 뉴스를 분석할 때 사용할 프롬프트입니다. 원하는 대로 수정하세요."
        )
        
        # 프롬프트 초기화 버튼
        if st.sidebar.button("🔄 기본값으로 초기화"):
            st.rerun()
    else:
        # 기본 프롬프트 사용
        user_prompt = default_news_prompt
    
    # 모델 정보 표시
    if st.sidebar.button("🔍 모델 정보 확인"):
        for model in selected_models:
            model_info = LLMFactory.get_model_info(model)
            st.sidebar.markdown(f"""
            <div class="model-info">
                <strong>모델:</strong> {model_info['user_model']}<br>
                <strong>실제 모델:</strong> {model_info['actual_model']}<br>
                <strong>API 키:</strong> {model_info['api_key_preview']}<br>
                <strong>Base URL:</strong> {model_info['base_url']}
            </div>
            """, unsafe_allow_html=True)
    
    # 디버깅 정보 표시
    if st.sidebar.button("🐛 모델 설정 디버깅"):
        debug_info = model_config.debug_model_config()
        st.sidebar.json(debug_info)
    
    # 연결 테스트
    if st.sidebar.button("🔗 연결 테스트"):
        with st.sidebar:
            with st.spinner("연결 테스트 중..."):
                for model in selected_models:
                    success = LLMFactory.test_connection(model)
                    if success:
                        st.success(f"✅ {model} 연결 성공!")
                    else:
                        st.error(f"❌ {model} 연결 실패")
    
    return selected_models, selected_method, summary_type, user_prompt, date_range_str

def process_uploaded_files(uploaded_files: List, models: List[str], method: str, summary_type: str, user_prompt: str):
    """업로드된 파일들을 여러 모델로 처리"""
    results = []
    
    # 전체 작업 수 계산 (파일 수 × 모델 수)
    total_tasks = len(uploaded_files) * len(models)
    current_task = 0
    
    # 진행률 표시
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for uploaded_file in uploaded_files:
        try:
            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # PDF 텍스트 추출 (한 번만)
            from langchain_community.document_loaders import PyMuPDFLoader
            loader = PyMuPDFLoader(tmp_file_path)
            docs = loader.load()
            full_text = "\n\n".join([doc.page_content for doc in docs])
            
            file_results = {
                'filename': uploaded_file.name,
                'file_size': len(uploaded_file.getvalue()),
                'pages': len(docs),
                'models': {}
            }
            
            # 각 모델별로 요약 처리
            for model in models:
                current_task += 1
                progress = current_task / total_tasks
                progress_bar.progress(progress)
                status_text.text(f"처리 중: {uploaded_file.name} - {model} ({current_task}/{total_tasks})")
                
                try:
                    # 뉴스 요약 처리
                    summarizer = PDFSummarizer(user_model=model)
                    llm = LLMFactory.create_llm(model)
                    news_summarizer = NewsArticleSummarizer(llm, custom_prompt=user_prompt)
                    
                    # 뉴스 요약
                    model_result = news_summarizer.summarize_article(full_text, uploaded_file.name)
                    model_result['user_model'] = model
                    model_result['actual_model'] = model_config.get_actual_model(model)
                    model_result['method'] = 'news_summary'
                    
                    file_results['models'][model] = model_result
                    
                except Exception as e:
                    st.error(f"❌ {uploaded_file.name} - {model} 처리 중 오류: {str(e)}")
                    file_results['models'][model] = {
                        'error': str(e),
                        'status': 'failed',
                        'user_model': model,
                        'actual_model': model_config.get_actual_model(model)
                    }
            
            results.append(file_results)
            
            # 임시 파일 삭제
            os.unlink(tmp_file_path)
            
        except Exception as e:
            st.error(f"❌ {uploaded_file.name} 파일 처리 중 오류: {str(e)}")
            current_task += len(models)  # 모든 모델 작업 스킵
            file_results = {
                'filename': uploaded_file.name,
                'error': str(e),
                'status': 'failed',
                'models': {}
            }
            results.append(file_results)
    
    # 진행률 바 숨기기
    progress_bar.empty()
    status_text.empty()
    
    return results

def display_summary_result(result: Dict[str, Any], summary_type: str):
    """요약 결과 표시 (Multi 모델 지원)"""
    filename = result.get('filename', 'Unknown')
    
    if result.get('status') == 'failed':
        st.error(f"❌ {filename}: {result.get('error', 'Unknown error')}")
        return
    
    # 기본 파일 정보
    st.markdown(f"""
    <div class="file-info">
        <strong>📄 파일:</strong> {filename}<br>
        <strong>📊 페이지:</strong> {result.get('pages', 'N/A')}페이지<br>
        <strong>📁 파일 크기:</strong> {result.get('file_size', 'N/A'):,} bytes
    </div>
    """, unsafe_allow_html=True)
    
    # 모델별 결과 표시
    if 'models' in result:
        models_data = result['models']
        
        if len(models_data) > 1:
            # Multi 모델 결과 - 탭으로 표시
            st.subheader("🤖 AI 모델별 비교 결과")
            
            # 성공한 모델들만 필터링
            successful_models = {}
            for model, model_data in models_data.items():
                if not (model_data.get('status') == 'failed' or model_data.get('error')):
                    successful_models[model] = model_data
                else:
                    st.error(f"❌ {model}: {model_data.get('error', 'Unknown error')}")
            
            if successful_models:
                tabs = st.tabs([f"🔍 {model}" for model in successful_models.keys()])
                
                for i, (model, model_data) in enumerate(successful_models.items()):
                    with tabs[i]:
                        st.markdown(f"""
                        <div class="model-info">
                            <strong>🤖 모델:</strong> {model_data.get('user_model', 'N/A')} → {model_data.get('actual_model', 'N/A')}<br>
                            <strong>⏰ 처리 시간:</strong> {model_data.get('timestamp', 'N/A')[:19] if model_data.get('timestamp') else 'N/A'}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 뉴스 요약 내용 표시
                        st.markdown(f"""
                        <div class="summary-card">
                            <h4>📰 {model_data.get('제목', 'N/A')}</h4>
                            <p><strong>📅 일자:</strong> {model_data.get('일자', 'N/A')} | 
                               <strong>🏢 GSP:</strong> {model_data.get('GSP', 'N/A')} | 
                               <strong>📺 매체:</strong> {model_data.get('매체', 'N/A')}</p>
                            <h5>🎯 핵심 요약:</h5>
                            <p>{model_data.get('핵심_요약', 'N/A')}</p>
                            <h5>📄 주요 내용:</h5>
                            <p>{model_data.get('주요_내용', 'N/A')}</p>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            # Single 모델 결과
            model = list(models_data.keys())[0]
            model_data = models_data[model]
            
            if model_data.get('status') == 'failed' or model_data.get('error'):
                st.error(f"❌ {model}: {model_data.get('error', 'Unknown error')}")
                return
            
            st.subheader(f"🤖 {model} 요약 결과")
            
            st.markdown(f"""
            <div class="model-info">
                <strong>🤖 모델:</strong> {model_data.get('user_model', 'N/A')} → {model_data.get('actual_model', 'N/A')}<br>
                <strong>⏰ 처리 시간:</strong> {model_data.get('timestamp', 'N/A')[:19] if model_data.get('timestamp') else 'N/A'}
            </div>
            """, unsafe_allow_html=True)
            
            # 뉴스 요약 내용 표시
            st.markdown(f"""
            <div class="summary-card">
                <h4>📰 {model_data.get('제목', 'N/A')}</h4>
                <p><strong>📅 일자:</strong> {model_data.get('일자', 'N/A')} | 
                   <strong>🏢 GSP:</strong> {model_data.get('GSP', 'N/A')} | 
                   <strong>📺 매체:</strong> {model_data.get('매체', 'N/A')}</p>
                <h5>🎯 핵심 요약:</h5>
                <p>{model_data.get('핵심_요약', 'N/A')}</p>
                <h5>📄 주요 내용:</h5>
                <p>{model_data.get('주요_내용', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("모델 결과 데이터가 없습니다.")

def display_html_report(results: List[Dict[str, Any]], date_range: str = None):
    """PWC 스타일 테이블 형식으로 뉴스 요약 리포트 출력 (Multi 모델 비교 지원)"""
    if not results:
        return
    
    # 성공한 결과만 필터링 및 모델 정보 확인
    successful_results = []
    models_used = set()
    
    for r in results:
        if r.get('status') != 'failed' and 'models' in r:
            # 각 파일의 성공한 모델들만 포함
            successful_models = {}
            for model, model_data in r['models'].items():
                if model_data.get('status') != 'failed' and not model_data.get('error'):
                    successful_models[model] = model_data
                    models_used.add(model)
            
            if successful_models:
                r_copy = r.copy()
                r_copy['models'] = successful_models
                successful_results.append(r_copy)
    
    if not successful_results:
        st.warning("성공적으로 처리된 뉴스가 없습니다.")
        return
    
    models_used = sorted(list(models_used))
    is_multi_model = len(models_used) > 1
    
    # PWC 스타일 헤더
    if not date_range:
        date_range = datetime.now().strftime('%Y년 %m월 %d일')
    
    st.markdown(f"""
    <div style="font-family: 'Malgun Gothic', Arial, sans-serif; font-size: 12px; line-height: 1.4; color: #333; margin-bottom: 20px;">
        <p style="margin: 3px 0;">안녕하세요?</p>
        <p style="margin: 3px 0;"></p>
        <p style="margin: 3px 0;">유료 언론사들의 핵심 기사들을 Anchor GSP 고객별로 정리한 News Intelligence를 보내드립니다.</p>
        <p style="margin: 3px 0;"></p>
        <p style="margin: 3px 0;">저작권 때문에 Anchor GRP들께만 공유드리며, 특정 기사의 원문이 필요하신 경우 Market 담당자(정혜원)에게 연락주십시오.</p>
    </div>
    
    <div style="font-style: italic; color: #d2691e; margin: 15px 0; font-size: 11px;">
        <em>Disclaimer: 본 기사는 유료 매체이므로 원문 직접 공유가 불가능하니, 철저히 삼일 내부의 제한된 수신자들에게만 요약문으로 공유됩니다. 외부로의 발송은 삼가 주십시오.</em>
    </div>
    
    <p style="margin: 20px 0 5px 0; font-size: 12px; font-weight: bold;">기간: {date_range}</p>
    
    <div style="font-weight: bold; font-size: 13px; margin: 20px 0 10px 0; color: #333;">
        [News Intelligence]
    </div>
    """, unsafe_allow_html=True)
    
    # Multi 모델 비교 모드 헤더
    if is_multi_model:
        st.markdown(f"""
        <div style="background-color: #e3f2fd; border: 1px solid #1976d2; border-radius: 5px; padding: 10px; margin: 15px 0; text-align: center;">
            <strong style="color: #1976d2;">🤖 AI 모델 비교 분석 결과</strong><br>
            <span style="font-size: 11px; color: #666;">사용된 모델: {', '.join(models_used)}</span>
        </div>
        """, unsafe_allow_html=True)
    
    # 각 뉴스를 테이블 형식으로 출력
    for result in successful_results:
        # 파일명에서 정보 추출
        from filename_parser import FilenameParser
        file_info = FilenameParser.parse_filename(result.get('filename', ''))
        
        if is_multi_model:
            # Multi 모델 비교 - 각 모델별로 별도 테이블
            for model in models_used:
                model_data = result['models'][model]
                table_html = f"""
                <table style="width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 12px;">
                    <tr>
                        <td colspan="3" style="font-weight:bold; background:#f9f9f9; border: 1px solid #ccc; padding: 8px;">
                            {file_info.get('매체', 'N/A')} - 🤖 {model}
                        </td>
                    </tr>
                    <tr>
                        <th style="width:60px; background-color: #f0f0f0; border: 1px solid #ccc; padding: 8px; text-align: center; font-weight: bold;">날짜</th>
                        <th style="width:80px; background-color: #f0f0f0; border: 1px solid #ccc; padding: 8px; text-align: center; font-weight: bold;">GSP</th>
                        <th style="background-color: #f0f0f0; border: 1px solid #ccc; padding: 8px; text-align: center; font-weight: bold;">제목</th>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ccc; padding: 8px; text-align:center;">{file_info.get('일자', 'N/A')}</td>
                        <td style="border: 1px solid #ccc; padding: 8px; text-align:center;">{file_info.get('GSP', 'Anchor GSP')}</td>
                        <td style="border: 1px solid #ccc; padding: 8px;">{model_data.get('제목', file_info.get('제목', 'N/A'))}</td>
                    </tr>
                    <tr>
                        <td style="font-weight:bold; background:#f9f9f9; border: 1px solid #ccc; padding: 8px; width: 100px; white-space: nowrap;">핵심 요약</td>
                        <td colspan="2" style="border: 1px solid #ccc; padding: 8px; padding-left:10px;">{model_data.get('핵심_요약', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="font-weight:bold; background:#f9f9f9; border: 1px solid #ccc; padding: 8px; width: 100px; white-space: nowrap;">상세 내용</td>
                        <td colspan="2" style="border: 1px solid #ccc; padding: 8px; padding-left:10px;">{model_data.get('주요_내용', 'N/A')}</td>
                    </tr>
                </table>
                """
                st.markdown(table_html, unsafe_allow_html=True)
            
            # 모든 모델 테이블 출력 후 구분선
            st.markdown('<div style="height:18px;"></div>', unsafe_allow_html=True)
            
        else:
            # 단일 모델 기존 테이블 형식
            model = models_used[0]
            model_data = result['models'][model]
            
            table_html = f"""
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 12px;">
                <tr>
                    <td colspan="3" style="font-weight:bold; background:#f9f9f9; border: 1px solid #ccc; padding: 8px;">
                        {file_info.get('매체', 'N/A')}
                    </td>
                </tr>
                <tr>
                    <th style="width:60px; background-color: #f0f0f0; border: 1px solid #ccc; padding: 8px; text-align: center; font-weight: bold;">날짜</th>
                    <th style="width:80px; background-color: #f0f0f0; border: 1px solid #ccc; padding: 8px; text-align: center; font-weight: bold;">GSP</th>
                    <th style="background-color: #f0f0f0; border: 1px solid #ccc; padding: 8px; text-align: center; font-weight: bold;">제목</th>
                </tr>
                <tr>
                    <td style="border: 1px solid #ccc; padding: 8px; text-align:center;">{file_info.get('일자', 'N/A')}</td>
                    <td style="border: 1px solid #ccc; padding: 8px; text-align:center;">{file_info.get('GSP', 'Anchor GSP')}</td>
                    <td style="border: 1px solid #ccc; padding: 8px;">{model_data.get('제목', file_info.get('제목', 'N/A'))}</td>
                </tr>
                <tr>
                    <td style="font-weight:bold; background:#f9f9f9; border: 1px solid #ccc; padding: 8px; width: 100px; white-space: nowrap;">핵심 요약</td>
                    <td colspan="2" style="border: 1px solid #ccc; padding: 8px; padding-left:10px;">{model_data.get('핵심_요약', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight:bold; background:#f9f9f9; border: 1px solid #ccc; padding: 8px; width: 100px; white-space: nowrap;">상세 내용</td>
                    <td colspan="2" style="border: 1px solid #ccc; padding: 8px; padding-left:10px;">{model_data.get('주요_내용', 'N/A')}</td>
                </tr>
            </table>
            <div style="height:18px;"></div>
            """
                
            st.markdown(table_html, unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-style: italic; color: #d2691e; margin: 15px 0; font-size: 11px;">
        <em>Disclaimer: 본 기사는 유료 매체이므로 원문 직접 공유가 불가능하니, 철저히 삼일 내부의 제한된 수신자들에게만 요약문으로 공유됩니다. 외부로의 발송은 삼가 주십시오.</em>
    </div>
    <p></p>
    <div class="footer-note" style="color: #888; font-size: 13px; margin-top: 10px;">
        ※ 본 Weekly intelligence는 주요 뉴스를 AI로 요약한 내용입니다. 일부 정확하지 못한 내용이 있는 경우, Market으로 말씀주시면 수정하도록 하겠습니다.
    </div>
    """, unsafe_allow_html=True)      
            
    
    # HTML 다운로드를 위한 전체 콘텐츠 생성
    download_html = generate_download_html(successful_results, models_used, is_multi_model, date_range)
    
    # HTML 다운로드 버튼
    st.download_button(
        label="📥 HTML 리포트 다운로드",
        data=download_html,
        file_name=f"news_intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        mime="text/html",
        help="PWC 스타일 리포트를 HTML 파일로 다운로드합니다"
    )

def generate_download_html(results: List[Dict[str, Any]], models_used: List[str], is_multi_model: bool, date_range: str = None) -> str:
    """PWC 스타일 다운로드용 HTML 생성 (Multi 모델 비교 지원)"""
    if not date_range:
        date_range = datetime.now().strftime('%Y년 %m월 %d일')
    period = date_range
    
    # 테이블 HTML 생성
    table_content = ""
    
    # Multi 모델 비교 헤더
    if is_multi_model:
        table_content += f"""
        <div style="background-color: #e3f2fd; border: 1px solid #1976d2; border-radius: 5px; padding: 10px; margin: 15px 0; text-align: center;">
            <strong style="color: #1976d2;">🤖 AI 모델 비교 분석 결과</strong><br>
            <span style="font-size: 11px; color: #666;">사용된 모델: {', '.join(models_used)}</span>
        </div>
        """
    
    for result in results:
        # 파일명에서 정보 추출
        from filename_parser import FilenameParser
        file_info = FilenameParser.parse_filename(result.get('filename', ''))
        
        if is_multi_model:
            # Multi 모델 비교 - 각 모델별로 별도 테이블
            for model in models_used:
                model_data = result['models'][model]
                table_content += f"""
    <table>
        <tr>
            <td colspan="3" style="font-weight:bold; background:#f9f9f9;">{file_info.get('매체', 'N/A')} - 🤖 {model}</td>
        </tr>
        <tr>
            <th style="width:60px;">날짜</th>
            <th style="width:80px;">GSP</th>
            <th>제목</th>
        </tr>
        <tr>
            <td style="text-align:center;">{file_info.get('일자', 'N/A')}</td>
            <td style="text-align:center;">{file_info.get('GSP', 'Anchor GSP')}</td>
            <td>{model_data.get('제목', file_info.get('제목', 'N/A'))}</td>
        </tr>
        <tr>
            <td style="font-weight:bold; background:#f9f9f9; width: 100px; white-space: nowrap;">핵심 요약</td>
            <td colspan="2" style="padding-left:10px;">{model_data.get('핵심_요약', 'N/A')}</td>
        </tr>
        <tr>
            <td style="font-weight:bold; background:#f9f9f9; width: 100px; white-space: nowrap;">상세 내용</td>
            <td colspan="2" style="padding-left:10px;">{model_data.get('주요_내용', 'N/A')}</td>
        </tr>
    </table>
    <div style="height:18px;"></div>
                """
        else:
            # 단일 모델 기존 테이블 형식
            model = models_used[0]
            model_data = result['models'][model]
            
            table_content += f"""
    <table>
        <tr>
            <td colspan="3" style="font-weight:bold; background:#f9f9f9;">{file_info.get('매체', 'N/A')}</td>
        </tr>
        <tr>
            <th style="width:60px;">날짜</th>
            <th style="width:80px;">GSP</th>
            <th>제목</th>
        </tr>
        <tr>
            <td style="text-align:center;">{file_info.get('일자', 'N/A')}</td>
            <td style="text-align:center;">{file_info.get('GSP', 'Anchor GSP')}</td>
            <td>{model_data.get('제목', file_info.get('제목', 'N/A'))}</td>
        </tr>
        <tr>
            <td style="font-weight:bold; background:#f9f9f9; width: 100px; white-space: nowrap;">핵심 요약</td>
            <td colspan="2" style="padding-left:10px;">{model_data.get('핵심_요약', 'N/A')}</td>
        </tr>
        <tr>
            <td style="font-weight:bold; background:#f9f9f9; width: 100px; white-space: nowrap;">상세 내용</td>
            <td colspan="2" style="padding-left:10px;">{model_data.get('주요_내용', 'N/A')}</td>
        </tr>
    </table>
    <div style="height:18px;"></div>
            """
    
    # PWC 스타일 HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PwC News Intelligence</title>
    <style>
        body {{
            font-family: 'Malgun Gothic', Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #ffffff;
        }}
        .header {{
            margin-bottom: 20px;
        }}
        .header p {{
            margin: 3px 0;
            font-size: 12px;
        }}
        .disclaimer {{
            font-style: italic;
            color: #d2691e;
            margin: 15px 0;
            font-size: 11px;
        }}
        .section-title {{
            font-weight: bold;
            font-size: 13px;
            margin: 20px 0 10px 0;
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 12px;
        }}
        th {{
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            padding: 8px;
            text-align: center;
            font-weight: bold;
        }}
        td {{
            border: 1px solid #ccc;
            padding: 8px;
        }}
        .detail-section {{
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <p>안녕하세요?</p>
        <p></p>
        <p>유료 언론사들의 핵심 기사들을 Anchor GSP 고객별로 정리한 News Intelligence를 보내드립니다.</p>
        <p></p>
        <p>저작권 때문에 Anchor GRP들께만 공유드리며, 특정 기사의 원문이 필요하신 경우 Market 담당자(정혜원)에게 연락주십시오.</p>
    </div>
    
    <div class="disclaimer">
        <em>Disclaimer: 본 기사는 유료 매체이므로 원문 직접 공유가 불가능하니, 철저히 삼일 내부의 제한된 수신자들에게만 요약문으로 공유됩니다. 외부로의 발송은 삼가 주십시오.</em>
    </div>
    
    <p style="margin: 20px 0 5px 0; font-size: 12px; font-weight: bold;">기간: {period}</p>
    
    <div class="section-title">[News Intelligence]</div>
    
    {table_content}
    <p></p>
    <div class="disclaimer">
        <em>Disclaimer: 본 기사는 유료 매체이므로 원문 직접 공유가 불가능하니, 철저히 삼일 내부의 제한된 수신자들에게만 요약문으로 공유됩니다. 외부로의 발송은 삼가 주십시오.</em>
    </div>
    <div class="footer-note" style="color: #888; font-size: 13px; margin-top: 10px;">
        ※ 본 Weekly intelligence는 AI를 통해 주요 뉴스만 수집한 내용입니다. 일부 정확하지 못한 내용이 있는 경우, Market으로 말씀주시면 수정하도록 하겠습니다.
    </div>
</body>
</html>"""
    
    return html_content

def main():
    """메인 함수"""
    init_session_state()
    display_header()
    
    # 사이드바 설정
    selected_models, selected_method, summary_type, user_prompt, date_range_str = setup_sidebar()
    
    # 메인 컨텐츠
    st.header("📁 뉴스 PDF 파일 업로드")
    
    # 선택된 모델 정보 표시
    if len(selected_models) > 1:
        st.info(f"🤖 선택된 모델: {', '.join(selected_models)} (총 {len(selected_models)}개)")
        st.warning(f"⚠️ 여러 모델 비교 모드: 처리 시간이 약 {len(selected_models)}배 소요됩니다.")
    else:
        st.info(f"🤖 선택된 모델: {selected_models[0]}")
    
    uploaded_files = st.file_uploader(
        "뉴스 PDF 파일을 선택하세요 (여러 파일 동시 업로드 가능)",
        type="pdf",
        accept_multiple_files=True,
        help="최대 10개까지 동시 뉴스 PDF 업로드 가능합니다"
    )
    
    if uploaded_files:
        # 파일 정보 표시
        st.info(f"📋 {len(uploaded_files)}개 파일이 선택되었습니다")
        
        with st.expander("📄 선택된 파일 목록", expanded=True):
            for file in uploaded_files:
                st.write(f"- {file.name} ({file.size:,} bytes)")
        
        # 예상 처리 시간 표시
        estimated_time = len(uploaded_files) * len(selected_models) * 30  # 파일당 모델당 약 30초 추정
        if estimated_time > 60:
            st.info(f"⏱️ 예상 처리 시간: 약 {estimated_time // 60}분 {estimated_time % 60}초")
        
        # 요약 실행 버튼
        if st.button("🚀 요약 시작", type="primary", disabled=st.session_state.processing):
            if len(uploaded_files) > 10:
                st.error("❌ 최대 10개 파일까지만 업로드할 수 있습니다.")
            elif len(selected_models) == 0:
                st.error("❌ 최소 1개 이상의 모델을 선택해주세요.")
            else:
                st.session_state.processing = True
                
                with st.spinner("AI가 뉴스를 분석하고 있습니다... ⏳"):
                    try:
                        results = process_uploaded_files(uploaded_files, selected_models, selected_method, summary_type, user_prompt)
                        st.session_state.summaries = results
                        st.session_state.selected_models = selected_models  # 모델 정보 저장
                        st.success("✅ 요약이 완료되었습니다!")
                    except Exception as e:
                        st.error(f"❌ 요약 중 오류가 발생했습니다: {str(e)}")
                        st.error("상세 오류 정보:")
                        st.code(traceback.format_exc())
                    finally:
                        st.session_state.processing = False
    
    # 결과 표시
    if st.session_state.summaries:
        st.header("📋 뉴스 요약 결과")
        
        # 성공/실패 통계
        success_count = len([r for r in st.session_state.summaries if r.get('status') != 'failed'])
        total_count = len(st.session_state.summaries)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("전체 파일", total_count)
        with col2:
            st.metric("성공", success_count, delta=f"{success_count}/{total_count}")
        with col3:
            st.metric("실패", total_count - success_count, delta=f"{total_count - success_count}/{total_count}")
        
        # 개별 결과 표시
        for i, result in enumerate(st.session_state.summaries):
            with st.expander(f"📄 {result.get('filename', f'File {i+1}')} 요약 결과", expanded=True):
                display_summary_result(result, "뉴스 기사")
        
        # HTML 결과 출력
        st.header("📄 통합 뉴스 요약 리포트")
        display_html_report(st.session_state.summaries, date_range_str)
        
        # 결과 초기화 버튼
        if st.button("🗑️ 결과 초기화"):
            st.session_state.summaries = []
            st.rerun()

if __name__ == "__main__":
    main() 