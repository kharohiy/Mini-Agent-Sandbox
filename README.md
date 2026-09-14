  🚀 Architecture and Design of the "Mini Agent Sandbox" Project 
  The Mini Agent Sandbox project is a custom, locally deployable sandbox operating on the principles of an LLM-OS (LLM-based Operating System). It is designed    
  for autonomous resolution of engineering tasks through the interactive collaboration of several specialized AI agents, equipped with their own multi-level memory and       
  tools for interacting with the environment.
  Below is a detailed breakdown of the architecture, patterns, and tools embedded in the project.
  ──────
  ## 💡 Concept and Idea
  Instead of relying on a single prompt to a large language model, the system uses the concept of Multi-Agent Debate.
  The process is divided into roles. Currently, three basic ones are implemented:

  1. Feature Developer (Coder): Writes code based on the user's task and architectural context.
  2. Tech Lead Reviewer: A strict critic who checks the code for memory leaks, errors, and code-style compliance.
  3. Data Analyst (Analyst / Predictive Architect-Diagnostician): Analyzes session logs and generates Few-Shot instructions to fix the output.
  4. Architectural Arbitrator (Judge): Steps in in case of a deadlock between the Coder and Reviewer. Analyzes the logs of their debates and delivers a final, unappealable architectural verdict.

  Agents communicate in a loop until the Tech Lead is convinced of the solution's quality and issues an APPROVE verdict.
  ──────
  ## 🏗 System Architecture (Enterprise AI Pipeline)

The project's architecture is built around a 4-stage data processing pipeline that meets Enterprise AI standards:

### 1. Ingestion & Validation
- **Vector Database & Advanced RAG (ChromaDB)**: The knowledge base runs on the local `ollama/nomic-embed-text` model. The context is isolated by user.
  - *Knowledge Ingestion Pipeline*: Automatic conversion of PDF books to Markdown, semantic chunking, and vectorization.
  - *Query Expansion & Dynamic Context*: Query expansion with synonyms and dynamic substitution of architectural rules into prompts. Acts as **Restating Binding Constraints**, forcibly reminding agents of global rules on every turn.
- **Shift-Left Validation**: Static code analysis (Ruff, Semgrep) runs *before* passing the code to the Reviewer Agent. Errors are caught at an early stage, returning the code to the Coder with a detailed report, saving time and tokens. Linter execution is hardware-isolated via `subprocess` with strict timeouts (10s/15s) to prevent hangs.

### 2. Security & Anonymization
- **Mini Presidio (Layered DataGuardrail)**: Three-tier serverless leak protection: Regex, Contextual Validation, and Tokenization Engine (two-way obfuscation with substitution by tokens like `__VAULT_SECRET_...__`). Includes a Deobfuscation Vault (VaultRegistry) that encrypts the key map (Fernet AES-128) and unpackages tokens (Runner-Interceptor) on the fly before local code execution.
- **Prompt Injection Protection**: Includes Affirmative Reframing (CBSI framework), RAG Isolation (escaping extracted facts with XML tags), and Output Integrity Guardrails.
- **Multimodal & MCP Isolation**: Protection against hidden commands in images (OCR Attack Protection) and strict directory isolation (Path Traversal Protection). A Human-in-the-loop (HITL) mechanism is built-in for critical tool calls. **Protection against The Agentic Shift vector:** Agents are hardware-restricted from direct access to the system shell at the tool level (tools like `execute_command` are absent). This completely eliminates the risk of Install-time execution (automatic downloading and installation of malicious dependencies), ensuring the system remains under the operator's full control.
- **Tool Circuit Breaker**: Protection against agent looping (Excessive Requests) with a hard limit (`MAX_TOOL_CALLS_PER_TURN = 5`). If exceeded, execution is interrupted (`SECURITY BLOCK`).

