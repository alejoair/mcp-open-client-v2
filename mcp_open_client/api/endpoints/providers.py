"""
FastAPI endpoints for AI provider management.
"""

from typing import Dict

from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import JSONResponse

from ...core.providers import AIProviderManager
from ...exceptions import MCPError
from ..models.provider import (
    ModelConfig,
    ModelDeleteResponse,
    ModelListResponse,
    ModelSetRequest,
    ModelSetResponse,
    ModelTestRequest,
    ModelTestResponse,
    ProviderConfig,
    ProviderConfigResponse,
    ProviderCreateRequest,
    ProviderCreateResponse,
    ProviderDeleteResponse,
    ProviderListResponse,
    ProviderTestRequest,
    ProviderTestResponse,
    ProviderUpdateRequest,
    ProviderUpdateResponse,
)

# Create router
router = APIRouter(prefix="/providers", tags=["AI Providers"])

# Global provider manager instance
provider_manager = AIProviderManager()


@router.post(
    "/",
    response_model=ProviderCreateResponse,
    status_code=201,
    operation_id="provider_create",
)
async def create_provider(request: ProviderCreateRequest):
    """
    Create a new AI provider configuration.
    """
    try:
        return await provider_manager.add_provider(request.provider)
    except MCPError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/", response_model=ProviderListResponse, operation_id="provider_list_all")
