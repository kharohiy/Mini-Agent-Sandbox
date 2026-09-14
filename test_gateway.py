import sys
import io
from runner import run_agent_loop

# Mock input for Case RU
input_data = "Write a simple function to add two numbers in Python. Do not use Repository Pattern.\n\n"
sys.stdin = io.StringIO(input_data)

print("=== STARTING INTEGRATION TEST (CASE EN) ===")
run_agent_loop("test_ru")
print("=== END INTEGRATION TEST ===")
