"""Modern DeepSeek transport; upstream search and prompts are unchanged.

DeepSeek accepts one completion per request, so n samples use n requests.
API credentials are read from the environment and are never written to logs.
"""

import json
import os
import time
from pathlib import Path

from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

completion_tokens = prompt_tokens = api_calls = retry_calls = 0
_client = None
_log_path = None
_call_limit = 350
_token_limit = 200000


class BudgetExceeded(RuntimeError):
    """Stop an instance instead of allowing unbounded API expenditure."""


def reset_usage(log_path=None, call_limit=350, token_limit=200000):
    global completion_tokens, prompt_tokens, api_calls, retry_calls
    global _log_path, _call_limit, _token_limit
    completion_tokens = prompt_tokens = api_calls = retry_calls = 0
    _log_path = Path(log_path) if log_path else None
    _call_limit, _token_limit = call_limit, token_limit


def _append(record):
    if _log_path is not None:
        _log_path.parent.mkdir(parents=True, exist_ok=True)
        with _log_path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')


def _get_client():
    global _client
    if _client is None:
        key = os.environ.get('DEEPSEEK_API_KEY')
        if not key:
            raise RuntimeError('Set DEEPSEEK_API_KEY through Colab Secrets; do not put it in a notebook.')
        _client = OpenAI(api_key=key,
            base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
            timeout=90.0, max_retries=0)
    return _client


def chatgpt(messages, model=None, temperature=0.7, max_tokens=1000, n=1, stop=None):
    global completion_tokens, prompt_tokens, api_calls, retry_calls
    model = model or os.getenv('DEEPSEEK_MODEL', 'deepseek-flash')
    outputs = []
    # Independent draws replace the old SDK's batched n parameter.
    for sample in range(n):
        params = dict(model=model, messages=messages, temperature=temperature,
                      top_p=1.0, max_tokens=max_tokens,
                      extra_body={'thinking': {'type': 'disabled'}})
        if stop is not None:
            params['stop'] = stop
        for attempt in range(3):
            if api_calls >= _call_limit or prompt_tokens + completion_tokens >= _token_limit:
                raise BudgetExceeded('Per-instance API call/token budget reached; failure is retained.')
            api_calls += 1
            start = time.perf_counter()
            try:
                response = _get_client().chat.completions.create(**params)
            except (APIConnectionError, APIStatusError) as exc:
                code = getattr(exc, 'status_code', None)
                retryable = isinstance(exc, (APIConnectionError, RateLimitError)) or (code is not None and code >= 500)
                _append({'event': 'api_error', 'attempt': attempt + 1,
                         'error_type': type(exc).__name__, 'status_code': code,
                         'seconds': time.perf_counter() - start})
                if not retryable or attempt == 2:
                    raise
                retry_calls += 1
                time.sleep(2 ** attempt)
                continue
            usage = response.usage
            in_tokens = usage.prompt_tokens if usage else 0
            out_tokens = usage.completion_tokens if usage else 0
            prompt_tokens += in_tokens
            completion_tokens += out_tokens
            text = response.choices[0].message.content or ''
            _append({'event': 'completion', 'sample': sample, 'attempt': attempt + 1,
                     'created': response.created,
                     'requested_model': model, 'resolved_model': response.model,
                     'response_id': response.id,
                     'system_fingerprint': getattr(response, 'system_fingerprint', None),
                     'temperature': temperature, 'top_p': 1.0, 'max_tokens': max_tokens,
                     'thinking': 'disabled', 'stop': stop, 'messages': messages,
                     'output': text, 'finish_reason': response.choices[0].finish_reason,
                     'usage': usage.model_dump() if usage else None,
                     'seconds': time.perf_counter() - start})
            outputs.append(text)
            break
    return outputs


def gpt(prompt, model=None, temperature=0.7, max_tokens=1000, n=1, stop=None):
    return chatgpt([{'role': 'user', 'content': prompt}], model=model,
                   temperature=temperature, max_tokens=max_tokens, n=n, stop=stop)


def gpt_usage(backend=None):
    # USD is deliberately omitted: cache hits and time-dependent tariffs matter.
    return {'completion_tokens': completion_tokens, 'prompt_tokens': prompt_tokens,
            'total_tokens': completion_tokens + prompt_tokens,
            'api_calls': api_calls, 'retry_calls': retry_calls, 'cost': None}
