"""
LLM API Provider 모듈
- Gemini 2.0 Flash
- GPT-5-nano
- GPT-5-mini
- GPT-4o-mini
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """LLM 응답 데이터 클래스"""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int

    @property
    def estimated_cost(self) -> float:
        """예상 비용 계산 (USD)"""
        # 모델별 가격 ($/1M tokens)
        pricing = {
            "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
            "gpt-5-nano": {"input": 0.05, "output": 0.40},
            "gpt-5-mini": {"input": 0.25, "output": 2.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        }

        if self.model in pricing:
            p = pricing[self.model]
            return (self.input_tokens * p["input"] + self.output_tokens * p["output"]) / 1_000_000
        return 0.0


class LLMProvider(ABC):
    """LLM Provider 베이스 클래스"""

    name: str = "base"
    model_id: str = ""

    # 가격 정보 ($/1M tokens)
    input_price: float = 0.0
    output_price: float = 0.0

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> LLMResponse:
        """텍스트 생성"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """API 사용 가능 여부 확인"""
        pass

    def get_pricing_info(self) -> dict:
        """가격 정보 반환"""
        return {
            "model": self.model_id,
            "input_price_per_1m": self.input_price,
            "output_price_per_1m": self.output_price,
        }


class GeminiFlashProvider(LLMProvider):
    """Google Gemini 2.0 Flash"""

    name = "Gemini 2.0 Flash"
    model_id = "gemini-2.0-flash"
    input_price = 0.10
    output_price = 0.40

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self._client = None

        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel("gemini-2.0-flash-exp")
            except ImportError:
                pass

    def is_available(self) -> bool:
        return self._client is not None

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> LLMResponse:
        if not self.is_available():
            return LLMResponse("", self.model_id, 0, 0, 0)

        try:
            # 시스템 프롬프트 + 사용자 프롬프트 결합
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            response = self._client.generate_content(
                full_prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                }
            )

            # 토큰 수 추정 (Gemini는 직접 제공하지 않을 수 있음)
            input_tokens = len(full_prompt.split()) * 1.3  # 대략적 추정
            output_tokens = len(response.text.split()) * 1.3

            return LLMResponse(
                content=response.text,
                model=self.model_id,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
                total_tokens=int(input_tokens + output_tokens)
            )

        except Exception as e:
            print(f"[Gemini] 생성 오류: {e}")
            return LLMResponse("", self.model_id, 0, 0, 0)


class OpenAIProvider(LLMProvider):
    """OpenAI 모델 베이스 클래스"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                pass

    def is_available(self) -> bool:
        return self._client is not None

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> LLMResponse:
        if not self.is_available():
            return LLMResponse("", self.model_id, 0, 0, 0)

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self._client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            content = response.choices[0].message.content or ""
            usage = response.usage

            return LLMResponse(
                content=content,
                model=self.model_id,
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0
            )

        except Exception as e:
            print(f"[{self.name}] 생성 오류: {e}")
            return LLMResponse("", self.model_id, 0, 0, 0)


class GPT5NanoProvider(OpenAIProvider):
    """GPT-5-nano (최저가)"""
    name = "GPT-5-nano"
    model_id = "gpt-5-nano"
    input_price = 0.05
    output_price = 0.40


class GPT5MiniProvider(OpenAIProvider):
    """GPT-5-mini (GPT-5 80% 성능)"""
    name = "GPT-5-mini"
    model_id = "gpt-5-mini"
    input_price = 0.25
    output_price = 2.00


class GPT4oMiniProvider(OpenAIProvider):
    """GPT-4o-mini (검증된 모델)"""
    name = "GPT-4o-mini"
    model_id = "gpt-4o-mini"
    input_price = 0.15
    output_price = 0.60


class LLMManager:
    """
    통합 LLM 매니저
    - 여러 LLM Provider 관리
    - 모델 선택 및 비교
    """

    PROVIDERS = {
        "Gemini 2.0 Flash": GeminiFlashProvider,
        "GPT-5-nano": GPT5NanoProvider,
        "GPT-5-mini": GPT5MiniProvider,
        "GPT-4o-mini": GPT4oMiniProvider,
    }

    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}
        self._init_providers()

    def _init_providers(self):
        """모든 Provider 초기화"""
        for name, provider_class in self.PROVIDERS.items():
            self._providers[name] = provider_class()

    def get_available_providers(self) -> list[str]:
        """사용 가능한 Provider 목록 반환"""
        return [name for name, provider in self._providers.items() if provider.is_available()]

    def get_all_providers(self) -> list[str]:
        """모든 Provider 이름 반환"""
        return list(self.PROVIDERS.keys())

    def get_pricing_info(self, provider_name: str) -> Optional[dict]:
        """특정 Provider의 가격 정보 반환"""
        if provider_name in self._providers:
            return self._providers[provider_name].get_pricing_info()
        return None

    def generate(
        self,
        prompt: str,
        provider_name: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> LLMResponse:
        """
        텍스트 생성

        Args:
            prompt: 사용자 프롬프트
            provider_name: 사용할 LLM Provider
            system_prompt: 시스템 프롬프트
            max_tokens: 최대 출력 토큰
            temperature: 창의성 (0.0 ~ 1.0)

        Returns:
            LLMResponse 객체
        """
        if provider_name not in self._providers:
            return LLMResponse(
                content=f"알 수 없는 Provider: {provider_name}",
                model="",
                input_tokens=0,
                output_tokens=0,
                total_tokens=0
            )

        provider = self._providers[provider_name]
        if not provider.is_available():
            return LLMResponse(
                content=f"{provider_name} API 키가 설정되지 않았습니다.",
                model=provider.model_id,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0
            )

        return provider.generate(prompt, system_prompt, max_tokens, temperature)


# 편의를 위한 싱글톤 인스턴스
_llm_manager: Optional[LLMManager] = None


def get_llm_manager() -> LLMManager:
    """LLMManager 싱글톤 인스턴스 반환"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager
