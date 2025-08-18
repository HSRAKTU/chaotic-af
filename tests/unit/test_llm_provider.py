"""Unit tests for LLM providers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agent_framework.core.llm import (
    create_llm_provider, 
    ToolDefinition, 
    LLMResponse,
    OpenAIProvider,
    AnthropicProvider,
    GoogleProvider
)


def test_tool_definition():
    """Test ToolDefinition creation."""
    tool = ToolDefinition(
        name="test_tool",
        description="A test tool",
        parameters={
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            },
            "required": ["input"]
        }
    )
    
    assert tool.name == "test_tool"
    assert tool.description == "A test tool"
    assert "properties" in tool.parameters


def test_create_llm_provider():
    """Test LLM provider factory."""
    # Test OpenAI
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        provider = create_llm_provider("openai", "test-key", "gpt-4")
        assert isinstance(provider, OpenAIProvider)
    
    # Test Anthropic
    provider = create_llm_provider("anthropic", "test-key", "claude-3")
    assert isinstance(provider, AnthropicProvider)
    
    # Test Google
    provider = create_llm_provider("google", "test-key", "gemini-1.5-pro")
    assert isinstance(provider, GoogleProvider)
    
    # Test invalid provider
    with pytest.raises(ValueError):
        create_llm_provider("invalid", "test-key", "model")


@pytest.mark.asyncio
async def test_openai_provider_complete():
    """Test OpenAI provider complete method."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Test response"))
    ]
    
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    provider = OpenAIProvider("test-key", "gpt-4")
    provider.client = mock_client
    
    messages = [{"role": "user", "content": "Hello"}]
    response = await provider.complete(messages)
    
    assert isinstance(response, LLMResponse)
    assert response.content == "Test response"
    assert response.tool_calls is None


@pytest.mark.asyncio
async def test_anthropic_provider_complete():
    """Test Anthropic provider complete method."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Test response")]
    
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    
    provider = AnthropicProvider("test-key", "claude-3")
    provider.client = mock_client
    
    messages = [{"role": "user", "content": "Hello"}]
    response = await provider.complete(messages, temperature=0.5)
    
    assert isinstance(response, LLMResponse)
    assert response.content == "Test response"
    
    # Verify temperature was passed
    mock_client.messages.create.assert_called_once()
    call_args = mock_client.messages.create.call_args[1]
    assert call_args['temperature'] == 0.5


@pytest.mark.asyncio 
async def test_google_provider_complete():
    """Test Google provider complete method."""
    # Mock the generative AI module
    with patch('agent_framework.core.llm.genai') as mock_genai:
        # Mock model instance
        mock_model = MagicMock()
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Test response"
        
        # Setup the mock chain
        mock_chat.send_message.return_value = mock_response
        mock_model.start_chat.return_value = mock_chat
        mock_genai.GenerativeModel.return_value = mock_model
        
        provider = GoogleProvider("test-key", "gemini-1.5-pro")
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]
        
        response = await provider.complete(messages)
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        
        # Verify the combined message was sent
        mock_chat.send_message.assert_called_once()
        sent_message = mock_chat.send_message.call_args[0][0]
        assert "You are helpful" in sent_message
        assert "Hello" in sent_message


def test_llm_response():
    """Test LLMResponse object."""
    response = LLMResponse(content="Hello", tool_calls=None)
    assert response.content == "Hello"
    assert response.tool_calls is None
    
    # With tool calls
    from agent_framework.core.llm import ToolCall
    tool_call = ToolCall(
        id="123",
        tool="test_tool",
        parameters={"input": "test"}
    )
    
    response = LLMResponse(content="", tool_calls=[tool_call])
    assert response.content == ""
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].tool == "test_tool"
