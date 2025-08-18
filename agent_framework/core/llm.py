"""LLM abstraction layer with universal tool calling support.

Requirements:
- Support OpenAI, Anthropic, Google LLMs
- Enable tool calling for ANY model (including GPT-3, Claude-1)
- Parse tool calls from responses
- Handle both native and prompt-based tool calling
- Structured logging of LLM interactions
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
import asyncio

# LLM client imports
try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None


@dataclass
class ToolDefinition:
    """Definition of a tool available to the LLM."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema


@dataclass
class ToolCall:
    """A tool call requested by the LLM."""
    tool: str
    parameters: Dict[str, Any]
    id: Optional[str] = None


@dataclass
class LLMResponse:
    """Response from an LLM, potentially containing tool calls."""
    content: str
    tool_calls: List[ToolCall]
    reasoning: Optional[str] = None  # For models that support CoT
    raw_response: Optional[Any] = None  # Original API response


class LLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.supports_native_tools = self._check_native_tool_support()
    
    @abstractmethod
    def _check_native_tool_support(self) -> bool:
        """Check if this model supports native function calling."""
        pass
    
    @abstractmethod
    async def complete(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7
    ) -> LLMResponse:
        """Complete a conversation, potentially with tool calls."""
        pass
    
    def _build_tool_use_prompt(self, tools: List[ToolDefinition]) -> str:
        """Build prompt that teaches LLM to use tools (for older models)."""
        tool_descriptions = []
        
        for tool in tools:
            params_str = json.dumps(tool.parameters, indent=2)
            tool_descriptions.append(
                f"{tool.name}: {tool.description}\n"
                f"Parameters:\n{params_str}"
            )
        
        return f"""You have access to the following tools:

{chr(10).join(tool_descriptions)}

To use a tool, respond with a special XML tag:
<tool_use>
{{"tool": "tool_name", "parameters": {{"param1": "value1"}}}}
</tool_use>

You can use multiple tools by including multiple <tool_use> tags.
After using a tool, wait for the result before continuing your response.

Important: Always use tools when they would help answer the user's request."""

    def _parse_tool_calls(self, content: str) -> Tuple[str, List[ToolCall]]:
        """Parse tool calls from LLM response (for older models)."""
        tool_calls = []
        
        # Find all tool_use XML tags
        pattern = r'<tool_use>(.*?)</tool_use>'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            try:
                tool_data = json.loads(match.group(1).strip())
                tool_calls.append(ToolCall(
                    tool=tool_data["tool"],
                    parameters=tool_data.get("parameters", {})
                ))
            except json.JSONDecodeError:
                # Skip malformed tool calls
                continue
        
        # Remove tool_use tags from content
        clean_content = re.sub(pattern, '', content).strip()
        
        return clean_content, tool_calls


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider (GPT-3.5, GPT-4, etc)."""
    
    def __init__(self, api_key: str, model: str):
        if not openai:
            raise ImportError("openai package not installed. Run: pip install openai")
        super().__init__(api_key, model)
        self.client = openai.AsyncOpenAI(api_key=api_key)
    
    def _check_native_tool_support(self) -> bool:
        """GPT-3.5-turbo and GPT-4 support native function calling."""
        return "gpt-3.5-turbo" in self.model or "gpt-4" in self.model
    
    async def complete(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7
    ) -> LLMResponse:
        """Complete with OpenAI API."""
        
        # Prepare messages
        api_messages = messages.copy()
        
        if tools and not self.supports_native_tools:
            # Add tool use prompt for older models
            tool_prompt = self._build_tool_use_prompt(tools)
            api_messages.insert(0, {"role": "system", "content": tool_prompt})
        
        # Prepare request
        kwargs = {
            "model": self.model,
            "messages": api_messages,
            "temperature": temperature
        }
        
        # Add native tools if supported
        if tools and self.supports_native_tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters
                    }
                }
                for tool in tools
            ]
        
        # Make API call
        response = await self.client.chat.completions.create(**kwargs)
        
        # Parse response
        message = response.choices[0].message
        content = message.content or ""
        tool_calls = []
        
        if self.supports_native_tools and message.tool_calls:
            # Native tool calls
            for tc in message.tool_calls:
                tool_calls.append(ToolCall(
                    tool=tc.function.name,
                    parameters=json.loads(tc.function.arguments),
                    id=tc.id
                ))
        else:
            # Parse tool calls from content
            content, tool_calls = self._parse_tool_calls(content)
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            raw_response=response
        )


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider (Claude family)."""
    
    def __init__(self, api_key: str, model: str):
        if not anthropic:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
        super().__init__(api_key, model)
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    def _check_native_tool_support(self) -> bool:
        """Claude 3 models support native tool use."""
        return "claude-3" in self.model
    
    async def complete(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7
    ) -> LLMResponse:
        """Complete with Anthropic API."""
        
        # Convert messages to Anthropic format
        system_message = ""
        api_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message += msg["content"] + "\n"
            else:
                api_messages.append({
                    "role": msg["role"] if msg["role"] != "user" else "user",
                    "content": msg["content"]
                })
        
        # Add tool use prompt for older models
        if tools and not self.supports_native_tools:
            system_message += "\n" + self._build_tool_use_prompt(tools)
        
        # Prepare request
        kwargs = {
            "model": self.model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": 4096
        }
        
        if system_message:
            kwargs["system"] = system_message.strip()
        
        # Add native tools if supported
        if tools and self.supports_native_tools:
            kwargs["tools"] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.parameters
                }
                for tool in tools
            ]
        
        # Make API call
        response = await self.client.messages.create(**kwargs)
        
        # Parse response
        content = ""
        tool_calls = []
        
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    tool=block.name,
                    parameters=block.input,
                    id=block.id
                ))
        
        # Parse tool calls from content if no native calls
        if not tool_calls and tools:
            content, tool_calls = self._parse_tool_calls(content)
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            raw_response=response
        )