async def list_providers():
    """
    List all configured AI providers.
    """
    try:
        return provider_manager.get_all_providers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get(
    "/{provider_id}", response_model=ProviderCreateResponse, operation_id="provider_get"
)
async def get_provider(provider_id: str = Path(..., description="Provider ID")):
    """
    Get a specific AI provider configuration.
    """
    try:
        provider = provider_manager.get_provider(provider_id)
        if not provider:
            raise HTTPException(
                status_code=404, detail=f"Provider with ID '{provider_id}' not found"
            )

        return ProviderCreateResponse(
            success=True, provider=provider, message="Provider found"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.put(
    "/{provider_id}",
    response_model=ProviderUpdateResponse,
    operation_id="provider_update",
)
async def update_provider(
    provider_id: str = Path(..., description="Provider ID"),
    request: ProviderCreateRequest = None,
):
    """
    Update an entire AI provider configuration.
    """
    try:
        return await provider_manager.update_provider(provider_id, request.provider)
    except MCPError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.patch(
    "/{provider_id}",
    response_model=ProviderUpdateResponse,
    operation_id="provider_partial_update",
)
async def partial_update_provider(
    provider_id: str = Path(..., description="Provider ID"),
    request: ProviderUpdateRequest = None,
):
    """
    Partially update an AI provider configuration.
    """
    try:
        provider = provider_manager.get_provider(provider_id)
        if not provider:
            raise HTTPException(
                status_code=404, detail=f"Provider with ID '{provider_id}' not found"
            )

        # Create updated config by merging existing and new values
        current_config = provider.config
        updated_config_data = current_config.model_dump()

        # Update only provided fields
        update_data = request.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "models" and value is not None:
                # For models, merge the dictionaries
                current_models = updated_config_data[key]
                if current_models:
                    if value.get("small"):
                        current_models["small"] = value["small"]
                    if value.get("main"):
                        current_models["main"] = value["main"]
                else:
                    updated_config_data[key] = value
            else:
                updated_config_data[key] = value

        updated_config = ProviderConfig(**updated_config_data)

        return await provider_manager.update_provider(provider_id, updated_config)
    except HTTPException:
        raise
    except MCPError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.delete(
    "/{provider_id}",
    response_model=ProviderDeleteResponse,
    operation_id="provider_delete",
)
async def delete_provider(provider_id: str = Path(..., description="Provider ID")):
    """
    Delete an AI provider configuration.
    """
    try:
        return await provider_manager.delete_provider(provider_id)
    except MCPError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# Model management endpoints
@router.get(
    "/{provider_id}/models",
    response_model=ModelListResponse,
    operation_id="provider_list_models",
)
async def list_provider_models(provider_id: str = Path(..., description="Provider ID")):
    """
    Get small and main models for a specific provider.
    """
    try:
        return provider_manager.get_provider_models(provider_id)
    except MCPError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.post(
    "/{provider_id}/models/{model_type}",
    response_model=ModelSetResponse,
    status_code=201,
    operation_id="provider_set_model",
)
async def set_provider_model(
    provider_id: str = Path(..., description="Provider ID"),
    model_type: str = Path(..., description="Model type: 'small' or 'main'"),
    request: ModelConfig = None,
):
    """
    Set a small or main model for a provider.
    """
    try:
        if model_type not in ["small", "main"]:
            raise HTTPException(
                status_code=400, detail=f"Model type must be 'small' or 'main'"
            )

        return await provider_manager.set_model(provider_id, model_type, request)
    except MCPError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/{provider_id}/models/{model_type}", operation_id="provider_get_model")
async def get_provider_model(
    provider_id: str = Path(..., description="Provider ID"),
    model_type: str = Path(..., description="Model type: 'small' or 'main'"),
):
    """
    Get a specific model configuration (small or main).
    """
    try:
        if model_type not in ["small", "main"]:
            raise HTTPException(
                status_code=400, detail=f"Model type must be 'small' or 'main'"
            )

        provider = provider_manager.get_provider(provider_id)
        if not provider:
            raise HTTPException(
                status_code=404, detail=f"Provider with ID '{provider_id}' not found"
            )

        model_config = None
        if model_type == "small":
            model_config = provider.config.models.small
        else:  # model_type == 'main'
            model_config = provider.config.models.main

        if not model_config:
            raise HTTPException(
                status_code=404, detail=f"No {model_type} model configured for provider"
            )

        return {
            "success": True,
            "model_type": model_type,
            "model_config": model_config.model_dump(),
            "provider_id": provider_id,
            "message": f"{model_type.capitalize()} model found",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.delete(
    "/{provider_id}/models/{model_type}",
    response_model=ModelDeleteResponse,
    operation_id="provider_delete_model",
)
async def delete_provider_model(
    provider_id: str = Path(..., description="Provider ID"),
    model_type: str = Path(..., description="Model type: 'small' or 'main'"),
):
    """
    Remove a small or main model from a provider.
    """
    try:
        if model_type not in ["small", "main"]:
            raise HTTPException(
                status_code=400, detail=f"Model type must be 'small' or 'main'"
            )

        return await provider_manager.remove_model(provider_id, model_type)
    except MCPError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# Control endpoints
@router.post("/{provider_id}/enable", operation_id="provider_enable")
async def enable_provider(provider_id: str = Path(..., description="Provider ID")):
    """
    Enable a provider.
    """
    try:
        await provider_manager.enable_provider(provider_id)
        return {
            "success": True,
            "message": f"Provider '{provider_id}' enabled successfully",
        }
    except MCPError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.post("/{provider_id}/disable", operation_id="provider_disable")
async def disable_provider(provider_id: str = Path(..., description="Provider ID")):
    """
    Disable a provider.
    """
    try:
        await provider_manager.disable_provider(provider_id)
        return {
            "success": True,
            "message": f"Provider '{provider_id}' disabled successfully",
        }
    except MCPError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.post("/{provider_id}/set-default", operation_id="provider_set_default")
async def set_default_provider(provider_id: str = Path(..., description="Provider ID")):
    """
    Set a provider as the default.
    """
    try:
        await provider_manager.set_default_provider(provider_id)
        return {
            "success": True,
            "message": f"Provider '{provider_id}' set as default successfully",
        }
    except MCPError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# Global configuration endpoints
@router.get(
    "/config/global",
    response_model=ProviderConfigResponse,
    operation_id="provider_get_global_config",
)
async def get_global_config():
    """
    Get global provider configuration.
    """
    try:
        return provider_manager.get_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/default/current", operation_id="provider_get_default")
async def get_default_provider():
    """
    Get the current default provider.
    """
    try:
        provider = provider_manager.get_default_provider()
        if not provider:
            return {
                "success": True,
                "default_provider": None,
                "message": "No default provider set",
            }

        return {
            "success": True,
            "default_provider": {
                "id": provider.id,
                "name": provider.config.name,
                "enabled": provider.enabled,
            },
            "message": "Default provider found",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# Testing endpoints (placeholder for now)
@router.post(
    "/{provider_id}/test",
    response_model=ProviderTestResponse,
    operation_id="provider_test",
)
async def test_provider(
    provider_id: str = Path(..., description="Provider ID"),
    request: ProviderTestRequest = None,
):
    """
    Test a provider connection.
    """
    try:
        provider = provider_manager.get_provider(provider_id)
        if not provider:
            raise HTTPException(
                status_code=404, detail=f"Provider with ID '{provider_id}' not found"
            )

        # Use the actual validation service
        validation_result = await provider_manager.validate_provider(
            provider_id, request.model_name if request else None
        )

        return ProviderTestResponse(
            success=validation_result.success,
            provider_id=provider_id,
            model_name=request.model_name if request else None,
            response_time_ms=validation_result.response_time_ms,
            available_models=validation_result.available_models,
            error_message=validation_result.error_message,
            message=(
                "Provider test completed successfully"
                if validation_result.success
                else "Provider test failed"
            ),
        )
    except HTTPException:
        raise
    except MCPError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        return ProviderTestResponse(
            success=False,
            provider_id=provider_id,
            error_message=str(e),
            message=f"Provider test failed: {e}",
        )


@router.post(
    "/{provider_id}/models/{model_name}/test",
    response_model=ModelTestResponse,
    operation_id="provider_test_model",
)
async def test_model(
    provider_id: str = Path(..., description="Provider ID"),
    model_name: str = Path(..., description="Model name"),
    request: ModelTestRequest = None,
):
    """
    Test a specific model.
    """
    try:
        provider = provider_manager.get_provider(provider_id)
        if not provider:
            raise HTTPException(
                status_code=404, detail=f"Provider with ID '{provider_id}' not found"
            )

        if model_name not in provider.config.models:
            raise HTTPException(
                status_code=404, detail=f"Model '{model_name}' not found"
            )

        # Use the actual model testing service
        test_message = request.test_message if request else "Hello, this is a test."
        test_result = await provider_manager.test_model(
            provider_id, model_name, test_message
        )

        return ModelTestResponse(
            success=test_result.success,
            provider_id=provider_id,
            model_name=model_name,
            response_time_ms=test_result.response_time_ms,
            test_response=test_result.test_response,
            error_message=test_result.error_message,
            message=(
                "Model test completed successfully"
                if test_result.success
                else "Model test failed"
            ),
        )
    except HTTPException:
        raise
    except MCPError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        return ModelTestResponse(
            success=False,
            provider_id=provider_id,
            model_name=model_name,
            error_message=str(e),
            message=f"Model test failed: {e}",
        )
