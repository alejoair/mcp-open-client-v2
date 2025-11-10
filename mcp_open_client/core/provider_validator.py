"""
AI provider validation and testing service.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import aiohttp
from ..api.models.provider import ProviderConfig, ModelConfig


@dataclass
class ValidationResult:
    """Result of provider validation."""
    
    success: bool
    provider_name: str
    response_time_ms: Optional[float] = None
    available_models: Optional[List[str]] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class ModelTestResult:
    """Result of model testing."""
    
    success: bool
    provider_name: str
    model_name: str
    response_time_ms: Optional[float] = None
    test_response: Optional[str] = None
    error_message: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None


class AIProviderValidator:
    """
    Service for validating and testing AI provider connections.
    """
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
    
    async def validate_provider(self, config: ProviderConfig, model_name: Optional[str] = None) -> ValidationResult:
        """
        Validate a provider connection and optionally test a specific model.
        
        Args:
            config: Provider configuration
            model_name: Optional specific model to test
            
        Returns:
            ValidationResult with validation details
        """
        start_time = time.time()
        
        try:
            # Determine provider type and validation method
            provider_type = self._detect_provider_type(config.base_url, config.name)
            
            if provider_type == "openai":
                result = await self._validate_openai_provider(config, model_name)
            elif provider_type == "anthropic":
                result = await self._validate_anthropic_provider(config, model_name)
            elif provider_type == "cerebras":
                result = await self._validate_cerebras_provider(config, model_name)
            elif provider_type == "openrouter":
                result = await self._validate_openrouter_provider(config, model_name)
            else:
                result = await self._validate_generic_provider(config, model_name)
            
            # Calculate response time
            end_time = time.time()
            result.response_time_ms = (end_time - start_time) * 1000
            result.provider_name = config.name
            
            return result
            
        except asyncio.TimeoutError:
            return ValidationResult(
                success=False,
                provider_name=config.name,
                response_time_ms=self.timeout * 1000,
                error_message=f"Validation timed out after {self.timeout} seconds"
            )
        except Exception as e:
            end_time = time.time()
            return ValidationResult(
                success=False,
                provider_name=config.name,
                response_time_ms=(end_time - start_time) * 1000,
                error_message=f"Validation failed: {str(e)}"
            )
    
    async def test_model(self, config: ProviderConfig, model_name: str, test_message: str = "Hello, this is a test.") -> ModelTestResult:
        """
        Test a specific model with a simple message.
        
        Args:
            config: Provider configuration
            model_name: Model to test
            test_message: Test message to send
            
        Returns:
            ModelTestResult with test details
        """
        start_time = time.time()
        
        try:
            provider_type = self._detect_provider_type(config.base_url, config.name)
            
            if provider_type == "openai":
                result = await self._test_openai_model(config, model_name, test_message)
            elif provider_type == "anthropic":
                result = await self._test_anthropic_model(config, model_name, test_message)
            elif provider_type == "cerebras":
                result = await self._test_cerebras_model(config, model_name, test_message)
            elif provider_type == "openrouter":
                result = await self._test_openrouter_model(config, model_name, test_message)
            else:
                result = await self._test_generic_model(config, model_name, test_message)
            
            # Calculate response time
            end_time = time.time()
            result.response_time_ms = (end_time - start_time) * 1000
            result.provider_name = config.name
            
            return result
            
        except asyncio.TimeoutError:
            return ModelTestResult(
                success=False,
                provider_name=config.name,
                model_name=model_name,
                response_time_ms=self.timeout * 1000,
                error_message=f"Model test timed out after {self.timeout} seconds"
            )
        except Exception as e:
            end_time = time.time()
            return ModelTestResult(
                success=False,
                provider_name=config.name,
                model_name=model_name,
                response_time_ms=(end_time - start_time) * 1000,
                error_message=f"Model test failed: {str(e)}"
            )
    
    def _detect_provider_type(self, base_url: str, name: str) -> str:
        """
        Detect the provider type based on URL and name.
        
        Args:
            base_url: Provider base URL
            name: Provider name
            
        Returns:
            Provider type string
        """
        base_url_lower = base_url.lower()
        name_lower = name.lower()
        
        if "openai.com" in base_url_lower or "openai" in name_lower:
            return "openai"
        elif "anthropic.com" in base_url_lower or "anthropic" in name_lower:
            return "anthropic"
        elif "cerebras.ai" in base_url_lower or "cerebras" in name_lower:
            return "cerebras"
        elif "openrouter.ai" in base_url_lower or "openrouter" in name_lower:
            return "openrouter"
        else:
            return "generic"
    
    async def _validate_openai_provider(self, config: ProviderConfig, model_name: Optional[str] = None) -> ValidationResult:
        """Validate OpenAI provider."""
        headers = {"Authorization": f"Bearer {config.api_key}"}
        
        async with aiohttp.ClientSession() as session:
            # List models to validate connection
            async with session.get(f"{config.base_url}models", headers=headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                if response.status == 200:
                    data = await response.json()
                    available_models = [model["id"] for model in data.get("data", [])]
                    
                    # If specific model requested, check if it exists
                    if model_name and model_name not in available_models:
                        return ValidationResult(
                            success=False,
                            provider_name=config.name,
                            error_message=f"Model '{model_name}' not found in available models"
                        )
                    
                    return ValidationResult(
                        success=True,
                        provider_name=config.name,
                        available_models=available_models,
                        details={"total_models": len(available_models)}
                    )
                else:
                    error_text = await response.text()
                    return ValidationResult(
                        success=False,
                        provider_name=config.name,
                        error_message=f"OpenAI API error (status {response.status}): {error_text}"
                    )
    
    async def _validate_anthropic_provider(self, config: ProviderConfig, model_name: Optional[str] = None) -> ValidationResult:
        """Validate Anthropic provider."""
        headers = {
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Anthropic doesn't have a models endpoint, so we send a minimal message
        test_payload = {
            "model": model_name or "claude-3-haiku-20240307",
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "test"}]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{config.base_url}messages", 
                                   headers=headers, 
                                   json=test_payload,
                                   timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                
                if response.status == 200:
                    # Anthropic is valid if we get a successful response
                    known_models = [
                        "claude-3-opus-20240229",
                        "claude-3-sonnet-20240229", 
                        "claude-3-haiku-20240307",
                        "claude-2.1",
                        "claude-2.0",
                        "claude-instant-1.2"
                    ]
                    
                    return ValidationResult(
                        success=True,
                        provider_name=config.name,
                        available_models=known_models,
                        details={"validated_model": test_payload["model"]}
                    )
                else:
                    error_text = await response.text()
                    return ValidationResult(
                        success=False,
                        provider_name=config.name,
                        error_message=f"Anthropic API error (status {response.status}): {error_text}"
                    )
    
    async def _validate_cerebras_provider(self, config: ProviderConfig, model_name: Optional[str] = None) -> ValidationResult:
        """Validate Cerebras provider."""
        headers = {"Authorization": f"Bearer {config.api_key}"}
        
        async with aiohttp.ClientSession() as session:
            # Try to list models first
            async with session.get(f"{config.base_url}models", headers=headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                if response.status == 200:
                    data = await response.json()
                    available_models = [model["id"] for model in data.get("data", [])]
                    
                    if model_name and model_name not in available_models:
                        return ValidationResult(
                            success=False,
                            provider_name=config.name,
                            error_message=f"Model '{model_name}' not found"
                        )
                    
                    return ValidationResult(
                        success=True,
                        provider_name=config.name,
                        available_models=available_models
                    )
                else:
                    # Try alternative endpoint or simple model test
                    test_model = model_name or "llama3.1-8b"
                    test_payload = {
                        "model": test_model,
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 5
                    }
                    
                    async with session.post(f"{config.base_url}chat/completions",
                                           headers=headers,
                                           json=test_payload,
                                           timeout=aiohttp.ClientTimeout(total=self.timeout)) as chat_response:
                        
                        if chat_response.status == 200:
                            return ValidationResult(
                                success=True,
                                provider_name=config.name,
                                available_models=[test_model],
                                details={"validated_model": test_model}
                            )
                        else:
                            error_text = await chat_response.text()
                            return ValidationResult(
                                success=False,
                                provider_name=config.name,
                                error_message=f"Cerebras API error (status {chat_response.status}): {error_text}"
                            )
    
    async def _validate_openrouter_provider(self, config: ProviderConfig, model_name: Optional[str] = None) -> ValidationResult:
        """Validate OpenRouter provider."""
        headers = {"Authorization": f"Bearer {config.api_key}"}
        
        async with aiohttp.ClientSession() as session:
            # List models
            async with session.get(f"{config.base_url}models", headers=headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                if response.status == 200:
                    data = await response.json()
                    available_models = [model["id"] for model in data.get("data", [])]
                    
                    if model_name and model_name not in available_models:
                        return ValidationResult(
                            success=False,
                            provider_name=config.name,
                            error_message=f"Model '{model_name}' not found"
                        )
                    
                    return ValidationResult(
                        success=True,
                        provider_name=config.name,
                        available_models=available_models,
                        details={"total_models": len(available_models)}
                    )
                else:
                    error_text = await response.text()
                    return ValidationResult(
                        success=False,
                        provider_name=config.name,
                        error_message=f"OpenRouter API error (status {response.status}): {error_text}"
                    )
    
    async def _validate_generic_provider(self, config: ProviderConfig, model_name: Optional[str] = None) -> ValidationResult:
        """Validate generic OpenAI-compatible provider."""
        headers = {"Authorization": f"Bearer {config.api_key}"}
        
        async with aiohttp.ClientSession() as session:
            # Try OpenAI-compatible models endpoint
            try:
                async with session.get(f"{config.base_url}models", headers=headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                    if response.status == 200:
                        data = await response.json()
                        available_models = [model["id"] for model in data.get("data", [])]
                        
                        if model_name and model_name not in available_models:
                            return ValidationResult(
                                success=False,
                                provider_name=config.name,
                                error_message=f"Model '{model_name}' not found"
                            )
                        
                        return ValidationResult(
                            success=True,
                            provider_name=config.name,
                            available_models=available_models,
                            details={"api_format": "openai-compatible"}
                        )
                    else:
                        # Try a simple chat completion test
                        test_model = model_name or "gpt-3.5-turbo"
                        test_payload = {
                            "model": test_model,
                            "messages": [{"role": "user", "content": "test"}],
                            "max_tokens": 1
                        }
                        
                        async with session.post(f"{config.base_url}chat/completions",
                                               headers=headers,
                                               json=test_payload,
                                               timeout=aiohttp.ClientTimeout(total=self.timeout)) as chat_response:
                            
                            if chat_response.status == 200:
                                return ValidationResult(
                                    success=True,
                                    provider_name=config.name,
                                    available_models=[test_model],
                                    details={"validated_model": test_model, "api_format": "openai-compatible"}
                                )
                            else:
                                error_text = await chat_response.text()
                                return ValidationResult(
                                    success=False,
                                    provider_name=config.name,
                                    error_message=f"Generic provider API error (status {chat_response.status}): {error_text}"
                                )
            except Exception as e:
                return ValidationResult(
                    success=False,
                    provider_name=config.name,
                    error_message=f"Generic provider validation failed: {str(e)}"
                )
    
    async def _test_openai_model(self, config: ProviderConfig, model_name: str, test_message: str) -> ModelTestResult:
        """Test OpenAI model."""
        headers = {"Authorization": f"Bearer {config.api_key}"}
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": test_message}],
            "max_tokens": 50
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{config.base_url}chat/completions", 
                                   headers=headers, 
                                   json=payload,
                                   timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                
                if response.status == 200:
                    data = await response.json()
                    choice = data.get("choices", [{}])[0]
                    message = choice.get("message", {}).get("content", "")
                    usage = data.get("usage", {})
                    
                    return ModelTestResult(
                        success=True,
                        provider_name=config.name,
                        model_name=model_name,
                        test_response=message,
                        token_usage={
                            "prompt_tokens": usage.get("prompt_tokens", 0),
                            "completion_tokens": usage.get("completion_tokens", 0),
                            "total_tokens": usage.get("total_tokens", 0)
                        }
                    )
                else:
                    error_text = await response.text()
                    return ModelTestResult(
                        success=False,
                        provider_name=config.name,
                        model_name=model_name,
                        error_message=f"OpenAI API error (status {response.status}): {error_text}"
                    )
    
    async def _test_anthropic_model(self, config: ProviderConfig, model_name: str, test_message: str) -> ModelTestResult:
        """Test Anthropic model."""
        headers = {
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": model_name,
            "max_tokens": 50,
            "messages": [{"role": "user", "content": test_message}]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{config.base_url}messages", 
                                   headers=headers, 
                                   json=payload,
                                   timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                
                if response.status == 200:
                    data = await response.json()
                    message = data.get("content", [{}])[0].get("text", "")
                    usage = data.get("usage", {})
                    
                    return ModelTestResult(
                        success=True,
                        provider_name=config.name,
                        model_name=model_name,
                        test_response=message,
                        token_usage={
                            "input_tokens": usage.get("input_tokens", 0),
                            "output_tokens": usage.get("output_tokens", 0)
                        }
                    )
                else:
                    error_text = await response.text()
                    return ModelTestResult(
                        success=False,
                        provider_name=config.name,
                        model_name=model_name,
                        error_message=f"Anthropic API error (status {response.status}): {error_text}"
                    )
    
    async def _test_cerebras_model(self, config: ProviderConfig, model_name: str, test_message: str) -> ModelTestResult:
        """Test Cerebras model."""
        return await self._test_openai_model(config, model_name, test_message)  # Same format as OpenAI
    
    async def _test_openrouter_model(self, config: ProviderConfig, model_name: str, test_message: str) -> ModelTestResult:
        """Test OpenRouter model."""
        return await self._test_openai_model(config, model_name, test_message)  # Same format as OpenAI
    
    async def _test_generic_model(self, config: ProviderConfig, model_name: str, test_message: str) -> ModelTestResult:
        """Test generic OpenAI-compatible model."""
        return await self._test_openai_model(config, model_name, test_message)  # Same format as OpenAI