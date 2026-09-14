import os

replacements = {
    # runner.py
    "Resetting state for": "Resetting state for",
    "Memory compression error": "Memory compression error",
    "Extracting new facts for": "Extracting new facts for",
    "JSON parse error": "JSON parse error",
    "Fact update error": "Fact update error",
    "Fact retired": "Fact retired",
    "New fact added": "New fact added",
    "Window utilization": "Window utilization",
    "Successful memory reads": "Successful memory reads",
    "Context": "Context",
    "assembled. Facts:": "assembled. Facts:",
    "Attempting to call model": "Attempting to call model",
    "Response sanitization error": "Response sanitization error",
    "ERROR: Local Ollama model is unavailable or timed out": "ERROR: Local Ollama model is unavailable or timed out",
    "was globally banned (Error": "was globally banned (Error",
    "Error": "Error",
    "in model": "in model",
    "Excluded for this turn": "Excluded for this turn",
    "Waking up to analyze telemetry (every 10 sessions)": "Waking up to analyze telemetry (every 10 sessions)",
    "Condition not met or no data. Sleeping": "Condition not met or no data. Sleeping",
    "Analyzing metrics": "Analyzing metrics",
    "Evolution proposal": "Evolution proposal",
    "Architecture Standard": "Architecture Standard",
    "No relevant context.": "No relevant context.",
    "Waiting for LLM response": "Waiting for LLM response",
    "Agent calls tool": "Agent calls tool",
    "No active facts.": "No active facts.",
    "Response:": "Response:",
    "during LLM call": "during LLM call",
    "RAM for user": "RAM for user",
    "cleared (state.json). Fact base (Tier 2) is untouched!": "cleared (state.json). Fact base (Tier 2) is untouched!",
    
    # evals & prompts
    "You are a System Regulator. Your task is to analyze compressed telemetry metrics (Incident Summary)": "You are a System Regulator. Your task is to analyze compressed telemetry metrics (Incident Summary)",
    "and propose improvements for roles or rules. You are forbidden to use external tools.": "and propose improvements for roles or rules. You are forbidden to use external tools.",
    "Current metrics:": "Current metrics:",
    "Identify weak spots in the system based on errors or triggers. Propose a rule.": "Identify weak spots in the system based on errors or triggers. Propose a rule.",
    "\"rule\" in content.lower()": "\"rule\" in content.lower()",

    # analyst_agent.py
    "Role 'analyst' not found in roles.json.": "Role 'analyst' not found in roles.json.",
    "Code successfully passed review. Log analysis not required.": "Code successfully passed review. Log analysis not required.",
    "Gathering context for Analyst...": "Gathering context for Analyst...",
    "A system anomaly or empty agent response was detected in the pipeline, causing a loop. Analyze the log, find the failure point, and form a Few-Shot example-instruction to fix the main agent's output format.": "A system anomaly or empty agent response was detected in the pipeline, causing a loop. Analyze the log, find the failure point, and form a Few-Shot example-instruction to fix the main agent's output format.",
    "Waiting for model response...": "Waiting for model response...",
    "Proposed Few-Shot example": "Proposed Few-Shot example",
    "Apply proposed Few-Shot example? (y/n): ": "Apply proposed Few-Shot example? (y/n): ",
    "Example saved to": "Example saved to",
    "Example rejected.": "Example rejected."
}

def translate_files():
    for filename in ['runner.py', 'evals_pipeline.py', 'analyst_agent.py']:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for ru, en in replacements.items():
            content = content.replace(ru, en)
            
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
    print("Files translated.")

if __name__ == "__main__":
    translate_files()
