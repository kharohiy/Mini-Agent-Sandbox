import sys
import unittest
from unittest.mock import patch
import runner

class MockResponse:
    class Message:
        def __init__(self, content):
            self.content = content
            self.tool_calls = None
        def model_dump(self):
            return {"role": "assistant", "content": self.content}
            
    class Choice:
        def __init__(self, content):
            self.message = MockResponse.Message(content)
            
    class Usage:
        total_tokens = 10
        
    def __init__(self, content):
        self.choices = [MockResponse.Choice(content)]
        self.usage = MockResponse.Usage()

def mock_llm_completion(model, messages, **kwargs):
    # Depending on the agent role in the system prompt, return a mocked response
    system_prompt = messages[0]["content"]
    
    if "Architectural Arbitrator" in system_prompt:
        return MockResponse("ARBITRATOR DECISION: I have reviewed the logs. We will use the Repository pattern.")
    elif "Feature Developer" in system_prompt:
        return MockResponse("```kotlin\nfun add(a: Int, b: Int) = a + b\n```")
    elif "Tech Lead Reviewer" in system_prompt:
        # Always reject to force deadlock
        return MockResponse("REJECTED. You must do it my way.")
    
    return MockResponse("mocked")

def test_deadlock_arbitration():
    print("Starting Arbitration test...")
    # Mock safe_llm_completion
    with patch('runner.safe_llm_completion', side_effect=mock_llm_completion):
        # We also need to mock validate_generated_code so it doesn't fail Ruff/Semgrep and loop infinitely
        with patch('runner.validate_generated_code', return_value=(True, "")):
            # Force the language gateway to just return english
            with patch('runner.language_gateway', return_value=("Write code", "en")):
                
                # Capture print statements to verify the output flow
                import io
                capturedOutput = io.StringIO()
                sys.stdout = capturedOutput
                
                # Fake input for the loop
                sys.stdin = io.StringIO("Write code\n\n")
                
                runner.run_agent_loop("test_user_arbitrator")
                
                sys.stdout = sys.__stdout__
                output = capturedOutput.getvalue()
                
                # Check for key phrases in output
                assert "Deadlock detected. Invoking Architectural Arbitrator" in output, "Arbitrator was not invoked!"
                assert "ARBITRATOR DECISION:" in output, "Arbitrator did not provide a decision!"
                assert "🎯 TASK COMPLETED" in output, "Task did not complete gracefully!"
                assert "Graceful Abandonment" not in output, "Hit hard step limit instead of resolving via Arbitrator!"
                
                print("✅ Arbitrated Debate logic passed successfully!")

if __name__ == "__main__":
    test_deadlock_arbitration()
