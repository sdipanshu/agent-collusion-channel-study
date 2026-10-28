"""Collect an OpenAI-style server-sent-event stream into the same dict shape as a non-streamed reply."""
import json


def collect_stream(response):
    content, reasoning, finish, usage, model = [], [], None, {}, None
    for raw in response.iter_lines(decode_unicode=True):
        if not raw or not raw.startswith("data:"):
            continue
        body = raw[5:].strip()
        if body == "[DONE]":
            break
        chunk = json.loads(body)
        model = chunk.get("model", model)
        if chunk.get("usage"):
            usage = chunk["usage"]
        for choice in chunk.get("choices") or []:
            delta = choice.get("delta") or {}
            if delta.get("content"):
                content.append(delta["content"])
            part = delta.get("reasoning_content") or delta.get("reasoning")
            if part:
                reasoning.append(part)
            if choice.get("finish_reason"):
                finish = choice["finish_reason"]
    message = {"role": "assistant", "content": "".join(content)}
    if reasoning:
        message["reasoning_content"] = "".join(reasoning)
    return {"model": model, "choices": [{"message": message, "finish_reason": finish}], "usage": usage, "streamed": True}
