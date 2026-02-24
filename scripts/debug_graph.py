
import asyncio
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from app.schemas import GraphState

async def check():
    mem = MemorySaver()
    print("MemorySaver attributes:", dir(mem))
    
    workflow = StateGraph(GraphState)
    workflow.add_node("test", lambda x: x)
    workflow.set_entry_point("test")
    app = workflow.compile(checkpointer=mem)
    print("CompiledStateGraph attributes:", dir(app))
    
    if hasattr(mem, "adelete"):
        print("MemorySaver has adelete")
    else:
        print("MemorySaver does NOT have adelete")

    if hasattr(app, "adelete"):
        print("CompiledStateGraph has adelete")
    else:
        print("CompiledStateGraph does NOT have adelete")

if __name__ == "__main__":
    asyncio.run(check())
