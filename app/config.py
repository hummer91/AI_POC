"""
설정 및 상수
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 앱 설정
APP_TITLE = "AI POC - 건강기능식품 검색 챗봇"
APP_ICON = "🔬"

# 검색 설정
DEFAULT_SEARCH_RESULTS = 5
MAX_SEARCH_RESULTS = 10

# LLM 설정
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TEMPERATURE = 0.7

# 가격 정보 ($/1M tokens)
LLM_PRICING = {
    "Gemini 2.0 Flash": {"input": 0.10, "output": 0.40},
    "GPT-5-nano": {"input": 0.05, "output": 0.40},
    "GPT-5-mini": {"input": 0.25, "output": 2.00},
    "GPT-4o-mini": {"input": 0.15, "output": 0.60},
}

SEARCH_PRICING = {
    "DDGS": {"free_limit": "무제한", "cost_per_1k": 0},
    "Brave": {"free_limit": "2,000/월", "cost_per_1k": 3.0},
    "Tavily": {"free_limit": "1,000/월", "cost_per_1k": 8.0},
    "Google": {"free_limit": "100/일", "cost_per_1k": 5.0},
}