class GoogleProvider(LLMProvider):
    """Google AI (Gemini) LLM provider."""
    
    def __init__(self, api_key: str, model: str):
        if not genai:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")
        super().__init__(api_key, model)
        genai.configure(api_key=api_key)
        # Don't create model instance here - we'll create it with tools in complete()
    
    def _check_native_tool_support(self) -> bool:
        """Gemini models support native function calling."""
        return "gemini" in self.model.lower()
    
    async def complete(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7
    ) -> LLMResponse:
        """Complete with Google AI API."""
        
        # Convert messages to Gemini format
        chat_history = []
        
        for msg in messages:
            if msg["role"] == "system":
                # Gemini doesn't have system role, prepend to first user message
                if not chat_history:
                    chat_history.append({
                        "role": "user",
                        "parts": [msg["content"]]
                    })
            elif msg["role"] == "user":
                if chat_history and chat_history[0].get("role") == "user" and len(chat_history) == 1:
                    # Append to system message
                    chat_history[0]["parts"].append("\n\nUser: " + msg["content"])
                else:
                    chat_history.append({
                        "role": "user",
                        "parts": [msg["content"]]
                    })
            elif msg["role"] == "assistant":
                chat_history.append({
                    "role": "model",
                    "parts": [msg["content"]]
                })

        
        # Configure generation settings
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": 4096,
        }
        
        # Create model with or without tools
        if tools and self.supports_native_tools:
            # Convert tools to Gemini format
            functions = []
            for tool in tools:
                functions.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                })
            
            # Create model WITH tools
            model_instance = genai.GenerativeModel(
                self.model,
                tools=[{"function_declarations": functions}]
            )
        else:
            # Create model without tools
            model_instance = genai.GenerativeModel(self.model)
            
            # Add tool prompt if needed
            if tools and not self.supports_native_tools:
                tool_prompt = self._build_tool_use_prompt(tools)
                if chat_history and chat_history[0]["role"] == "user":
                    chat_history[0]["parts"].insert(0, tool_prompt + "\n\n")
        
        # Create chat and send message
        chat = model_instance.start_chat(
            history=chat_history[:-1] if chat_history else [],
            enable_automatic_function_calling=False
        )
        
        # For Gemini, when we have a combined message, send all parts
        if chat_history and chat_history[-1]["parts"]:
            message_to_send = "\n".join(chat_history[-1]["parts"])
        else:
            message_to_send = ""
        
        response = await asyncio.to_thread(
            chat.send_message,
            message_to_send,
            generation_config=generation_config
        )
        
        # Parse response - check for function calls FIRST
        tool_calls = []
        content = ""
        
        # Check for function calls in response
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call'):
                        fc = part.function_call
                        # Only add tool call if it has a name
                        if fc.name:
                            # fc.args can be None if no parameters
                            args = dict(fc.args) if fc.args else {}
                            tool_calls.append(ToolCall(
                                tool=fc.name,
                                parameters=args
                            ))
                    elif hasattr(part, 'text'):
                        content += part.text
        
        # If no content was extracted and no tool calls, try response.text
        if not content and not tool_calls:
            try:
                content = response.text
            except ValueError:
                # response.text fails when there's only a function call
                pass
        
        # If no native tool calls, try parsing from content
        if not tool_calls and tools and content:
            content, tool_calls = self._parse_tool_calls(content)
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            raw_response=response
        )


def create_llm_provider(provider: str, api_key: str, model: str) -> LLMProvider:
    """Factory function to create LLM providers."""
    
    if provider == "openai":
        return OpenAIProvider(api_key, model)
    elif provider == "anthropic":
        return AnthropicProvider(api_key, model)
    elif provider == "google":
        return GoogleProvider(api_key, model)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
