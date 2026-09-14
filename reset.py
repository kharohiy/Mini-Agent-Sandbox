import sys
import json
import os
from runner import SandboxStorage

def reset_session(user_id):
    storage = SandboxStorage(base_dir="data")
    state_file = os.path.join(storage._get_user_dir(user_id), "state.json")
    
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
    except FileNotFoundError:
        print(f"[Error] state.json for {user_id} not found.")
        return
        
    state["memory"] = []
    state["status"] = "in_progress"
    state["current_turn"] = "coder"
    
    # Save directly, bypassing the compression logic.
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        
    print(f"[System] RAM for user {user_id} cleared. project_facts.json is untouched!")

if __name__ == "__main__":
    user = sys.argv[1] if len(sys.argv) > 1 else "user_123"
    reset_session(user)
