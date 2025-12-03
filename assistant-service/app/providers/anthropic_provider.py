"""
Anthropic (Claude) provider implementation.
"""

import os
import logging
from typing import AsyncIterator, List, Optional

from .base import BaseProvider, ProviderConfig, ChatMessage

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    """Anthropic Claude API provider"""
    
    # Known working models - these are the stable/latest aliases
    KNOWN_MODELS = [
        "claude-sonnet-4-20250514",
        "claude-3-7-sonnet-20250219",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022", 
        "claude-3-opus-20240229",
        "claude-3-haiku-20240307",
    ]
    
    @property
    def name(self) -> str:
        return "anthropic"
    
    @property
    def default_model(self) -> str:
        return "claude-sonnet-4-20250514"
    
    def _get_client(self):
        """Get Anthropic client"""
        from anthropic import AsyncAnthropic
        
        api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        base_url = self.config.base_url or os.environ.get("ANTHROPIC_BASE_URL")
        
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
            
        return AsyncAnthropic(**kwargs)
    
    async def is_available(self) -> bool:
        """Check if Anthropic is configured"""
        api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        return bool(api_key)
    
    async def stream_chat(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Stream chat completion from Anthropic"""
        client = self._get_client()
        model = self.config.model or self.default_model
        
        # Build messages list (Anthropic uses separate system parameter)
        api_messages = []
        for msg in messages:
            api_messages.append({"role": msg.role, "content": msg.content})
        
        try:
            async with client.messages.stream(
                model=model,
                messages=api_messages,
                system=system_prompt or "",
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Anthropic stream error: {e}")
            raise
    
    async def chat(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
    ) -> str:
        """Non-streaming chat completion"""
        client = self._get_client()
        model = self.config.model or self.default_model
        
        api_messages = []
        for msg in messages:
            api_messages.append({"role": msg.role, "content": msg.content})
        
        response = await client.messages.create(
            model=model,
            messages=api_messages,
            system=system_prompt or "",
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
        
        # Extract text from content blocks
        return "".join(
            block.text for block in response.content 
            if hasattr(block, 'text')
        )
    
    async def list_models(self) -> List[str]:
        """List available Anthropic models from the API with pagination"""
        try:
            client = self._get_client()
            
            # Fetch all models with pagination
            # API reference: https://platform.claude.com/docs/en/api/models/list
            chat_models = []
            after_id = None
            
            while True:
                # Build request params
                params = {"limit": 100}
                if after_id:
                    params["after_id"] = after_id
                
                models_response = await client.models.list(**params)
                
                # Process models from this page
                for model in models_response.data:
                    model_id = model.id
                    # Include all Claude models (the API only returns available models)
                    if model_id.startswith('claude'):
                        chat_models.append(model_id)
                
                # Check if there are more pages
                if not models_response.has_more:
                    break
                    
                # Set cursor for next page
                after_id = models_response.last_id
            
            logger.info(f"Fetched {len(chat_models)} Anthropic models from API")
            
            # Sort with newest/best models first
            def sort_key(model_name):
                # Priority by model family (newest first)
                version_priority = 10
                if 'sonnet-4' in model_name or 'claude-4' in model_name:
                    version_priority = 0
                elif '3-7' in model_name or '3.7' in model_name:
                    version_priority = 1
                elif '3-5' in model_name or '3.5' in model_name:
                    version_priority = 2
                elif 'opus' in model_name:
                    version_priority = 3
                elif '3' in model_name:
                    version_priority = 4
                
                # Model type priority (sonnet > haiku > opus for balance)
                type_priority = 5
                if 'sonnet' in model_name:
                    type_priority = 0
                elif 'haiku' in model_name:
                    type_priority = 1
                elif 'opus' in model_name:
                    type_priority = 2
                
                # Get date suffix if present (newer dates first)
                date_suffix = 0
                parts = model_name.split('-')
                for part in reversed(parts):
                    if part.isdigit() and len(part) == 8:
                        date_suffix = int(part)
                        break
                
                return (version_priority, type_priority, -date_suffix, model_name)
            
            chat_models.sort(key=sort_key)
            
            # If API returned models, use them; otherwise fall back
            if chat_models:
                return chat_models
            
            return self.KNOWN_MODELS
            
        except Exception as e:
            logger.warning(f"Failed to list Anthropic models: {e}")
            # Fallback to known working models
            return self.KNOWN_MODELS