### 3. AI Analysis & Orchestration
- **Multi-Agent Debate**: Coder, Reviewer, Analyst, and Arbitrator debate until the `APPROVE` status is reached. The Reviewer Agent is reinforced with strict protocols: **SIX-DIMENSIONAL AUDIT METHOD** (code analysis across 6 vectors: dependencies, logic, access rights, etc.) and **AUDIT WORKFLOW** (a 4-step check with mandatory Unit test requirements and Slopsquatting protection). Built-in Arbitrated Debate & Graceful Abandonment safeguard (forced loop termination at step 8). A hard session reset is a defense against **Long-Session Failure (Silent Context Loss)**, preventing agents from forgetting initial requirements when logs grow excessively.
- **Smart LLM Router & Circuit Breaker**: An intelligent proxy `safe_llm_completion` implementing a dynamic model cascade (Cloud -> Lite -> Local Ollama). It tracks quotas (429 RateLimit) and blocks unavailable providers.
- **Tiered Memory Architecture**: 
  - *Tier-1 (Working Memory)*: `state.json` stores the Session State. Includes the Orchestrator Tool Tracking mechanism for strict logging of tool calls and eliminating hallucinations.
  - *Tier-2 (Long-term Knowledge Base)*: `project_facts.json` for storing global architectural rules.
- **Dynamic Token Limiting**: Hard output token limits (1000 for Coder, 150 for Reviewer).

