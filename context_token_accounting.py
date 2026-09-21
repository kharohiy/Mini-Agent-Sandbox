"""Deterministic context counting for the configured local Qwen model."""

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


QWEN_MODEL = "ollama/qwen2.5:14b"
QWEN_TOKENIZER_DIR_ENV = "MINI_AGENT_QWEN_TOKENIZER_DIR"
QWEN_TOKENIZER_SHA256 = "c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539"
QWEN_TOKENIZER_CONFIG_SHA256 = "5b5d4f65d0acd3b2d56a35b56d374a36cbc1c8fa5cf3b3febbbfabf22f359583"
QWEN_OLLAMA_SYSTEM_PROMPT = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."


@dataclass(frozen=True)
class ContextTokenCount:
    tokens: int
    mode: str


def _legacy_estimate(messages: Sequence[Mapping[str, Any]]) -> ContextTokenCount:
    return ContextTokenCount(
        sum(len(str(message.get("content", ""))) for message in messages) // 4,
        "legacy-estimate",
    )


def _compact_json(value: Any) -> str | None:
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    except (TypeError, ValueError):
        return None


def _render_ollama_tool_function(function: Mapping[str, Any]) -> str | None:
    """Mirror Ollama 0.21.0's Go-template rendering of `.Function`.

    The installed Qwen template renders a Go struct directly rather than
    JSON-marshalling it. Keep this deliberately narrow: unknown JSON-schema
    extensions fall back to the legacy estimate instead of being guessed.
    """
    if set(function) - {"name", "description", "parameters"}:
        return None
    name = function.get("name")
    description = function.get("description", "")
    parameters = function.get("parameters")
    if not isinstance(name, str) or not isinstance(description, str) or not isinstance(parameters, Mapping):
        return None
    if set(parameters) - {"type", "required", "properties"}:
        return None
    schema_type = parameters.get("type")
    required = parameters.get("required", [])
    properties = parameters.get("properties")
    if (
        not isinstance(schema_type, str)
        or not isinstance(required, Sequence)
        or isinstance(required, (str, bytes))
        or not all(isinstance(value, str) for value in required)
        or not isinstance(properties, Mapping)
    ):
        return None
    properties_json = _compact_json(properties)
    if properties_json is None:
        return None
    required_text = "[" + " ".join(required) + "]"
    return f"{{{name} {description} {{{schema_type} <nil> <nil> {required_text} {properties_json}}}}}"


def _tool_instruction_block(tools: Sequence[Mapping[str, Any]]) -> str | None:
    rendered_tools: list[str] = []
    for tool in tools:
        if not isinstance(tool, Mapping) or tool.get("type") != "function":
            return None
        function = tool.get("function")
        if not isinstance(function, Mapping) or not isinstance(function.get("name"), str):
            return None
        function_text = _render_ollama_tool_function(function)
        rendered = (
            '{"type": "function", "function": ' + function_text + "}"
            if function_text is not None
            else None
        )
        if rendered is None:
            return None
        rendered_tools.append(rendered)
    if not rendered_tools:
        return ""
    return (
        "# Tools\n\n"
        "You may call one or more functions to assist with the user query.\n\n"
        "You are provided with function signatures within <tools></tools> XML tags:\n"
        "<tools>\n"
        + "\n".join(rendered_tools)
        + "\n</tools>\n\n"
        "For each function call, return a json object with function name and arguments within "
        "<tool_call></tool_call> XML tags:\n"
        "<tool_call>\n"
        '{"name": <function-name>, "arguments": <args-json-object>}\n'
        "</tool_call>\n"
    )


def _render_assistant_tool_calls(tool_calls: Any) -> str | None:
    if not isinstance(tool_calls, Sequence) or isinstance(tool_calls, (str, bytes)):
        return None
    blocks: list[str] = []
    for call in tool_calls:
        if not isinstance(call, Mapping) or not isinstance(call.get("function"), Mapping):
            return None
        function = call["function"]
        name = function.get("name")
        arguments = function.get("arguments")
        if not isinstance(name, str):
            return None
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                return None
        arguments_json = _compact_json(arguments)
        if arguments_json is None:
            return None
        blocks.append(
            "<tool_call>\n"
            f'{{"name": "{name}", "arguments": {arguments_json}}}\n'
            "</tool_call>"
        )
    return "\n".join(blocks)


