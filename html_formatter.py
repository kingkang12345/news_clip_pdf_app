from datetime import datetime
from typing import Dict, Any
import json
import re

class HTMLFormatter:
    """요약 결과를 PWC 스타일 HTML로 포맷팅하는 클래스"""
    
    @staticmethod
    def format_summary_to_html(result: Dict[str, Any], pdf_name: str = "document.pdf") -> str:
        """요약 결과를 PWC 스타일 HTML로 포맷팅"""
        
        summary = result.get("summary", "요약 없음")
        method = result.get("method", "unknown")
        user_model = result.get("user_model", "unknown")
        actual_model = result.get("actual_model", "unknown")
        pages = result.get("pages", 0)
        timestamp = result.get("timestamp", datetime.now().isoformat())
        
        # JSON 파싱 시도
        parsed_data = HTMLFormatter._parse_json_summary(summary)
        
        # 날짜 포맷팅
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_date = dt.strftime("%Y년 %m월 %d일")
            formatted_time = dt.strftime("%H:%M:%S")
        except:
            formatted_date = datetime.now().strftime("%Y년 %m월 %d일")
            formatted_time = datetime.now().strftime("%H:%M:%S")
        
        # 방법별 설명
        method_descriptions = {
            "stuff": "전체 문서 통합 분석",
            "map_reduce": "페이지별 분석 후 통합",
            "map_refine": "점진적 정밀 분석",
            "chain_of_density": "고밀도 반복 분석"
        }
        
        method_desc = method_descriptions.get(method, method)
        
        # PWC 스타일 HTML 생성
        if parsed_data:
            content_html = HTMLFormatter._create_structured_content(parsed_data, pdf_name, pages, method_desc, user_model, actual_model)
        else:
            content_html = HTMLFormatter._create_fallback_content(summary, pdf_name, pages, method_desc, user_model, actual_model)
        
        html_template = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PwC Document Intelligence</title>
    <style>
        body {{
            background: #f6f6f6;
            padding: 40px 0;
            font-family: '맑은 고딕', Arial, sans-serif;
            margin: 0;
        }}
        .container {{
            background: #fff;
            max-width: 800px;
            margin: auto;
            border-radius: 8px;
            box-shadow: 0 1px 6px rgba(0,0,0,0.06);
            padding: 36px 40px;
        }}
        .header {{
            border-left: 6px solid #e03a3e;
            padding-left: 16px;
            margin-bottom: 24px;
        }}
        .header-title {{
            font-size: 22px;
            color: #e03a3e;
            font-weight: bold;
            letter-spacing: 0.5px;
        }}
        .header-subtitle {{
            font-size: 15px;
            color: #555;
            margin-top: 10px;
        }}
        .section-title {{
            border-bottom: 2px solid #e03a3e;
            margin-bottom: 18px;
            padding-bottom: 4px;
            font-size: 16px;
            font-weight: 600;
            color: #333;
            letter-spacing: 0.3px;
        }}
        .document-info {{
            background: #f8f9fa;
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 20px;
            border: 1px solid #e9ecef;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
        }}
        .info-item {{
            font-size: 14px;
        }}
        .info-label {{
            color: #666;
            font-weight: 500;
        }}
        .info-value {{
            color: #333;
            font-weight: 600;
            margin-left: 8px;
        }}
        .content-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }}
        .content-table th {{
            background: #004578;
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            border: 1px solid #ddd;
        }}
        .content-table td {{
            padding: 12px 8px;
            border: 1px solid #ddd;
            vertical-align: top;
            line-height: 1.5;
        }}
        .content-table tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        .category-badge {{
            display: inline-block;
            background: #e03a3e;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 8px;
        }}
        .importance-high {{
            background: #dc3545;
        }}
        .importance-medium {{
            background: #ffc107;
            color: #000;
        }}
        .importance-low {{
            background: #6c757d;
        }}
        .timeline-item {{
            margin-bottom: 8px;
            padding-left: 16px;
            border-left: 2px solid #e03a3e;
        }}
        .footer {{
            margin-top: 32px;
            padding-top: 16px;
            border-top: 1px solid #eee;
            font-size: 14px;
            color: #666;
        }}
        .pwc-logo {{
            margin-top: 32px;
            text-align: right;
        }}
        .pwc-logo div {{
            font-size: 18px;
            color: #e03a3e;
            font-weight: bold;
        }}
        .companies-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .company-tag {{
            background: #004578;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-title">PwC Document Intelligence</div>
            <div class="header-subtitle">
                안녕하세요. <b>Document Intelligence</b> 분석 결과를 전달드립니다.<br>
                AI를 통해 문서의 핵심 내용을 체계적으로 분석하였습니다.
            </div>
        </div>
        
        <div class="section-title">[Document Intelligence] {formatted_date}</div>
        
        <div class="document-info">
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">📄 문서명:</span>
                    <span class="info-value">{pdf_name}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">📊 페이지:</span>
                    <span class="info-value">{pages}페이지</span>
                </div>
                <div class="info-item">
                    <span class="info-label">🤖 분석 모델:</span>
                    <span class="info-value">{user_model}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">📋 분석 방식:</span>
                    <span class="info-value">{method_desc}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">⏰ 분석 시간:</span>
                    <span class="info-value">{formatted_time}</span>
                </div>
            </div>
        </div>
        
        {content_html}
        
        <div class="footer">
            <div style="font-weight: bold; color: #e03a3e;">Client & Market 드림</div>
            <div style="margin-top: 12px; font-size: 13px; color: #888;">
                ※ 본 Document Intelligence는 AI를 통해 주요 내용만 추출한 결과입니다. 
                일부 정확하지 못한 내용이 있는 경우, 담당자에게 말씀주시면 수정하도록 하겠습니다.
            </div>
            <div style="margin-top: 8px; font-size: 12px; color: #aaa;">
                실제 처리 모델: {actual_model} | 분석 ID: {timestamp.split('T')[0]}-{hash(pdf_name) % 10000:04d}
            </div>
        </div>
        
        <div class="pwc-logo">
            <div>PwC</div>
        </div>
    </div>
</body>
</html>"""
        
        return html_template
    
    @staticmethod
    def _parse_json_summary(summary: str) -> Dict[str, Any]:
        """JSON 요약 파싱"""
        try:
            # JSON 부분만 추출 시도
            json_match = re.search(r'\{.*\}', summary, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            return None
        except (json.JSONDecodeError, AttributeError):
            return None
    
    @staticmethod
    def _create_structured_content(data: Dict[str, Any], pdf_name: str, pages: int, method: str, user_model: str, actual_model: str) -> str:
        """구조화된 JSON 데이터로 HTML 생성"""
        
        content_html = f"""
        <div style="margin-top: 20px;">
            <div style="font-size: 15px; font-weight: bold; color: #004578; margin-bottom: 12px;">
                📋 문서 개요
            </div>
            <div style="background: #f8f9fa; padding: 16px; border-radius: 6px; border-left: 4px solid #e03a3e;">
                <div style="margin-bottom: 8px;">
                    <strong>문서 유형:</strong> {data.get('document_type', 'N/A')}
                </div>
                <div style="margin-bottom: 8px;">
                    <strong>주요 주제:</strong> {data.get('main_topic', 'N/A')}
                </div>
                <div>
                    <strong>결론:</strong> {data.get('conclusion', 'N/A')}
                </div>
            </div>
        </div>"""
        
        # 핵심 포인트 테이블
        key_points = data.get('key_points', [])
        if key_points:
            content_html += """
        <div style="margin-top: 24px;">
            <div style="font-size: 15px; font-weight: bold; color: #004578; margin-bottom: 12px;">
                🎯 핵심 포인트
            </div>
            <table class="content-table">
                <thead>
                    <tr>
                        <th style="width: 15%;">분야</th>
                        <th style="width: 25%;">제목</th>
                        <th style="width: 50%;">요약</th>
                        <th style="width: 10%;">중요도</th>
                    </tr>
                </thead>
                <tbody>"""
            
            for point in key_points:
                importance = point.get('importance', '보통')
                importance_class = {
                    '높음': 'importance-high',
                    '보통': 'importance-medium', 
                    '낮음': 'importance-low'
                }.get(importance, 'importance-medium')
                
                content_html += f"""
                    <tr>
                        <td><span class="category-badge">{point.get('category', 'N/A')}</span></td>
                        <td style="font-weight: 600;">{point.get('title', 'N/A')}</td>
                        <td>{point.get('summary', 'N/A')}</td>
                        <td><span class="category-badge {importance_class}">{importance}</span></td>
                    </tr>"""
            
            content_html += """
                </tbody>
            </table>
        </div>"""
        
        # 주요 수치
        key_figures = data.get('key_figures', [])
        if key_figures:
            content_html += """
        <div style="margin-top: 24px;">
            <div style="font-size: 15px; font-weight: bold; color: #004578; margin-bottom: 12px;">
                📊 주요 수치
            </div>
            <table class="content-table">
                <thead>
                    <tr>
                        <th style="width: 20%;">유형</th>
                        <th style="width: 20%;">수치</th>
                        <th style="width: 60%;">설명</th>
                    </tr>
                </thead>
                <tbody>"""
            
            for figure in key_figures:
                content_html += f"""
                    <tr>
                        <td><span class="category-badge">{figure.get('type', 'N/A')}</span></td>
                        <td style="font-weight: 600; color: #e03a3e;">{figure.get('value', 'N/A')}</td>
                        <td>{figure.get('context', 'N/A')}</td>
                    </tr>"""
            
            content_html += """
                </tbody>
            </table>
        </div>"""
        
        # 타임라인
        timeline = data.get('timeline', [])
        if timeline:
            content_html += """
        <div style="margin-top: 24px;">
            <div style="font-size: 15px; font-weight: bold; color: #004578; margin-bottom: 12px;">
                📅 주요 일정
            </div>
            <div style="background: #f8f9fa; padding: 16px; border-radius: 6px;">"""
            
            for item in timeline:
                content_html += f"""
                <div class="timeline-item">
                    <strong>{item.get('date', 'N/A')}</strong>: {item.get('event', 'N/A')}
                </div>"""
            
            content_html += """
            </div>
        </div>"""
        
        # 관련 회사
        companies = data.get('companies_mentioned', [])
        if companies:
            content_html += """
        <div style="margin-top: 24px;">
            <div style="font-size: 15px; font-weight: bold; color: #004578; margin-bottom: 12px;">
                🏢 관련 회사
            </div>
            <div class="companies-list">"""
            
            for company in companies:
                content_html += f'<span class="company-tag">{company}</span>'
            
            content_html += """
            </div>
        </div>"""
        
        return content_html
    
    @staticmethod
    def _create_fallback_content(summary: str, pdf_name: str, pages: int, method: str, user_model: str, actual_model: str) -> str:
        """JSON 파싱 실패시 일반 텍스트 요약 표시"""
        
        content_html = f"""
        <div style="margin-top: 20px;">
            <div style="font-size: 15px; font-weight: bold; color: #004578; margin-bottom: 12px;">
                📝 문서 요약
            </div>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #e03a3e;">
                <div style="line-height: 1.6; color: #333;">
                    {HTMLFormatter._format_text_content(summary)}
                </div>
            </div>
        </div>
        
        <div style="margin-top: 20px; padding: 12px; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px;">
            <div style="color: #856404; font-size: 13px;">
                <strong>ℹ️ 안내:</strong> 구조화된 분석 결과를 생성하지 못해 일반 텍스트 요약을 표시합니다.
            </div>
        </div>"""
        
        return content_html
    
    @staticmethod
    def _format_text_content(text: str) -> str:
        """일반 텍스트를 HTML로 포맷팅"""
        if not text:
            return "<p>요약 내용이 없습니다.</p>"
        
        # 줄바꿈을 <br>로 변환
        formatted = text.replace('\n', '<br>')
        
        # bullet point 감지 및 처리
        lines = text.split('\n')
        if any(line.strip().startswith(('•', '-', '*', '▪', '▫', '1.', '2.', '3.')) for line in lines):
            html_lines = []
            in_list = False
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith(('•', '-', '*', '▪', '▫')):
                    if not in_list:
                        html_lines.append('<ul style="margin: 10px 0; padding-left: 20px;">')
                        in_list = True
                    content = stripped[1:].strip()
                    html_lines.append(f'<li style="margin: 6px 0;">{content}</li>')
                elif re.match(r'^\d+\.', stripped):
                    if not in_list:
                        html_lines.append('<ol style="margin: 10px 0; padding-left: 20px;">')
                        in_list = True
                    content = re.sub(r'^\d+\.\s*', '', stripped)
                    html_lines.append(f'<li style="margin: 6px 0;">{content}</li>')
                else:
                    if in_list:
                        html_lines.append('</ul>' if '•' in text or '-' in text else '</ol>')
                        in_list = False
                    if stripped:
                        html_lines.append(f'<p style="margin: 10px 0;">{stripped}</p>')
            
            if in_list:
                html_lines.append('</ul>' if '•' in text or '-' in text else '</ol>')
            
            formatted = ''.join(html_lines)
        else:
            # 일반 텍스트는 단락으로 분리
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            formatted = ''.join(f'<p style="margin: 10px 0;">{p}</p>' for p in paragraphs)
        
        return formatted
    
    @staticmethod
    def create_error_html(error_message: str, pdf_name: str = "document.pdf") -> str:
        """오류 발생시 HTML 생성"""
        current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")
        
        return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>❌ PDF 요약 오류</title>
    <style>
        body {{
            font-family: 'Malgun Gothic', sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            text-align: center;
        }}
        .error-container {{
            background: #fff5f5;
            border: 2px solid #fed7d7;
            border-radius: 12px;
            padding: 40px;
        }}
        .error-icon {{
            font-size: 64px;
            margin-bottom: 20px;
        }}
        .error-title {{
            color: #e53e3e;
            font-size: 24px;
            margin-bottom: 15px;
        }}
        .error-message {{
            color: #4a5568;
            font-size: 16px;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-icon">❌</div>
        <h1 class="error-title">PDF 요약 처리 실패</h1>
        <div class="error-message">
            <p><strong>파일:</strong> {pdf_name}</p>
            <p><strong>시간:</strong> {current_time}</p>
            <p><strong>오류:</strong> {error_message}</p>
            <p>관리자에게 문의해주세요.</p>
        </div>
    </div>
</body>
</html>""" 