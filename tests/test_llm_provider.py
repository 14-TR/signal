from signalai.llm.provider import FallbackProvider
from signalai.llm.cache import LLMCache


class DummyProvider:
    def __init__(self, model: str = "dummy", response: str = "ok"):
        self.model = model
        self.response = response
        self.calls = 0

    def chat(self, messages):
        self.calls += 1
        return self.response


class FailingProvider:
    def __init__(self, model: str = "fail"):
        self.model = model
        self.calls = 0

    def chat(self, messages):
        self.calls += 1
        return ""


def test_cache_uses_prompt_and_model_params():
    cache = LLMCache()
    messages = [{"role": "user", "content": "hello"}]

    p1 = DummyProvider(model="m1")
    fb1 = FallbackProvider([p1], cache=cache)
    assert fb1.chat(messages) == "ok"
    assert fb1.chat(messages) == "ok"
    assert p1.calls == 1  # second call served from cache

    p2 = DummyProvider(model="m2")
    fb2 = FallbackProvider([p2], cache=cache)
    assert fb2.chat(messages) == "ok"
    assert p2.calls == 1  # different model -> not cached


def test_fallback_and_cache_behavior():
    cache = LLMCache()
    messages = [{"role": "user", "content": "hi"}]

    failing = FailingProvider()
    secondary = DummyProvider(model="m2", response="fallback")
    fb = FallbackProvider([failing, secondary], cache=cache, retries=2)

    assert fb.chat(messages) == "fallback"
    assert failing.calls == 2  # retried twice before fallback
    assert secondary.calls == 1

    # Second invocation hits cache; no additional calls
    assert fb.chat(messages) == "fallback"
    assert failing.calls == 2
    assert secondary.calls == 1