def render_ollama_qwen_prompt(
    messages: Sequence[Mapping[str, Any]], tools: Sequence[Mapping[str, Any]] | None = None
) -> str | None:
    """Render the verified text/tool subset of the installed Ollama Qwen template."""
    system_messages = [message for message in messages if message.get("role") == "system"]
    turns = [message for message in messages if message.get("role") != "system"]
    tool_block = _tool_instruction_block(tools) if tools is not None else ""
    if len(system_messages) > 1 or tool_block is None:
        return None
    parts: list[str] = []
    if system_messages:
        system_content = system_messages[0].get("content")
        if not isinstance(system_content, str):
            return None
        if tool_block:
            system_content = f"{system_content}\n\n{tool_block}"
        parts.append(f"<|im_start|>system\n{system_content}<|im_end|>\n")
    else:
        default_system = QWEN_OLLAMA_SYSTEM_PROMPT
        if tool_block:
            default_system = f"{default_system}\n\n{tool_block}"
        parts.append(f"<|im_start|>system\n{default_system}<|im_end|>\n")
    for index, message in enumerate(turns):
        is_last = index == len(turns) - 1
        role = message.get("role")
        content = message.get("content")
        if role == "user":
            if not isinstance(content, str) or message.get("tool_calls"):
                return None
            parts.append(f"<|im_start|>user\n{content}<|im_end|>\n")
        elif role == "tool":
            if not isinstance(content, str) or message.get("tool_calls"):
                return None
            parts.append(f"<|im_start|>user\n<tool_response>\n{content}\n</tool_response><|im_end|>\n")
        elif role == "assistant":
            tool_calls = message.get("tool_calls")
            if tool_calls:
                rendered_calls = _render_assistant_tool_calls(tool_calls)
                if rendered_calls is None or content not in {None, ""}:
                    return None
                parts.append(f"<|im_start|>assistant\n{rendered_calls}")
            elif isinstance(content, str):
                parts.append(f"<|im_start|>assistant\n{content}")
            else:
                return None
            if not is_last:
                parts.append("<|im_end|>\n")
        else:
            return None
    if not turns or turns[-1]["role"] != "assistant":
        parts.append("<|im_start|>assistant\n")
    return "".join(parts)


def _verified_tokenizer_path() -> Path | None:
    root = os.environ.get(QWEN_TOKENIZER_DIR_ENV)
    if not root:
        return None
    directory = Path(root).expanduser().resolve()
    tokenizer_path = directory / "tokenizer.json"
    config_path = directory / "tokenizer_config.json"
    if not tokenizer_path.is_file() or not config_path.is_file():
        return None
    if hashlib.sha256(tokenizer_path.read_bytes()).hexdigest() != QWEN_TOKENIZER_SHA256:
        return None
    if hashlib.sha256(config_path.read_bytes()).hexdigest() != QWEN_TOKENIZER_CONFIG_SHA256:
        return None
    return tokenizer_path


def count_context_tokens(
    model: str,
    messages: Sequence[Mapping[str, Any]],
    tools: Sequence[Mapping[str, Any]] | None = None,
) -> ContextTokenCount:
    """Use Qwen's verified local tokenizer, otherwise preserve legacy behavior."""
    rendered = render_ollama_qwen_prompt(messages, tools) if model == QWEN_MODEL else None
    tokenizer_path = _verified_tokenizer_path() if rendered is not None else None
    if tokenizer_path is None:
        return _legacy_estimate(messages)
    from tokenizers import Tokenizer

    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    token_count = len(tokenizer.encode(rendered).ids)
    if tools:
        # Ollama 0.21.0 reports one fewer prompt token for a rendered tool
        # schema than tokenizers' JSON asset. This is verified against the
        # local /api/chat prompt_eval_count; do not generalize it to text or
        # tool-history prompts, which have independent acceptance fixtures.
        token_count -= 1
    return ContextTokenCount(token_count, "qwen-ollama-exact")
