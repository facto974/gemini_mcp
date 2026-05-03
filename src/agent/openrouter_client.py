"""Client OpenRouter (free tier) — utilisé pour faire valider/contester un signal."""
from __future__ import annotations

from openai import OpenAI


SYSTEM_PROMPT = """You are a senior quantitative trader. Given a structured trading
signal (score, momentum, sentiment, fear&greed) and the proposed action, respond
strictly with JSON: {"approve": true|false, "reason": "..."}.
Reject the action if (a) the signal is weak/contradictory, (b) sentiment and
momentum disagree strongly, or (c) fear&greed is extreme in the opposite side."""


class OpenRouterAgent:
    def __init__(self, api_key: str, model: str, temperature: float = 0.2):
        self.enabled = bool(api_key)
        self.model = model
        self.temperature = temperature
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key or "no-key",
        ) if api_key else None

    def validate(self, signal: dict, action: str) -> dict:
        """Retourne {'approve': bool, 'reason': str}. Approuvé par défaut si LLM off."""
        if not self.enabled or self.client is None:
            return {"approve": True, "reason": "LLM disabled (default approve)"}
        try:
            user = (f"signal={signal}\nproposed_action={action}\n"
                    f"Return only JSON {{\"approve\": bool, \"reason\": str}}.")
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user},
                ],
            )
            text = resp.choices[0].message.content.strip()
            import json
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                data = json.loads(text[start:end + 1])
                return {"approve": bool(data.get("approve", True)),
                        "reason": str(data.get("reason", ""))}
            return {"approve": True, "reason": "unparsable"}
        except Exception as e:  # noqa: BLE001
            return {"approve": True, "reason": f"llm_error: {e}"}
