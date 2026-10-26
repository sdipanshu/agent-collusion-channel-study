"""HF-hosted chat transport. No local inference and no provider fallback."""
import json
import os
import time
from pathlib import Path

from dotenv import dotenv_values
from terrarium.llm.clients.vllm_client import VLLMClient, _convert_tools


def load_token():
    token = os.getenv("HF_TOKEN", "").strip()
    if not token:
        env = Path(__file__).resolve().parents[3] / ".env"
        token = (dotenv_values(env).get("HF_TOKEN") or "").strip()
    if not token and os.getenv("HF_TOKEN_FILE"):
        path = Path(os.environ["HF_TOKEN_FILE"])
        raw = path.read_text(encoding="utf-8-sig").strip()
        token = (dotenv_values(path).get("HF_TOKEN") or "").strip() if "=" in raw else raw
    if not token:
        raise RuntimeError("HF_TOKEN is required even for included credits; no inference was started")
    return token


class HFClient(VLLMClient):
    requests_made = 0
    tokens_used = 0

    def __init__(self, model, log_path, actor):
        super().__init__("https://router.huggingface.co/v1", model,
                         api_key=load_token(), request_timeout=120)
        self.log_path = Path(log_path)
        self.actor = actor

    def generate_response(self, input, params):
        if HFClient.requests_made >= int(os.getenv("HF_MAX_REQUESTS", "60")):
            raise RuntimeError("HF request cap reached")
        if HFClient.tokens_used >= int(os.getenv("HF_MAX_TOTAL_TOKENS", "100000")):
            raise RuntimeError("HF observed-token cap reached")
        payload = {"model": self.model_name, "messages": input,
                   "max_tokens": int(params.get("max_output_tokens") or
                                     params.get("max_completion_tokens") or 256),
                   "temperature": float(params.get("temperature", 0.7))}
        if params.get("tools"):
            payload["tools"] = _convert_tools(params["tools"])
        HFClient.requests_made += 1
        start = time.monotonic()
        response = self.session.post(self.base_url + "/chat/completions",
                                     headers=self._build_headers(), json=payload,
                                     timeout=self.request_timeout)
        # Never log headers or credentials; record failed calls without response bodies.
        record = {"actor": self.actor, "model": self.model_name,
                  "elapsed_seconds": time.monotonic()-start,
                  "http_status": response.status_code, "request": payload}
        if response.ok:
            data = response.json()
            record["response"] = data
            HFClient.tokens_used += int((data.get("usage") or {}).get("total_tokens", 0))
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        if not response.ok:
            raise RuntimeError(f"HF inference HTTP {response.status_code}; no retry/fallback. Check account access and credits.")
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("HF returned no choices")
        if choices[0].get("finish_reason") == "length":
            raise RuntimeError("HF response truncated at output budget; smoke gate failed")
        return data, self._extract_message_content(choices[0].get("message") or {})