### 4. Output Delivery
- **Cross-lingual Communication (Language Gateway)**: A two-way language gateway. The user's request is translated into English (accelerates inference and saves tokens by 3-4 times), and the final response is translated back into the user's native language.
- **Output Formatting Pattern**: Hiding the agents' internal debates from the user. Only a clean, final response is outputted after task completion.

  ──────
  ## ⚙️ Key Mechanisms and Design Patterns

  The project uses classic engineering patterns:

  1. State Machine
  The `run_agent_loop` operation cycle is implemented as a state machine: `status: "in_progress" | "completed"` and `current_turn: "coder" | "reviewer"`. The state machine guarantees    
  clear context transfer between agents without human intervention.
  2. Repository & Adapter Pattern
  The `SandboxStorage` class encapsulates all file system operations. Agents and functions do not touch files directly, but request or save state through
  a storage adapter.
  3. Function Calling & Orchestrator Tracking (Agent Tools)
  Agents are "hardwired" with the tools `read_project_facts`, `update_project_fact`, `create_file`, `read_file`, and `list_directory`.
  The Supersession mechanism (Rule Replacement) is used to update facts.
  Each tool call is recorded in the `tool_executions` array of the state machine, forming a verifiable, deterministic log (Orchestrator Tracking). Agents receive this log in context and are obligated to rely only on the actual tool execution results, not their own guesses.
  4. Chain of Responsibility
  The error handling logic in the API (`safe_llm_completion`) passes the request through a chain of providers until one of them returns a successful response.
  ──────
  ## 🧪 Testing and Monitoring (LLMOps)
  The project includes built-in mechanisms for evaluating agent quality and monitoring costs:

  1. Hardened Evals Pipeline (CI/CD Security Check)
  The `evals_pipeline.py` script uses a dataset of attack vectors (`tests/adversarial_prompts.json`). 
  👉 **A detailed description of all attacks, testing scenarios (including Tool Abuse, Memory Poisoning, and Shift-Left Validation), and behavior rules are described in a special guideline: [TESTS.md](TESTS.md).**
  
  • The pipeline simulates the debate cycle and validates that DataGuardrail or the Reviewer successfully blocked the attack. It returns a strict Security Score (target value: 100%). If the Score is below 100%, the script issues `sys.exit(1)`, interrupting the hypothetical CI/CD process and protecting against the deployment of vulnerable roles.

  2. Telemetry Aggregation & System Regulator (Self-learning)
  Instead of raw logs, the `telemetry_aggregator.py` script is used, which mathematically compresses `telemetry.json` into `incident_summary.json`. 
  • **Regulator Agent**: Every 10 sessions, a special super-agent "Regulator" is launched. It analyzes dry incident statistics (without access to raw user prompts, which completely eliminates *Data Poisoning*) and automatically generates improvements for `roles.json` or the facts database.
  • **Evolutionary Facts**: To avoid endless memory bloat (`project_facts.json`), the Regulator uses semantic consolidation — it merges similar facts and removes unused ones using the LRU algorithm, strictly maintaining the limit (no more than 15 facts).

  3. Drift Metrics (Drift Control)
  After running automatic tests, the pipeline analyzes the average number of agent debate rounds. If solving a single task takes on average more than 3 iterations, the system issues a WARNING about context drift, signaling the need for prompt calibration or facts review.

  4. Prompt Engineering & Few-Shot Prompting (Prompt Tuning)
  The system allows flexible management of review quality through the configuration of system instructions (`roles.json`). The use of strict acceptance criteria (Guardrails) and the introduction of `Few-Shot` examples (providing specific code templates with errors and the expected reaction) forms a powerful semantic anchor for the LLM's Attention mechanism. This forces the language model to more accurately identify architectural violations and push the agents' Accuracy to high values.
  • **UI State Observation Guardrails**: The role is hardcoded with strict Anti-patterns for Jetpack Compose: the use of infinite `while(true)` loops inside `LaunchedEffect` is prohibited. The Reviewer is trained to uncompromisingly reject such solutions and demand safe methods for subscribing to state.
  • **Predictive Architect Diagnostics**: The Analyst agent is endowed with an auto-recovery mechanism. If the base models start outputting empty responses or the session loops, the Analyst intercepts the log and forcibly generates a strict instruction on the output format (for example, demanding to wrap the code in markdown), saving the pipeline from crashing.
  ──────
  ## 🛠 Tech Stack and Tooling

  The project is written in Python with a minimal number of external dependencies to maintain lightweightness:

  • LiteLLM (`litellm`): The main driver of the system. A powerful library that unifies API calls to 100+ providers (Google, OpenAI, Anthropic) under a single input-       
  output standard (OpenAI API Format).
  • Ollama: A local engine for running open-source LLMs on the user's desktop. Acts as a guarantor of autonomy and free inference if the clouds stop responding.
    - **AMD GPU Support**: To activate hardware acceleration on AMD (Radeon) graphics cards, before starting the pipeline, you must start the Ollama server in a separate terminal window with a special environment variable:
      ```cmd
      set HSA_OVERRIDE_GFX_VERSION=10.3.0
      ollama serve
      ```
  • Python Standard Library (`json`, `os`, `shutil`, `datetime`): Used for managing the file system, facts lifetime metrics, and state serialization.  
  • Logging (`logging`): Targeted logger configuration blocks garbage output from libraries, leaving the console clean and transparent for observing the agents' thoughts.       

  ### Summary

  Mini Agent Sandbox is a fault-tolerant, confidential, and autonomous system. It is able to survive under the harsh limits of a free API, shifting tasks
  from the cloud to a local graphics card, while teaching AI agents to negotiate with each other to write perfect code.

  ──────
  ## 🚀 Release 1.0 (Production-Ready)
  
  The system has successfully passed all tests and is locked as the stable Version 1.0:
  - **Self-Healing & RAG**: ✅ Agents autonomously extract architectural rules and apply them. The Analyst successfully intercepts infinite loops.
  - **Mini Presidio Guardrail**: ✅ Absolute interception of AWS keys, API tokens, and PII through a 3-layer system (Regex + Contextual Validation).
  - **Hardened Evals**: ✅ Security Score 100% against injections (Indirect, Multimodal, Role-play, Exfiltration).
  - **Regulator Trigger**: ✅ Self-evolution is enabled: every 10 sessions, the system rewrites its facts and strengthens security based on telemetry metadata, protecting against Data Poisoning.
  - **Two-Way Obfuscation (Deobfuscation Vault)**: ✅ Successfully implemented the tokenization and interception model. Sensitive data is substituted with tokens (`__VAULT_SECRET_...__`), and transparently deobfuscated via `Runner-Interceptor` before actual code execution. The key map is stored outside the working directory and is encrypted.

  ──────
  ## 🔮 Future Roadmap
  
  - **Dynamic Model Downgrade Strategy**: Development of a smarter token planner capable of switching tasks on the fly between heavy cloud models and lightweight local models depending on context complexity (Cost Optimization).