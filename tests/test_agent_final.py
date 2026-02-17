import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

from app.core.langgraph.graph import LangGraphAgent

async def test_agent_final_answer():
    agent = LangGraphAgent()
    session_id = "test_session_final"
    
    print("Sending message to agent...")
    # This should trigger RAG tool, then loop back to LLM for final answer
    messages = [{"role": "user", "content": "What is the company refund policy?"}]
    
    result = await agent.get_response(messages, session_id)
    
    print("\n--- Final Agent Response ---")
    for msg in result:
        print(f"[{msg['role']}]: {msg['content'][:200]}...")
    
    # Verify that the last message is from the assistant and is NOT just tool metadata
    last_msg = result[-1]
    if last_msg['role'] == 'assistant' and last_msg['content']:
        print("\n✅ Agent generated a final answer.")
    else:
        print("\n❌ Agent did not generate a final answer.")

if __name__ == "__main__":
    asyncio.run(test_agent_final_answer())
