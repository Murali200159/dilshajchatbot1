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
                graph_builder.add_node("chat", self._chat)
                graph_builder.add_node("tool_call", self._tool_call)
                
                graph_builder.set_entry_point("chat")
                
                # Edges
                # Note: 'chat' handles its own conditional transition via Command(goto)
                # but we still need a default edge from tool_call back to chat
                graph_builder.add_edge("tool_call", "chat")

                # ✅ CHANGED: Use MemorySaver instead of PostgresSaver
                checkpointer = MemorySaver()

                self._graph = graph_builder.compile(
                    checkpointer=checkpointer,
                    name=f"{settings.PROJECT_NAME} Agent ({settings.ENVIRONMENT.value})",
                )

                logger.info(
                    "graph_created",
                    graph_name=f"{settings.PROJECT_NAME} Agent",
                    environment=settings.ENVIRONMENT.value,
                    has_checkpointer=True,
                )

            except Exception as e:
                logger.error("graph_creation_failed", error=str(e))
                raise e

        return self._graph

    # ❌ REMOVED: clear_chat_history Postgres delete logic
    async def clear_chat_history(self, session_id: str) -> None:
        if self._graph is None:
            self._graph = await self.create_graph()

        try:
            await self._graph.adelete(
                config={"configurable": {"thread_id": session_id}}
            )
            logger.info("chat_history_cleared", session_id=session_id)
        except Exception as e:
            logger.error("Failed to clear chat history", error=str(e))
            raise

    async def _chat(self, state: GraphState, config: RunnableConfig):
        """Chat node for processing messages through the LLM."""
        messages = prepare_messages(state["messages"], llm=self.llm_service.get_llm())
        
        # Load system prompt with memory context
        user_id = state.get("user_id", "guest_user")
        memories = await memory_service.search(query=str(messages[-1]["content"]), user_id=user_id)
        
        # Extract tool results to inject as context
        tool_results = []
        for msg in state["messages"]:
            # Handle both class instances and dictionaries
            if isinstance(msg, ToolMessage):
                tool_results.append(f"Output from tool: {msg.content}")
            elif isinstance(msg, dict):
                # Role 'tool' is used for tool outputs
                if msg.get("role") == "tool" or msg.get("type") == "tool":
                    tool_results.append(f"Output from tool: {msg.get('content')}")
        
        if tool_results:
            retrieved_context = "CRITICAL METADATA FROM INTERNAL TOOLS:\n" + "\n\n".join(tool_results)
        else:
            retrieved_context = "No internal document context retrieved yet. You should use company_docs_tool if you need company-specific info."
        
        system_prompt = await load_system_prompt(
            long_term_memory=str(memories),
            retrieved_context=retrieved_context
        )
        
        messages = [{"role": "system", "content": system_prompt}] + messages

        # Add to long term memory asynchronously
        await memory_service.add(messages[-1]["content"], user_id=user_id)

        try:
            with llm_inference_duration_seconds.labels(
                model=settings.DEFAULT_LLM_MODEL
            ).time():
                # Pass config to allow LangGraph to handle callbacks/streaming
                response = await self.llm_service.call(messages, config=config)
            
            parsed_response = process_llm_response(response)
            
            # Determine if we need to call tools
            if response.tool_calls:
                return Command(
                    update={"messages": [response]},
                    goto="tool_call"
                )
            
            return {"messages": [response]}
        except Exception as e:
            logger.error("chat_node_failed", error=str(e))
            raise

    async def _tool_call(self, state: GraphState, config: RunnableConfig):
        """Execute tool calls requested by the LLM."""
        last_message = state["messages"][-1]
        tool_outputs = []

        for tool_call in last_message.tool_calls:
            tool = self.tools_by_name.get(tool_call["name"])
            if tool:
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
            if isinstance(event[0], AIMessage) and event[0].content:
                yield event[0].content

    async def get_chat_history(self, session_id: str):
        """Retrieve chat history for a session."""
        if self._graph is None:
            self._graph = await self.create_graph()
            
        config = {"configurable": {"thread_id": session_id}}
        state = await self._graph.aget_state(config)
        
        if state and state.values.get("messages"):
            return dump_messages(state.values["messages"])
        return []
