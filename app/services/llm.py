"""LLM service for managing LLM calls with retries and fallback mechanisms."""

import logging
from typing import (
    AsyncIterator,
    List,
    Optional,
)
import os

from langchain_community.chat_models import ChatOllama
from langchain_core.messages import BaseMessage, BaseMessageChunk
from tenacity import (
    before_sleep_log,
    retry,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.logging import logger


class LLMService:
    """Service for managing LLM calls to Ollama."""

    def __init__(self):
        """Initialize the LLM service."""
        self._llm: Optional[ChatOllama] = None
        self._tools: List = []

        # Load Ollama-specific configuration with requested defaults
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Determine which model to use based on configuration
        use_finetuned = os.getenv("USE_FINETUNED_MODEL", "false").lower() == "true"
        finetuned_path = os.getenv("FINETUNED_MODEL_PATH")
        default_model = os.getenv("OLLAMA_MODEL", "dilshaj-ai")
        self.temperature = settings.DEFAULT_LLM_TEMPERATURE
        
        if use_finetuned and finetuned_path:
            # Use local HuggingFace model pipeline (GPU/CPU)
            self.model = finetuned_path
            logger.info("loading_local_model", path=self.model)
            
            try:
                # Lazy import to avoid heavy dependencies if not using local model
                from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
                from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
                import torch

                # Determine device and quantization
                device_map = "auto"
                quantization_config = None
                
                # Check for CUDA availability
                if torch.cuda.is_available():
                    from transformers import BitsAndBytesConfig
                    quantization_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_quant_type="nf4"
                    )
                
                tokenizer = AutoTokenizer.from_pretrained(self.model)
                model = AutoModelForCausalLM.from_pretrained(
                    self.model,
                    device_map=device_map,
                    quantization_config=quantization_config,
                    trust_remote_code=True
                )
                
                pipe = pipeline(
                    "text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    max_new_tokens=2048,
                    temperature=self.temperature,
                    top_p=0.9,
                    repetition_penalty=1.1
                )
                
                hf_pipeline = HuggingFacePipeline(pipeline=pipe)
                self._llm = ChatHuggingFace(llm=hf_pipeline)
                
                logger.info(
                    "llm_service_initialized",
                    provider="local_transformers",
                    model=self.model,
                    device="cuda" if torch.cuda.is_available() else "cpu"
                )

            except ImportError as e:
                logger.critical("missing_dependencies_for_local_llm", error=str(e), hint="Install transformers, torch, accelerate, bitsandbytes")
                raise
            except Exception as e:
                logger.critical("local_llm_initialization_failed", error=str(e))
                raise

        else:
            # Fallback to standard Ollama service
            self.model = default_model
            try:
                self._llm = ChatOllama(
                    base_url=self.base_url,
                    model=self.model,
                    temperature=self.temperature,
                    timeout=settings.LLM_TIMEOUT,
                    keep_alive="5m"
                )
                logger.info(
                    "llm_service_initialized",
                    provider="ollama",
                    model=self.model,
                    base_url=self.base_url
                )
            except Exception as e:
                logger.critical("ollama_initialization_failed", error=str(e), hint="Check if Ollama is running")

    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def call(
        self,
        messages: List[BaseMessage],
        model_name: Optional[str] = None,
        **model_kwargs,
    ) -> BaseMessage:
        """Call the LLM with the specified messages."""
        if not self._llm:
            raise RuntimeError("llm not initialized")

        try:
            response = await self._llm.ainvoke(messages, **model_kwargs)
            logger.debug("llm_call_successful", message_count=len(messages))
            return response
        except Exception as e:
            logger.error("llm_call_failed", error=str(e), exc_info=True)
            raise

    async def astream(
        self,
        messages: List[BaseMessage],
        **model_kwargs,
    ) -> AsyncIterator[BaseMessageChunk]:
        """Stream the LLM response token by token."""
        if not self._llm:
            raise RuntimeError("llm not initialized")

        try:
            async for chunk in self._llm.astream(messages, **model_kwargs):
                yield chunk
        except Exception as e:
            logger.error("llm_stream_failed", error=str(e), exc_info=True)
            raise

    def get_llm(self) -> Optional[ChatOllama]:
        """Get the current LLM instance."""
        return self._llm

    def bind_tools(self, tools: List) -> "LLMService":
        """Bind tools to the current LLM."""
        self._tools = tools
        if self._llm:
            try:
                self._llm = self._llm.bind_tools(tools)
                logger.debug("tools_bound_to_llm", tool_count=len(tools))
            except Exception as e:
                 logger.warning("failed_to_bind_tools_to_ollama", error=str(e))
        return self


# Create global LLM service instance
llm_service = LLMService()
