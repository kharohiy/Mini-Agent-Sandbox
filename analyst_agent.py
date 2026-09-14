import json
import sys
import os
from runner import SandboxStorage, safe_llm_completion, load_json, ROLES_FILE

def main():
    user_id = sys.argv[1] if len(sys.argv) > 1 else "eval_bot"
    storage = SandboxStorage(base_dir="data")
    
    roles_data = load_json(ROLES_FILE)
    if not roles_data or "analyst" not in roles_data.get("agents", {}):
        print("Role 'analyst' not found in roles.json.")
        sys.exit(1)
        
    analyst_config = roles_data["agents"]["analyst"]
    
    state = storage.get_current_state(user_id)
    memory = state.get("memory", [])
    
    # We are looking for the reviewer's latest message.
    last_reviewer_msg = None
    for msg in reversed(memory):
        if msg.get("role") == "reviewer":
            last_reviewer_msg = msg.get("content", "")
            break
            
    has_anomaly = False
    for msg in memory:
        if len(msg.get("content", "").strip()) < 5:
            has_anomaly = True
            break
            
    if state.get("status") == "completed" and not (last_reviewer_msg and "APPROVE" in last_reviewer_msg):
        has_anomaly = True
        
    if last_reviewer_msg and "APPROVE" in last_reviewer_msg and not has_anomaly:
        print("Code successfully passed review. Log analysis not required.")
        sys.exit(0)
        
    print("Gathering context for Analyst...")
    conversation_text = ""
    for m in memory:
        conversation_text += f"{m.get('role', 'unknown').upper()}:\n{m.get('content', '')}\n\n"
        
    if has_anomaly:
        prompt = f"A system anomaly or empty agent response was detected in the pipeline, causing a loop. Analyze the log, find the failure point, and form a Few-Shot example-instruction to fix the main agent's output format.\n\nLog:\n{conversation_text}"
        model_to_use = "ollama/qwen2.5:14b"
    else:
        prompt = f"{analyst_config['system_prompt']}\n\nLog:\n{conversation_text}"
        model_to_use = analyst_config.get("model", "ollama/qwen2.5:14b")
    
    messages = [{"role": "system", "content": prompt}]
    
    print("Waiting for model response...")
    try:
        response = safe_llm_completion(
            model=model_to_use,
            messages=messages,
            user_id=user_id
        )
        
        answer = response.choices[0].message.content.strip()
        print("\n--- Proposed Few-Shot example ---")
        print(answer)
        print("------------------------------------")
        
        user_input = input("Apply proposed Few-Shot example? (y/n): ").strip().lower()
        if user_input == 'y':
            proposed_file = os.path.join(storage._get_user_dir(user_id), "proposed_facts.json")
            with open(proposed_file, "w", encoding="utf-8") as f:
                json.dump({"proposed_fact": answer}, f, ensure_ascii=False, indent=2)
            print(f"Example saved to {proposed_file}")
        else:
            print("Example rejected.")
            
    except Exception as e:
        print(f"Error during LLM call: {e}")

if __name__ == "__main__":
    main()
