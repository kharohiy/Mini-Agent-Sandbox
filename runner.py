import json
import time
import os
import sys
import shutil
import subprocess
import re
from datetime import datetime, timezone
import litellm
import logging
from rag_service import SandboxRagService
from data_guardrail import guardrail
from telemetry_aggregator import aggregate_telemetry
from vault_registry import vault

def resolve_secrets(code_string: str) -> str:
    """Runner-Interceptor: Decrypts tokens before execution"""
    if not isinstance(code_string, str) or "__VAULT_SECRET_" not in code_string:
        return code_string
        
    pattern = re.compile(r"__VAULT_SECRET_[A-Z0-9_]+__")
    
    def replacer(match):
        token = match.group(0)
        real_secret = vault.get_secret(token)
        if real_secret:
            print(f"[Interceptor] 🔓 Unlocked secret for execution. Token: {token}")
            return real_secret
        else:
            print(f"[Interceptor] ❌ Invalid token detected: {token}")
            return token

    return pattern.sub(replacer, code_string)

# Configuring the basic logger
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("SandboxStorage")

# Disable junk logs from LiteLLM
logging.getLogger("LiteLLM").setLevel(logging.ERROR)
litellm.drop_params = True

ROLES_FILE = "roles.json"
MAX_TOOL_CALLS_PER_TURN = 5

AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_project_facts",
            "description": "Returns a list of active global architectural facts and project rules. Call this if you lack project context.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_project_fact",
            "description": "Adds a new global rule. If it replaces an old one, specify the text of the old rule in retire_fact.",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_fact": {"type": "string", "description": "New global rule."},
                    "retire_fact": {"type": "string", "description": "Text of the old rule being replaced (if any)."}
                },
                "required": ["new_fact"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Creates or overwrites a file in the user's workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Relative path to file (e.g. 'src/main.py')."},
                    "content": {"type": "string", "description": "File content."}
                },
                "required": ["filepath", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads the content of a file in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Relative path to file."}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Lists contents of a directory in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dirpath": {"type": "string", "description": "Relative path to directory (use empty string '' for root)."}
                },
                "required": ["dirpath"]
            }
        }
    }
]

