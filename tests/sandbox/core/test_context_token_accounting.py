import os
import unittest
from unittest.mock import patch

from context_token_accounting import ContextTokenCount, count_context_tokens, render_ollama_qwen_prompt
from model_router import ModelRequest


MESSAGES = [
    {"role": "system", "content": "Reply with exactly OK."},
    {"role": "user", "content": "What is 2 + 2?"},
]

TOOLS = [{
    "type": "function",
    "function": {
        "name": "weather",
        "description": "Get current weather.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}]
TOOL_CALL_MESSAGES = [
    {"role": "user", "content": "Weather in Kyiv?"},
    {"role": "assistant", "content": "", "tool_calls": [{
        "function": {"name": "weather", "arguments": {"city": "Kyiv"}},
    }]},
]
TOOL_RESPONSE_MESSAGES = [
    *TOOL_CALL_MESSAGES,
    {"role": "tool", "content": '{"temperature":20}'},
]
TOOL_SCHEMA_MESSAGES = [
    {"role": "system", "content": "Reply with exactly OK."},
    {"role": "user", "content": "Weather in Kyiv?"},
]


class ContextTokenAccountingTests(unittest.TestCase):
    def test_qwen_renderer_matches_observed_ollama_template(self):
        self.assertEqual(
            render_ollama_qwen_prompt(MESSAGES),
            "<|im_start|>system\nReply with exactly OK.<|im_end|>\n"
            "<|im_start|>user\nWhat is 2 + 2?<|im_end|>\n<|im_start|>assistant\n",
        )

    def test_unconfigured_qwen_preserves_legacy_estimate(self):
        with patch.dict(os.environ, {"MINI_AGENT_QWEN_TOKENIZER_DIR": ""}):
            counted = count_context_tokens("ollama/qwen2.5:14b", MESSAGES)
        self.assertEqual((counted.tokens, counted.mode), (9, "legacy-estimate"))

    @unittest.skipUnless(
        os.environ.get("MINI_AGENT_QWEN_TOKENIZER_DIR"),
        "set MINI_AGENT_QWEN_TOKENIZER_DIR for the pinned local Qwen tokenizer asset",
    )
    def test_pinned_qwen_asset_matches_observed_ollama_prompt_count(self):
        counted = count_context_tokens("ollama/qwen2.5:14b", MESSAGES)
        self.assertEqual((counted.tokens, counted.mode), (26, "qwen-ollama-exact"))

    @unittest.skipUnless(
        os.environ.get("MINI_AGENT_QWEN_TOKENIZER_DIR"),
        "set MINI_AGENT_QWEN_TOKENIZER_DIR for the pinned local Qwen tokenizer asset",
    )
    def test_pinned_qwen_asset_matches_observed_ollama_tool_schema_count(self):
        counted = count_context_tokens("ollama/qwen2.5:14b", TOOL_SCHEMA_MESSAGES, TOOLS)
        self.assertEqual((counted.tokens, counted.mode), (135, "qwen-ollama-exact"))

    def test_qwen_renderer_matches_observed_ollama_tool_schema_shape(self):
        rendered = render_ollama_qwen_prompt(TOOL_SCHEMA_MESSAGES, TOOLS)
        self.assertIn(
            '{"type": "function", "function": {weather Get current weather. '
            '{object <nil> <nil> [city] {"city":{"type":"string"}}}}}',
            rendered,
        )

    @unittest.skipUnless(
        os.environ.get("MINI_AGENT_QWEN_TOKENIZER_DIR"),
        "set MINI_AGENT_QWEN_TOKENIZER_DIR for the pinned local Qwen tokenizer asset",
    )
    def test_pinned_qwen_asset_matches_observed_ollama_tool_call_count(self):
        counted = count_context_tokens("ollama/qwen2.5:14b", TOOL_CALL_MESSAGES)
        self.assertEqual((counted.tokens, counted.mode), (52, "qwen-ollama-exact"))

    @unittest.skipUnless(
        os.environ.get("MINI_AGENT_QWEN_TOKENIZER_DIR"),
        "set MINI_AGENT_QWEN_TOKENIZER_DIR for the pinned local Qwen tokenizer asset",
    )
    def test_pinned_qwen_asset_matches_observed_ollama_tool_response_count(self):
        counted = count_context_tokens("ollama/qwen2.5:14b", TOOL_RESPONSE_MESSAGES)
        self.assertEqual((counted.tokens, counted.mode), (76, "qwen-ollama-exact"))

    def test_router_uses_shared_counter_when_no_explicit_estimate(self):
        with patch("model_router.count_context_tokens", return_value=ContextTokenCount(26, "exact")):
            self.assertEqual(ModelRequest(model="ollama/qwen2.5:14b", messages=MESSAGES).context_tokens, 26)

    def test_router_passes_tools_to_shared_counter(self):
        with patch("model_router.count_context_tokens", return_value=ContextTokenCount(135, "exact")) as counter:
            request = ModelRequest(
                model="ollama/qwen2.5:14b", messages=MESSAGES, extra_kwargs={"tools": TOOLS}
            )
            self.assertEqual(request.context_tokens, 135)
        self.assertEqual(counter.call_args.args, ("ollama/qwen2.5:14b", MESSAGES, TOOLS))


if __name__ == "__main__":
    unittest.main()
