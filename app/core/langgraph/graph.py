"""This file contains the LangGraph Agent/workflow and interactions with the LLM."""

import asyncio
from datetime import datetime
from typing import (
    AsyncGenerator,
    Optional,
)

from asgiref.sync import sync_to_async
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ToolMessage,
)
# from langfuse.langchain import CallbackHandler
from langgraph.checkpoint.memory import MemorySaver   # ✅ CHANGED
from langgraph.graph import (
    END,
    StateGraph,
)
from langgraph.graph.state import (
    Command,
    CompiledStateGraph,
)
from langgraph.types import (
    RunnableConfig,
    StateSnapshot,
)
from app.services.memory import memory_service

from app.core.config import (
    Environment,
    settings,
)
from app.core.langgraph.tools import tools
from app.core.logging import logger
from app.core.metrics import llm_inference_duration_seconds
from app.core.prompts import load_system_prompt
from app.schemas import (
    GraphState,
    Message,
)
from app.services.llm import llm_service
from app.utils import (
    dump_messages,
    prepare_messages,
    process_llm_response,
)


class LangGraphAgent:
    def __init__(self):
        self.llm_service = llm_service
        self.llm_service.bind_tools(tools)
        self.tools_by_name = {tool.name: tool for tool in tools}

        self._graph: Optional[CompiledStateGraph] = None

        logger.info(
            "langgraph_agent_initialized",
            model=settings.DEFAULT_LLM_MODEL,
            environment=settings.ENVIRONMENT.value,
        )

    async def create_graph(self) -> Optional[CompiledStateGraph]:
        if self._graph is None:
            try:
                graph_builder = StateGraph(GraphState)
                
                # Nodes
                graph_builder.add_node("router", self._router_node)
                graph_builder.add_node("tool_call", self._tool_call_node)
                graph_builder.add_node("final_llm", self._final_llm_node)
                
                # Entry point is the Router
                graph_builder.set_entry_point("router")
                
                # Edges
                graph_builder.add_conditional_edges(
                    "router",
                    self._router_logic,
                    {
                        "tool_call": "tool_call",
                        "final_llm": "final_llm",
                    }
                )
                
                # After tool call, go to final_llm
                graph_builder.add_edge("tool_call", "final_llm")
                
                # After final_llm, we are done
                graph_builder.add_edge("final_llm", END)

                checkpointer = MemorySaver()
                self._graph = graph_builder.compile(
                    checkpointer=checkpointer,
                    name=f"{settings.PROJECT_NAME} Agent ({settings.ENVIRONMENT.value})",
                )

                logger.info("graph_created_strictly_aligned")

            except Exception as e:
                logger.error("graph_creation_failed", error=str(e))
                raise e

        return self._graph

    async def clear_chat_history(self, session_id: str) -> None:
        """Clear the history for a specific session."""
        if self._graph is None:
            self._graph = await self.create_graph()

        try:
            # MemorySaver holds state in memory. To "clear", we'd ideally 
            # delete the checkpoint. If adelete isn't available, we log it.
            if hasattr(self._graph, "adelete"):
                await self._graph.adelete(
                    config={"configurable": {"thread_id": session_id}}
                )
            elif hasattr(self._graph, "checkpointer") and hasattr(self._graph.checkpointer, "adelete"):
                 await self._graph.checkpointer.adelete(
                    config={"configurable": {"thread_id": session_id}}
                )
            else:
                logger.warning("clear_chat_history_direct_delete_not_supported")
            
            logger.info("chat_history_cleared", session_id=session_id)
        except Exception as e:
            logger.error("clear_chat_history_failed", error=str(e))

    async def _router_node(self, state: GraphState, config: RunnableConfig):
        """Router node: decides if tool(s) or direct response is needed."""
        messages = prepare_messages(state["messages"], llm=self.llm_service.get_llm())
        
        # We call the LLM to see if it wants to use tools
        # First, load memory and context (if any)
        user_id = state.get("user_id", "guest_user")
        last_msg = messages[-1]
        last_msg_content = getattr(last_msg, "content", str(last_msg))

        # Long-term memory search
        memories = await memory_service.search(query=str(last_msg_content), user_id=user_id)
        
        system_prompt = await load_system_prompt(
            long_term_memory=str(memories),
            retrieved_context="Initial routing phase. Determine if tools are needed."
        )
        
        routing_messages = [{"role": "system", "content": system_prompt}] + messages
        
        response = await self.llm_service.call(routing_messages, config=config)
        
        return {"messages": [response], "long_term_memory": str(memories)}

    def _router_logic(self, state: GraphState):
        """Route based on tool calls in the last message."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tool_call"
        return "final_llm"

    async def _tool_call_node(self, state: GraphState, config: RunnableConfig):
        """Execute tool calls requested by the LLM."""
        last_message = state["messages"][-1]
        tool_outputs = []

        for tool_call in last_message.tool_calls:
            tool = self.tools_by_name.get(tool_call["name"])
            if tool:
                logger.info("executing_tool", tool_name=tool_call["name"])
                observation = await tool.ainvoke(tool_call["args"])
                tool_outputs.append(
                    ToolMessage(
                        content=str(observation),
                        tool_call_id=tool_call["id"]
                    )
                )
            else:
                tool_outputs.append(
                    ToolMessage(
                        content=f"Error: Tool {tool_call['name']} not found.",
                        tool_call_id=tool_call["id"]
                    )
                )
        
        return {"messages": tool_outputs}

    async def _final_llm_node(self, state: GraphState, config: RunnableConfig):
        """Final LLM node: generates the final response using tool results."""
        messages = prepare_messages(state["messages"], llm=self.llm_service.get_llm())
        
        # Collect tool results for context injection
        tool_results = []
        for msg in reversed(state["messages"]):
            if isinstance(msg, ToolMessage):
                tool_results.append(f"Output from tool: {msg.content}")
            elif isinstance(msg, dict) and msg.get("role") == "tool":
                 tool_results.append(f"Output from tool: {msg.get('content')}")
        
        retrieved_context = "\n\n".join(tool_results) if tool_results else "No specific tool data retrieved."
        
        system_prompt = await load_system_prompt(
            long_term_memory=state.get("long_term_memory", "[]"),
            retrieved_context=retrieved_context
        )
        
        final_messages = [{"role": "system", "content": system_prompt}] + messages
        
        response = await self.llm_service.call(final_messages, config=config)
        
        # Save to memory (as per diagram: MongoDB Memory)
        user_id = state.get("user_id", "guest_user")
        last_user_msg = [m for m in messages if isinstance(m, dict) and m.get("role") == "user"]
        if last_user_msg:
             # Just store the user's last query and the current info
             asyncio.create_task(memory_service.add(str(last_user_msg[-1].get("content")), user_id=user_id))

        return {"messages": [response]}

    async def get_response(self, messages: list, session_id: str, user_id: str = "guest_user"):
        """Sync interface for getting agent response."""
        if self._graph is None:
            self._graph = await self.create_graph()
        
        inputs = {"messages": dump_messages(messages, for_llm=True), "user_id": user_id}
        config = {"configurable": {"thread_id": session_id}}
        
        final_state = await self._graph.ainvoke(inputs, config=config)
        return dump_messages(final_state["messages"])

    async def get_stream_response(self, messages: list, session_id: str, user_id: str = "guest_user"):
        """Async generator for streaming agent response."""
        if self._graph is None:
            self._graph = await self.create_graph()
            
        inputs = {"messages": dump_messages(messages, for_llm=True), "user_id": user_id}
        config = {"configurable": {"thread_id": session_id}}

        async for event in self._graph.astream(inputs, config=config, stream_mode="messages"):
            # Normalize event format (some versions return (message, metadata))
            msg = event[0] if isinstance(event, (list, tuple)) else event
            
            if isinstance(msg, AIMessage) and msg.content:
                # Check if this message has tool calls - if so, it's from the router, don't stream to user yet
                if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                    yield msg.content

    async def get_chat_history(self, session_id: str):
        """Retrieve chat history for a session."""
        if self._graph is None:
            self._graph = await self.create_graph()
            
        config = {"configurable": {"thread_id": session_id}}
        state = await self._graph.aget_state(config)
        
        if state and state.values.get("messages"):
            return dump_messages(state.values["messages"])
        return []