class SandboxStorage:
    def __init__(self, base_dir="data"):
        self.base_dir = base_dir
        self._init_rag_config()

    def _init_rag_config(self):
        settings_file = os.path.join(self.base_dir, "settings.json")
        os.makedirs(self.base_dir, exist_ok=True)
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except FileNotFoundError:
            settings = {}
            
        if "rag_config" not in settings:
            settings["rag_config"] = {"chunk_size": 512, "chunk_overlap": 51}
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)

    def _get_user_dir(self, user_id):
        """Creates and returns an isolated subfolder for the user."""
        user_dir = os.path.join(self.base_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        return user_dir

    def purge_user_data(self, user_id):
        """Right-to-be-forgotten pattern (GDPR Compliance)."""
        user_dir = os.path.join(self.base_dir, user_id)
        try:
            shutil.rmtree(user_dir)
            logger.info(f"[GDPR Compliance] All Tier-1, Tier-2 data and archive files for {user_id} successfully destroyed.")
        except FileNotFoundError:
            logger.info(f"[GDPR Compliance] Data for user {user_id} not found.")
        except Exception as e:
            logger.error(f"[GDPR Compliance] Error when deleting user data {user_id}: {e}")

    def get_current_state(self, user_id):
        state_file = os.path.join(self._get_user_dir(user_id), "state.json")
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"status": "pending", "memory": [], "current_turn": "coder", "tool_executions": []}
            
    def save_state(self, user_id, state):
        # TEMPORARILY DISABLED: self._summarize_memory_if_needed(user_id, state)
        state_file = os.path.join(self._get_user_dir(user_id), "state.json")
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        keys_changed = list(state.keys())
        logger.info(f"STORAGE Tier-1 updated for user {user_id}. Keys changed: {keys_changed}")

    def _load_all_facts(self, user_id):
        facts_file = os.path.join(self._get_user_dir(user_id), "project_facts.json")
        try:
            with open(facts_file, "r", encoding="utf-8") as f:
                existing_facts = json.load(f)
        except FileNotFoundError:
            existing_facts = []
            
        normalized_facts = []
        for f in existing_facts:
            if isinstance(f, str):
                normalized_facts.append({"fact": f, "status": "canonical", "validAt": datetime.now(timezone.utc).isoformat(), "invalidAt": None})
            else:
                if f.get("status") == "active": f["status"] = "canonical"
                if f.get("status") == "retired": f["status"] = "superseded"
                if "updated_at" in f: f["validAt"] = f.pop("updated_at")
                if "invalidAt" not in f: f["invalidAt"] = None if f["status"] == "canonical" else datetime.now(timezone.utc).isoformat()
                normalized_facts.append(f)
        return normalized_facts

    def _summarize_memory_if_needed(self, user_id, state):
        if len(state.get("memory", [])) > 6:
            print(f"\n[Storage/System] Memory of user {user_id} is full. Compacting (Tier 1)...")
            
            to_compact = state["memory"][:-2]
            keep_fresh = state["memory"][-2:]
            
            archive_name = os.path.join(self._get_user_dir(user_id), f"archive_{state.get('session_id', 'unknown')}_{int(time.time())}.json")
            try:
                with open(archive_name, "w", encoding="utf-8") as f:
                    json.dump(to_compact, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"[Storage/System] Error when saving archive: {e}")
            
            text_to_summarize = ""
            for m in to_compact:
                text_to_summarize += f"{m['role'].upper()}:\n{m['content']}\n\n"
                
            prompt = f"""You are the system memory architect for AI agents. Your task is to compress the history of a technical debate between Coder and Reviewer...

Analyze this conversation log:
{text_to_summarize}

Formulate an updated concise technical status according to the rules:
1. Highlight only the final approved decisions.
2. Completely remove noise and rejected options.
3. Briefly describe what the agents agreed upon.

Your response must be as concise as possible."""
            
            try:
                response = safe_llm_completion(
                    model="gemini/gemini-2.5-flash",
                    messages=[{"role": "user", "content": prompt}],
                    user_id=user_id
                )
                new_summary = response.choices[0].message.content
                
                state["memory"] = [
                    {
                        "role": "user", 
                        "content": f"[Brief summary of previous steps]:\n{new_summary}",
                        "archive_pointer": archive_name,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                ] + keep_fresh
            except Exception as e:
                print(f"[Storage/System] Memory compression error: {e}")

    # ==========================
    # === WRITE PATH ===
    # ==========================

    def ingest_and_extract_facts(self, user_id, state_memory):
        print(f"\n[Storage/WritePath] Extracting new facts for {user_id}...")
        try:
            active_facts = [f for f in self._load_all_facts(user_id) if f.get("invalidAt") is None and f.get("status") == "canonical"]
            active_facts_str = "\n".join([f"- {f['fact']}" for f in active_facts])
            
            conversation_text = ""
            for m in state_memory:
                conversation_text += f"{m.get('role', 'unknown').upper()}:\n{m.get('content', '')}\n\n"
                
            prompt = f"""You are a system architect. Analyzing this log, extract ONLY global architectural rules, code style standards, or requirements for libraries used that apply to the ENTIRE project (e.g.: Use coroutines and delay to simulate network, Use MutableStateFlow for state in ViewModel, Extract repository interfaces separately from implementations).

STRICTLY IGNORE local business requirements of a specific feature (e.g., anything specifically related to the User entity, names Alice/Bob, or loading a user list — this is NOISE for future tasks).

Current canonical project facts:
{active_facts_str if active_facts_str else "No canonical facts"}

Supersession rule: if a new fact contradicts a current canonical one, the old fact must be marked for retirement.
Return STRICTLY a valid JSON object in the following format:
{{
  "new_facts": ["new fact 1", "new fact 2"],
  "retire_facts": ["exact text of the old fact from the list above that is no longer relevant"]
}}
If there are no new rules, return empty arrays.

LOG:
{conversation_text}"""
            
            response = safe_llm_completion(
                model="gemini/gemini-2.5-flash",
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" },
                user_id=user_id
            )
            answer = response.choices[0].message.content.strip()
            
            import re
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', answer, re.DOTALL)
            if match:
                answer = match.group(1)
            else:
                if answer.startswith("```json"): answer = answer[7:]
                elif answer.startswith("```"): answer = answer[3:]
                if answer.endswith("```"): answer = answer[:-3]
                
            try:
                result = json.loads(answer.strip())
                self._update_facts_with_stamp(user_id, result.get("new_facts", []), result.get("retire_facts", []))
            except Exception as json_err:
                print(f"[Storage/WritePath] JSON parse error: {json_err}")
                masked_answer = guardrail.run(answer.strip(), user_id)
                print(f"[Storage/WritePath] Raw LLM Answer (Masked): {masked_answer}")
                
        except Exception as e:
            print(f"[Storage/WritePath] Fact update error: {e}")

    def _update_facts_with_stamp(self, user_id, new_facts, retire_facts):
        existing_facts = self._load_all_facts(user_id)
        changes_made = False
        
        for old_f in retire_facts:
            for f in existing_facts:
                if f["fact"] == old_f and f.get("invalidAt") is None:
                    f["status"] = "superseded"
                    f["invalidAt"] = datetime.now(timezone.utc).isoformat()
                    changes_made = True
                    print(f"[Storage/WritePath] Fact retired: {old_f}")
                    
        for nf in new_facts:
            # The simplest protection against duplicates: checking for a substring.
            is_duplicate = False
            nf_lower = nf.lower()
            for f in existing_facts:
                if f.get("invalidAt") is None:
                    ef_lower = f["fact"].lower()
                    if nf_lower in ef_lower or ef_lower in nf_lower:
                        is_duplicate = True
                        break
                        
            if not is_duplicate:
                existing_facts.append({
                    "fact": nf,
                    "status": "canonical",
                    "validAt": datetime.now(timezone.utc).isoformat(),
                    "invalidAt": None
                })
                changes_made = True
                print(f"[Storage/WritePath] New fact added (canonical): {nf}")
                
        if changes_made:
            facts_file = os.path.join(self._get_user_dir(user_id), "project_facts.json")
            with open(facts_file, "w", encoding="utf-8") as f:
                json.dump(existing_facts, f, ensure_ascii=False, indent=2)
            logger.info(f"STORAGE Tier-2 updated for user {user_id}. Keys changed: facts updated (added {len(new_facts)}, retired {len(retire_facts)})")

    def update_state_metrics(self, user_id, state, tokens, cost, window_utilization_pct):
        m = state.setdefault("metrics", {})
        m.setdefault("total_tokens", 0)
        m.setdefault("total_cost", 0.0)
        m.setdefault("max_window_tokens", 1048576)
        m.setdefault("last_window_utilization_pct", 0.0)
        m.setdefault("fact_retrieval_hits", 0)
        
        m["total_tokens"] += tokens
        m["total_cost"] += cost
        m["last_window_utilization_pct"] = window_utilization_pct
        self.save_state(user_id, state)
        print(f"[Monitoring] Window utilization: {window_utilization_pct:.2f}%, Successful memory reads: {m['fact_retrieval_hits']}")

    # ==========================
    # === READ PATH ===
    # ==========================

    def assemble_context_window(self, user_id, task, base_system_prompt, state):
        active_facts = [f for f in self._load_all_facts(user_id) if f.get("invalidAt") is None and f.get("status") == "canonical"]
        
        proposed_file = os.path.join(self._get_user_dir(user_id), "proposed_facts.json")
        proposed_text = ""
        if os.path.exists(proposed_file):
            try:
                with open(proposed_file, "r", encoding="utf-8") as f:
                    pf_data = json.load(f)
                    pf = pf_data.get("proposed_fact")
                    if pf:
                        proposed_text = f"\n\n[SYSTEM DIAGNOSTICS - RECOVERY INSTRUCTION]\n{pf}\n"
            except Exception:
                pass
                
        if not active_facts:
            return base_system_prompt + proposed_text
            
        task_text = (task or "").lower()
        task_keywords = [w for w in task_text.replace(",", " ").replace(".", " ").split() if len(w) > 3]
        
        relevant_facts = []
        for f in active_facts:
            fact_lower = f["fact"].lower()
            if any(kw in fact_lower for kw in task_keywords):
                relevant_facts.append(f)
                
        if not relevant_facts:
            relevant_facts = sorted(active_facts, key=lambda x: x.get("validAt", ""), reverse=True)[:3]
            
        if relevant_facts:
            m = state.setdefault("metrics", {})
            m["fact_retrieval_hits"] = m.get("fact_retrieval_hits", 0) + 1
            
        facts_block = "\n- ".join(f["fact"] for f in relevant_facts)
        
        tool_execs = state.get("tool_executions", [])
        tool_execs_str = ""
        if tool_execs:
            tool_execs_str = "\n\nTOOL EXECUTIONS AGGREGATED DATA:\n" + json.dumps(tool_execs, ensure_ascii=False, indent=2)
            
        print(f"[Storage/ReadPath] Context {user_id} assembled. Facts: {len(relevant_facts)}")
        return f"{base_system_prompt}{proposed_text}{tool_execs_str}\n\nPROJECT CONTEXT:\n- {facts_block}"


def load_json(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def log_prediction_telemetry(user_id, model_name, tokens_used, duration, status):
    if not user_id: return
    telemetry_file = os.path.join("data", user_id, "telemetry.json")
    os.makedirs(os.path.dirname(telemetry_file), exist_ok=True)
    
    try:
        if os.path.exists(telemetry_file):
            with open(telemetry_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
    except Exception:
        data = []
        
    data.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model_name,
        "tokens_used": tokens_used,
        "duration": duration,
        "latency": duration,
        "status": status
    })
    
    with open(telemetry_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Global provider blacklist (safeguard)
provider_blacklist = {}

def safe_llm_completion(model, messages, tools=None, user_id=None, **extra_kwargs):
    # DataGuardrail: Sanitize incoming messages before sending to LLM
    for msg in messages:
        if isinstance(msg.get("content"), str):
            msg["content"] = guardrail.run(msg["content"], user_id)
            vault.save_mapping(guardrail.extract_vault_mapping())

    gemini_chain = [
        "gemini/gemini-2.5-flash",
        "gemini/gemini-3.5-flash",
        "gemini/gemini-3.0-flash"
    ]
    
    failed_in_this_turn = set()
    current_model = model  # Correction: starting with the requested model
    failed_attempts = 0
    
    while True:
        # Clear the blacklist of expired bans (older than 10 minutes).
        now = time.time()
        for m in list(provider_blacklist.keys()):
            if now - provider_blacklist[m] > 600:
                del provider_blacklist[m]

        # If the requested model (or the current one) is banned or has crashed during this turn, we look for a replacement.
        if current_model in provider_blacklist or current_model in failed_in_this_turn:
            available_chain = [m for m in gemini_chain if m not in provider_blacklist and m not in failed_in_this_turn]
            if available_chain:
                current_model = available_chain[0]
            else:
                current_model = "ollama/qwen2.5:14b"
                print(f"\n[ALERT] Cloud API Error Rate is 100%! Seamless fallback triggered. Failed attempts: {failed_attempts}. Switching to local VRAM execution. Check provider quotas immediately.")
                
        kwargs = {"model": current_model, "messages": messages}
        kwargs.update(extra_kwargs)
        if "max_tokens" not in kwargs:
            kwargs["max_tokens"] = 1500
        
        if current_model.startswith("ollama/"):
            kwargs["api_base"] = "http://localhost:11434"
            kwargs["tools"] = None
        else:
            if tools: kwargs["tools"] = tools
            if "-lite" in current_model: kwargs["tools"] = None
                    
        print(f"DEBUG Attempting to call model: {current_model}")
        try:
            start_time = time.time()
            response = litellm.completion(**kwargs)
            duration = time.time() - start_time
            
            # DataGuardrail: Sanitize outgoing LLM response
            try:
                if hasattr(response, 'choices') and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    if content:
                        response.choices[0].message.content = guardrail.run(content, user_id)
                        vault.save_mapping(guardrail.extract_vault_mapping())
            except Exception as e:
                print(f"[Guardrail] ⚠️ Response sanitization error: {e}")

            pt = response.usage.prompt_tokens if hasattr(response, 'usage') else 0
            ct = response.usage.completion_tokens if hasattr(response, 'usage') else 0
            
            status = "Success"
            if current_model == "ollama/qwen2.5:14b":
                status = "Fallback_Ollama_11434"
                
            log_prediction_telemetry(user_id, current_model, pt + ct, duration, status)
            return response
            
        except Exception as e:
            failed_attempts += 1
            duration = time.time() - start_time
            error_status = type(e).__name__
            if current_model == "ollama/qwen2.5:14b":
                error_status = "Fallback_Ollama_11434_Error"
                
            log_prediction_telemetry(user_id, current_model, 0, duration, error_status)
            
            if current_model == "ollama/qwen2.5:14b":
                # We return a clear error in the state instead of crashing.
                class DummyMessage:
                    content = "[System] ERROR: Local Ollama model is unavailable or timed out."
                class DummyChoice:
                    message = DummyMessage()
                class DummyResponse:
                    choices = [DummyChoice()]
                return DummyResponse()
                
            # Added `NotFoundError` (for when a model does not exist) to the global ban list!
            if "429" in str(e) or "RateLimit" in type(e).__name__ or error_status == "NotFoundError":
                provider_blacklist[current_model] = time.time()
                print(f"[Router] Provider {current_model} was globally banned (Error: {error_status}).")
            else:
                # If it is a different error, we simply skip this model in the current cycle.
                failed_in_this_turn.add(current_model)
                print(f"[Router] Error {error_status} in model {current_model}. Excluded for this turn.")

def validate_generated_code(file_path: str) -> tuple[bool, str]:
    """
    Two-circuit static code analysis of the Coder Agent.
    Circuit 1: Ruff (Syntax, imports, PEP8 standards)
    Circuit 2: Semgrep (Checking architectural guidelines compliance)
    """
    # Secure subprocess invocation: isolate environment and set strict timeout
    
    # 1. Check via Ruff
    try:
        ruff_res = subprocess.run([sys.executable, '-m', 'ruff', 'check', file_path], capture_output=True, text=True, timeout=10)
        if ruff_res.returncode != 0:
            return False, f"Ruff Linting Error:\n{ruff_res.stdout}"
    except subprocess.TimeoutExpired:
        return False, "Security Error: Ruff execution timed out."
        
    # 2. Check via Semgrep (Architectural Compliance)
    try:
        semgrep_res = subprocess.run(
            [sys.executable, '-m', 'semgrep', '--config=rules/repo_pattern.yaml', file_path], 
            capture_output=True, text=True, timeout=15
        )
        if "ERROR" in semgrep_res.stdout or semgrep_res.returncode != 0:
            return False, f"Semgrep Architecture Violation:\n{semgrep_res.stdout}"
    except subprocess.TimeoutExpired:
        return False, "Security Error: Semgrep execution timed out."
        
    return True, "Code is syntactically clean and complies with architecture facts."

def trigger_regulator(user_id):
    print("\n[Regulator] 👁️ Waking up to analyze telemetry (every 10 sessions)...")
    try:
        report = aggregate_telemetry(user_id)
        if not report or report.get("total_requests", 0) % 10 != 0:
            print("[Regulator] 💤 Condition not met or no data. Sleeping.")
            return

        regulator_prompt = (
            "You are a System Regulator. Your task is to analyze compressed telemetry metrics (Incident Summary) "
            "and propose improvements for roles or rules. You are forbidden to use external tools. "
            f"Current metrics: {json.dumps(report, ensure_ascii=False)}\n"
            "Identify system weaknesses based on errors or triggers."
        )
        messages = [{"role": "system", "content": regulator_prompt}]
        print("[Regulator] Analyzing metrics...")
        response = safe_llm_completion("ollama/qwen2.5:14b", messages, tools=None, user_id="system_regulator")
        content = response.choices[0].message.content if hasattr(response, 'choices') else ""
        print(f"[Regulator] 💡 Evolution proposal:\n{content}")
    except Exception as e:
        print(f"[Regulator] ⚠️ Execution Error: {e}")

def language_gateway(text):
    detect_prompt = f"Detect language of this text. Output the 2-letter ISO code (e.g. 'en', 'ru', 'es'). ONLY 2 letters, no other words:\n\n{text[:500]}"
    try:
        res = safe_llm_completion("ollama/qwen2.5:14b", [{"role": "user", "content": detect_prompt}], user_id="system_translator")
        lang = res.choices[0].message.content.strip().lower()
        if len(lang) > 2:
            lang = lang[:2]
            
        if lang != "en":
            print(f"[Language Gateway] 🌐 Non-English input detected ({lang}). Normalizing to English (Cross-lingual Communication)...")
            trans_res = safe_llm_completion("ollama/qwen2.5:14b", [
                {"role": "system", "content": "You are a professional translator. Translate the text to English. Output only the translation."},
                {"role": "user", "content": text}
            ], user_id="system_translator")
            return trans_res.choices[0].message.content.strip(), lang
        return text, "en"
    except Exception as e:
        return text, "en"

def reverse_language_gateway(text, target_lang):
    if target_lang == "en":
        return text
    print(f"[Language Gateway] 🌐 Reverse translating final response to user's native language ({target_lang})...")
    try:
        trans_res = safe_llm_completion("ollama/qwen2.5:14b", [
            {"role": "system", "content": f"You are a professional translator. Translate the text to ISO language code '{target_lang}'. Preserve all code blocks, structure, and markdown."},
            {"role": "user", "content": text}
        ], user_id="system_translator")
        return trans_res.choices[0].message.content.strip()
    except Exception as e:
        return text

def run_agent_loop(user_id):
    roles_data = load_json(ROLES_FILE)
    roles = roles_data.get("agents", {}) if roles_data else {}
    storage = SandboxStorage(base_dir="data")
    
    # Forced state reset for testing
    state = {
        "status": "idle",
        "current_turn": "coder",
        "memory": [],
        "tool_executions": [],
        "metrics": {"total_cost": 0.0}
    }
    
    new_task = input("\nEnter task for agents (or empty string to exit): ")
    if not new_task.strip():
        print("Exiting.")
        return
        
    normalized_task, user_lang = language_gateway(new_task)
    clean_task = guardrail.run(normalized_task, user_id)
    
    state["task"] = clean_task
    state["user_lang"] = user_lang
    state["status"] = "in_progress"
    
    state["memory"].append({
        "role": "user",
        "content": f"NEW TASK FROM USER: {clean_task}",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    storage.save_state(user_id, state)

    print(f"\nStarting Multi-Agent Sandbox for user: {user_id}...")
    
    step_count = 0
    while state.get("status") != "completed":
        step_count += 1
        
        if step_count > 8:
            print("\n[Graceful Abandonment] Hard step limit reached (8 steps). Agents are stuck in a loop. Terminating session.")
            state["status"] = "completed"
            storage.save_state(user_id, state)
            break
            
        m = state.get("metrics", {})
        if m.get("total_cost", 0.0) > 0.05:
            print("\nEmergency Stop: Session token budget exceeded! Stopping debates to save costs.")
            state["status"] = "completed"
            storage.save_state(user_id, state)
            break
            
        current_turn = state.get("current_turn", "coder")
        
        agent_config = None
        current_turn_lower = current_turn.lower()
        for key, config in roles.items():
            if key.lower() == current_turn_lower:
                agent_config = config
                break
        
        if not agent_config:
            print(f"Role {current_turn} not found in roles.json!")
            break
            
        print(f"\n--- Agent Turn: {agent_config['name']} ({current_turn}) ---")
        
        active_model = agent_config.get("model", "gemini/gemini-2.5-flash")
        rag_service = SandboxRagService(user_id, storage, active_model)
        
        rag_base_query = state.get("task", "")[:1000] # Limit query length for RAG
        
        # Query Expansion
        try:
            expansion_prompt = f"You are a search optimizer. Take the user's search query and return a comma-separated list of 3 synonyms or related technical terms in English and Russian. Query: {rag_base_query}"
            expansion_response = safe_llm_completion(
                model="gemini/gemini-2.5-flash-lite",
                messages=[{"role": "user", "content": expansion_prompt}],
                user_id=user_id
            )
            synonyms = expansion_response.choices[0].message.content.strip()
            expanded_query = f"{rag_base_query}, {synonyms}"
        except Exception as e:
            print(f"[Query Expansion Error] {e}")
            expanded_query = rag_base_query
            
        retrieved_docs_list = rag_service.query_relevant_docs(query=expanded_query, top_k=4)
        if retrieved_docs_list:
            formatted_docs = []
            for idx, doc_text in enumerate(retrieved_docs_list, start=1):
                formatted_docs.append(f"Document {idx} - Architecture Standard\n{doc_text}")
            retrieved_docs_str = "\n\n".join(formatted_docs)
        else:
            retrieved_docs_str = "No relevant context.."
        
        base_prompt = agent_config.get("system_prompt", "")
        wrapped_context = f"<retrieved_docs>\n{retrieved_docs_str}\n</retrieved_docs>"
        base_prompt += f"\n\n{wrapped_context}"
            
        system_prompt = storage.assemble_context_window(user_id, state.get("task"), base_prompt, state)
            
        messages = [{"role": "system", "content": system_prompt}]
        
        for mem in state["memory"]:
            role = "assistant" if mem["role"] == current_turn else "user"
            messages.append({"role": role, "content": mem["content"]})

        print("Waiting for LLM response...")
        try:
            tokens_used = 0
            cost = 0.0
            window_utilization_pct = 0.0
            tool_calls_this_turn = 0
            breaker_triggered = False
            
            while True:
                # Rough estimate of context volume
                total_chars = sum(len(str(m.get("content", ""))) for m in messages)
                approx_tokens = total_chars / 4
                m = state.setdefault("metrics", {})
                max_tokens = m.setdefault("max_window_tokens", 1048576)
                window_utilization_pct = (approx_tokens / max_tokens) * 100
                
                response = safe_llm_completion(
                    model=agent_config.get("model", "gemini/gemini-2.5-flash"),
                    messages=messages,
                    tools=AGENT_TOOLS,
                    user_id=user_id
                )
                
                message = response.choices[0].message
                
                # We collect metrics from all iterations (including tool calls).
                if hasattr(response, 'usage'):
                    tokens_used += response.usage.total_tokens
                    cost += response.usage.total_tokens * 0.000001
                
                if getattr(message, "tool_calls", None):
                    messages.append(message.model_dump()) # Adding the Tula query to the history.
                    
                    for tool_call in message.tool_calls:
                        tool_calls_this_turn += 1
                        if tool_calls_this_turn > MAX_TOOL_CALLS_PER_TURN:
                            print("\n[Security] Excessive Requests / Tool Noise detected! Circuit Breaker triggered.")
                            state.setdefault("memory", []).append({
                                "role": "user",
                                "content": "SECURITY BLOCK: Tool Rate Limit Exceeded. Passing turn to Analyst to stabilize.",
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })
                            state["current_turn"] = "analyst"
                            breaker_triggered = True
                            break
                            
                        func_name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)
                        print(f"\n[System Call] Agent calls tool: {func_name}")
                        
                        # Argument Deobfuscation (Runner-Interceptor)
                        for k, v in args.items():
                            if isinstance(v, str):
                                args[k] = resolve_secrets(v)
                        
                        # Human-in-the-loop for external/critical tools
                        if func_name in ["send_email", "access_calendar", "web_search"]:
                            print(f"\n[Security] WARNING: Agent attempting to call external/critical tool: {func_name}")
                            confirm = input("Allow execution? (y/n): ")
                            if confirm.lower() != 'y':
                                tool_result = "Action denied by human security guardrail."
                            else:
                                tool_result = "Action executed (mocked for safety)."
                        elif func_name == "read_project_facts":
                            active_facts = [f for f in storage._load_all_facts(user_id) if f.get("invalidAt") is None and f.get("status") == "canonical"]
                            if active_facts:
                                m = state.setdefault("metrics", {})
                                m["fact_retrieval_hits"] = m.get("fact_retrieval_hits", 0) + 1
                            facts_text = "\n".join([f"- {f['fact']}" for f in active_facts])
                            tool_result = facts_text if facts_text else "No active facts.."
                            
                        elif func_name == "update_project_fact":
                            new_fact = args.get("new_fact")
                            retire_fact = args.get("retire_fact")
                            retire_list = [retire_fact] if retire_fact else []
                            storage._update_facts_with_stamp(user_id, [new_fact], retire_list)
                            tool_result = f"Fact '{new_fact}' saved successfully."
                        elif func_name in ["create_file", "read_file", "list_directory"]:
                            user_dir = storage._get_user_dir(user_id)
                            # Handle empty dirpath as root
                            raw_path = args.get("filepath", args.get("dirpath", ""))
                            if raw_path == "" or raw_path == ".":
                                target_path = os.path.abspath(user_dir)
                            else:
                                target_path = os.path.abspath(os.path.join(user_dir, raw_path))
                                
                            # Path traversal protection
                            if not target_path.startswith(os.path.abspath(user_dir)):
                                tool_result = "Security Error: Path traversal detected. Access denied."
                            else:
                                try:
                                    if func_name == "create_file":
                                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                                        with open(target_path, "w", encoding="utf-8") as f:
                                            f.write(args.get("content", ""))
                                        tool_result = f"File created at {raw_path} successfully."
                                    elif func_name == "read_file":
                                        # Limit file reading to 50KB to prevent OOM / Context overload
                                        file_size = os.path.getsize(target_path)
                                        if file_size > 50 * 1024:
                                            tool_result = f"Security Error: File exceeds 50KB limit ({file_size} bytes)."
                                        else:
                                            with open(target_path, "r", encoding="utf-8") as f:
                                                tool_result = f.read()
                                    elif func_name == "list_directory":
                                        if os.path.exists(target_path) and os.path.isdir(target_path):
                                            items = os.listdir(target_path)
                                            tool_result = "\n".join(items) if items else "Directory is empty."
                                        else:
                                            tool_result = "Directory does not exist."
                                except Exception as e:
                                    tool_result = f"FS Error: {e}"
                        else:
                            tool_result = "Unknown tool."
                            
                        state.setdefault("tool_executions", []).append({
                            "tool_name": func_name,
                            "arguments": args,
                            "raw_result": tool_result,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                            
                        messages.append({
                            "role": "tool",
                            "name": func_name,
                            "content": tool_result,
                            "tool_call_id": tool_call.id
                        })
                    if breaker_triggered:
                        break
                    # We proceed to the next `while` loop iteration so the model can provide a final answer based on the tool's result.
                else:
                    answer = message.content
                    break
            
            if breaker_triggered:
                storage.update_state_metrics(user_id, state, tokens_used, cost, window_utilization_pct)
                continue
                
            print("Response:\n", answer)
            
            state.setdefault("memory", []).append({
                "role": current_turn,
                "content": answer,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            if current_turn == "coder":
                user_workspace = storage._get_user_dir(user_id)
                is_clean, validation_error = validate_generated_code(user_workspace)
                if not is_clean:
                    print("\n[Shift-Left Validation] 🚨 Intercepted error before Reviewer. Returning to Coder.")
                    state["current_turn"] = "coder"
                    state.setdefault("memory", []).append({
                        "role": "user",
                        "content": f"Validation Error! Fix errors using file tools:\n{validation_error}",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    storage.update_state_metrics(user_id, state, tokens_used, cost, window_utilization_pct)
                    continue

                if state.get("force_complete_next"):
                    state["status"] = "completed"
                    # Reset the flag so we don't accidentally auto-complete in future turns if we add more loops
                    state["force_complete_next"] = False
                else:
                    state["current_turn"] = "reviewer"
            elif current_turn == "reviewer":
                if "APPROVE" in answer.strip():
                    state["status"] = "completed"
                    storage.ingest_and_extract_facts(user_id, state.get("memory", []))
                else:
                    if step_count >= 5:
                        print("\n[Arbitration] Deadlock detected. Invoking Architectural Arbitrator...")
                        state["current_turn"] = "arbitrator"
                        state.setdefault("memory", []).append({
                            "role": "user",
                            "content": "The Feature Developer and Tech Lead Reviewer are in a deadlock. You are the Arbitrator. Review their debate logs. Evaluate the pros and cons of the proposed architectures. Make a final architectural decision to break the deadlock and justify it based on Clean Architecture principles. Do not debate, just decide.",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                    else:
                        state["current_turn"] = "coder"
            elif current_turn == "arbitrator":
                state["current_turn"] = "coder"
                state.setdefault("memory", []).append({
                    "role": "user",
                    "content": "Coder, implement exactly the architecture decided by the Arbitrator. No more debates. This is your final attempt.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                state["force_complete_next"] = True
            
            storage.update_state_metrics(user_id, state, tokens_used, cost, window_utilization_pct)
            
        except Exception as e:
            print(f"Error during LLM call: {e}")
            break
            
    if state.get("status") == "completed":
        print("\n--- 🎯 TASK COMPLETED ---")
        print("Formulating final structured response...")
        
        history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in state.get("memory", [])])
        final_prompt = f"You are an experienced Software Engineer. Based on the debate log between the Coder and Reviewer agents, formulate a final, noise-free response for the user.\nYou MUST output in English.\nResponse structure:\n1. 🎯 Approach to the solution\n2. 💻 Final code\n3. 📝 Brief explanation.\n\nAgent debate:\n{history_text}"
        
        try:
            final_res = safe_llm_completion(
                model="ollama/qwen2.5:14b",
                messages=[{"role": "user", "content": final_prompt}],
                user_id=user_id
            )
            english_result = final_res.choices[0].message.content.strip()
            
            final_result = reverse_language_gateway(english_result, state.get("user_lang", "ru"))
            
            print("\n=== FINAL RESULT ===")
            print(final_result)
            print("=============================\n")
        except Exception as e:
            print(f"Failed to formulate final response: {e}")

    # Trigger regulator at the end of the session
    trigger_regulator(user_id)

def clear_session_history(user_id):
    storage = SandboxStorage(base_dir="data")
    state = storage.get_current_state(user_id)
    
    state["memory"] = []
    state["tool_executions"] = []
    state["status"] = "in_progress"
    state["current_turn"] = "coder"
    # The metrics (cost/tokens) and the task itself remain unchanged.
    
    # Direct saving, bypassing compression
    state_file = os.path.join(storage._get_user_dir(user_id), "state.json")
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        
    print(f"[System] RAM for user {user_id} cleared (state.json). Fact base (Tier 2) is untouched!")

def unload_ollama_models():
    import urllib.request
    print("\n[System] Clearing VRAM from local Ollama models...")
    models_to_unload = ["qwen2.5:14b"]
    
    for model in models_to_unload:
        try:
            req = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=json.dumps({"model": model, "keep_alive": 0}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=5)
            print(f"[System] Model {model} successfully unloaded from memory.")
        except Exception as e:
            pass # Ignore if server is off or model wasn't loaded

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--clear":
        clear_session_history(sys.argv[2])
    else:
        target_user = sys.argv[1] if len(sys.argv) > 1 else "user_123"
        try:
            run_agent_loop(user_id=target_user)
        finally:
            # We clear memory after the session ends (whether due to a crash or a normal termination).
            unload_ollama_models()
