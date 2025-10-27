"""
Model registry for versioning, production promotion, and rollback capabilities.

This module provides comprehensive model management capabilities including:
- Model versioning and metadata tracking
- Production promotion workflow
- Model rollback capabilities
- Model lifecycle management
- Model performance tracking
"""

import asyncio
import json
import shutil
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from utils.logging import LoggerFactory


class ModelStage(str, Enum):
    """Model lifecycle stages."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


class ModelStatus(str, Enum):
    """Model status."""

    TRAINING = "training"
    READY = "ready"
    DEPLOYED = "deployed"
    FAILED = "failed"
    DEPRECATED = "deprecated"


class ModelMetadata(BaseModel):
    """Metadata for a model."""

    model_id: str = Field(description="Unique model identifier")
    model_name: str = Field(description="Model name")
    version: str = Field(description="Model version")
    stage: ModelStage = Field(default=ModelStage.DEVELOPMENT, description="Model stage")
    status: ModelStatus = Field(
        default=ModelStatus.TRAINING, description="Model status"
    )

    # Model information
    model_type: str = Field(description="Type of model")
    framework: str = Field(description="ML framework used")
    architecture: str = Field(description="Model architecture")

    # Training information
    training_data_hash: str = Field(description="Hash of training data")
    training_config: Dict[str, Any] = Field(
        default_factory=dict, description="Training configuration"
    )
    hyperparameters: Dict[str, Any] = Field(
        default_factory=dict, description="Model hyperparameters"
    )

    # Performance metrics
    performance_metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Performance metrics"
    )
    evaluation_metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Evaluation metrics"
    )

    # Deployment information
    deployment_config: Dict[str, Any] = Field(
        default_factory=dict, description="Deployment configuration"
    )
    resource_requirements: Dict[str, Any] = Field(
        default_factory=dict, description="Resource requirements"
    )

    # Lifecycle information
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    created_by: str = Field(description="Creator")
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )
    deployed_at: Optional[datetime] = Field(
        default=None, description="Deployment timestamp"
    )

    # Model files
    model_files: List[str] = Field(default_factory=list, description="Model file paths")
    model_size: int = Field(default=0, description="Model size in bytes")

    # Tags and description
    tags: List[str] = Field(default_factory=list, description="Model tags")
    description: str = Field(default="", description="Model description")


class ModelVersion(BaseModel):
    """Version information for a model."""

    version: str = Field(description="Version string")
    model_id: str = Field(description="Model ID")
    metadata: ModelMetadata = Field(description="Model metadata")

    # Version relationships
    parent_version: Optional[str] = Field(default=None, description="Parent version")
    child_versions: List[str] = Field(
        default_factory=list, description="Child versions"
    )

    # Version status
    is_current: bool = Field(
        default=False, description="Whether this is the current version"
    )
    is_production: bool = Field(
        default=False, description="Whether this is in production"
    )

    # Version metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Version creation time"
    )
    changelog: str = Field(default="", description="Version changelog")


class PromotionRequest(BaseModel):
    """Request to promote a model to production."""

    request_id: str = Field(description="Unique request identifier")
    model_id: str = Field(description="Model ID to promote")
    version: str = Field(description="Version to promote")
    requested_by: str = Field(description="Person requesting promotion")
    requested_at: datetime = Field(
        default_factory=datetime.now, description="Request timestamp"
    )

    # Promotion details
    target_stage: ModelStage = Field(description="Target stage for promotion")
    promotion_reason: str = Field(description="Reason for promotion")
    approval_required: bool = Field(
        default=True, description="Whether approval is required"
    )

    # Status tracking
    status: str = Field(default="pending", description="Request status")
    approved_by: Optional[str] = Field(default=None, description="Approver")
    approved_at: Optional[datetime] = Field(
        default=None, description="Approval timestamp"
    )
    deployed_at: Optional[datetime] = Field(
        default=None, description="Deployment timestamp"
    )

    # Rollback information
    rollback_version: Optional[str] = Field(
        default=None, description="Version to rollback to"
    )
    rollback_reason: Optional[str] = Field(default=None, description="Rollback reason")


class ModelRegistry:
    """
    Model registry for versioning, production promotion, and rollback capabilities.

    Provides comprehensive model management capabilities including:
    - Model versioning and metadata tracking
    - Production promotion workflow
    - Model rollback capabilities
    - Model lifecycle management
    - Model performance tracking
    """

    def __init__(self, base_path: Path = Path("model_registry")):
        """
        Initialize model registry.

        Args:
            base_path: Base path for storing model registry data
        """
        self.logger = LoggerFactory.create_logger(__name__)
        self.base_path = base_path
        self.models_path = base_path / "models"
        self.versions_path = base_path / "versions"
        self.promotions_path = base_path / "promotions"
        self.deployments_path = base_path / "deployments"

        # Create directories
        self._create_directories()

        # In-memory storage
        self.models: Dict[str, ModelMetadata] = {}
        self.versions: Dict[
            str, Dict[str, ModelVersion]
        ] = {}  # model_id -> version -> ModelVersion
        self.promotions: Dict[str, PromotionRequest] = {}
        self.current_versions: Dict[str, str] = {}  # model_id -> current_version
        self.production_versions: Dict[str, str] = {}  # model_id -> production_version

        # Load existing data
        self._load_existing_data()

    def _create_directories(self) -> None:
        """Create necessary directories."""
        for path in [
            self.base_path,
            self.models_path,
            self.versions_path,
            self.promotions_path,
            self.deployments_path,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def _load_existing_data(self) -> None:
        """Load existing registry data."""
        try:
            # Load models
            models_file = self.base_path / "models.json"
            if models_file.exists():
                with open(models_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for model_data in data:
                        model = ModelMetadata(**model_data)
                        self.models[model.model_id] = model

            # Load versions
            versions_file = self.base_path / "versions.json"
            if versions_file.exists():
                with open(versions_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for model_id, versions_data in data.items():
                        self.versions[model_id] = {}
                        for version, version_data in versions_data.items():
                            version_obj = ModelVersion(**version_data)
                            self.versions[model_id][version] = version_obj

            # Load promotions
            promotions_file = self.base_path / "promotions.json"
            if promotions_file.exists():
                with open(promotions_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for prom_data in data:
                        promotion = PromotionRequest(**prom_data)
                        self.promotions[promotion.request_id] = promotion

            # Load current versions
            current_versions_file = self.base_path / "current_versions.json"
            if current_versions_file.exists():
                with open(current_versions_file, "r", encoding="utf-8") as f:
                    self.current_versions = json.load(f)

            # Load production versions
            production_versions_file = self.base_path / "production_versions.json"
            if production_versions_file.exists():
                with open(production_versions_file, "r", encoding="utf-8") as f:
                    self.production_versions = json.load(f)

            self.logger.info(
                f"Loaded {len(self.models)} models, {sum(len(versions) for versions in self.versions.values())} versions"
            )
        except Exception as e:
            self.logger.error(f"Failed to load existing data: {e}")

    def register_model(
        self,
        model_name: str,
        model_type: str,
        framework: str,
        architecture: str,
        version: str,
        model_files: List[Union[str, Path]],
        training_data_hash: str,
        performance_metrics: Optional[Dict[str, Any]] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        created_by: str = "system",
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> ModelMetadata:
        """
        Register a new model version.

        Args:
            model_name: Name of the model
            model_type: Type of model
            framework: ML framework used
            architecture: Model architecture
            version: Model version
            model_files: List of model file paths
            training_data_hash: Hash of training data
            performance_metrics: Performance metrics
            hyperparameters: Model hyperparameters
            created_by: Creator of the model
            description: Model description
            tags: Model tags

        Returns:
            ModelMetadata: Registered model metadata
        """
        model_id = f"{model_name}_{version}"

        # Calculate model size
        total_size = 0
        processed_files = []
        for file_path in model_files:
            file_path = Path(file_path)
            if file_path.exists():
                total_size += file_path.stat().st_size
                processed_files.append(str(file_path))

        # Create model metadata
        metadata = ModelMetadata(
            model_id=model_id,
            model_name=model_name,
            version=version,
            model_type=model_type,
            framework=framework,
            architecture=architecture,
            training_data_hash=training_data_hash,
            performance_metrics=performance_metrics or {},
            hyperparameters=hyperparameters or {},
            created_by=created_by,
            description=description,
            tags=tags or [],
            model_files=processed_files,
            model_size=total_size,
        )

        # Create model version
        model_version = ModelVersion(
            version=version, model_id=model_id, metadata=metadata
        )

        # Store in registry
        self.models[model_id] = metadata

        if model_name not in self.versions:
            self.versions[model_name] = {}
        self.versions[model_name][version] = model_version

        # Set as current version if it's the first version
        if model_name not in self.current_versions:
            self.current_versions[model_name] = version
            model_version.is_current = True

        # Save to disk
        self._save_model_files(model_id, model_files)
        self._save_registry_data()

        self.logger.info(f"Registered model {model_name} version {version}")
        return metadata

    def promote_model(
        self,
        model_name: str,
        version: str,
        target_stage: ModelStage,
        requested_by: str,
        promotion_reason: str,
        approval_required: bool = True,
    ) -> PromotionRequest:
        """
        Request promotion of a model to a target stage.

        Args:
            model_name: Name of the model
            version: Version to promote
            target_stage: Target stage for promotion
            requested_by: Person requesting promotion
            promotion_reason: Reason for promotion
            approval_required: Whether approval is required

        Returns:
            PromotionRequest: Created promotion request
        """
        model_id = f"{model_name}_{version}"

        if model_name not in self.versions or version not in self.versions[model_name]:
            raise ValueError(f"Model {model_name} version {version} not found")

        # Create promotion request
        request = PromotionRequest(
            request_id=f"promo_{model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            model_id=model_id,
            version=version,
            requested_by=requested_by,
            target_stage=target_stage,
            promotion_reason=promotion_reason,
            approval_required=approval_required,
        )

        self.promotions[request.request_id] = request

        # Auto-approve if no approval required
        if not approval_required:
            self.approve_promotion(request.request_id, requested_by)

        self._save_registry_data()

        self.logger.info(
            f"Created promotion request {request.request_id} for {model_name} v{version}"
        )
        return request

    def approve_promotion(self, request_id: str, approved_by: str) -> bool:
        """
        Approve a promotion request.

        Args:
            request_id: ID of the promotion request
            approved_by: Person approving the promotion

        Returns:
            bool: True if approved successfully
        """
        if request_id not in self.promotions:
            return False

        request = self.promotions[request_id]
        request.status = "approved"
        request.approved_by = approved_by
        request.approved_at = datetime.now()

        # Execute promotion
        self._execute_promotion(request)

        self._save_registry_data()

        self.logger.info(f"Approved promotion request {request_id}")
        return True

    def _execute_promotion(self, request: PromotionRequest) -> None:
        """Execute a promotion request."""
        model_name = request.model_id.split("_")[0]
        version = request.version

        # Update model stage
        if model_name in self.versions and version in self.versions[model_name]:
            model_version = self.versions[model_name][version]
            model_version.metadata.stage = request.target_stage

            # Update production version if promoting to production
            if request.target_stage == ModelStage.PRODUCTION:
                self.production_versions[model_name] = version
                model_version.is_production = True

                # Mark previous production version as not production
                for v, mv in self.versions[model_name].items():
                    if v != version and mv.is_production:
                        mv.is_production = False

        # Update request status
        request.status = "deployed"
        request.deployed_at = datetime.now()

    def rollback_model(
        self,
        model_name: str,
        target_version: str,
        rollback_reason: str,
        requested_by: str,
    ) -> PromotionRequest:
        """
        Rollback a model to a previous version.

        Args:
            model_name: Name of the model
            target_version: Version to rollback to
            rollback_reason: Reason for rollback
            requested_by: Person requesting rollback

        Returns:
            PromotionRequest: Created rollback request
        """
        if (
            model_name not in self.versions
            or target_version not in self.versions[model_name]
        ):
            raise ValueError(f"Model {model_name} version {target_version} not found")

        # Create rollback request
        request = PromotionRequest(
            request_id=f"rollback_{model_name}_{target_version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            model_id=f"{model_name}_{target_version}",
            version=target_version,
            requested_by=requested_by,
            target_stage=ModelStage.PRODUCTION,
            promotion_reason=f"Rollback: {rollback_reason}",
            approval_required=False,
            rollback_version=target_version,
            rollback_reason=rollback_reason,
        )

        self.promotions[request.request_id] = request

        # Execute rollback immediately
        self._execute_promotion(request)

        self._save_registry_data()

        self.logger.info(
            f"Executed rollback for {model_name} to version {target_version}"
        )
        return request

    def get_model(
        self, model_name: str, version: Optional[str] = None
    ) -> Optional[ModelMetadata]:
        """
        Get model metadata.

        Args:
            model_name: Name of the model
            version: Specific version (None for current version)

        Returns:
            ModelMetadata: Model metadata
        """
        if version:
            model_id = f"{model_name}_{version}"
            return self.models.get(model_id)
        else:
            current_version = self.current_versions.get(model_name)
            if current_version:
                model_id = f"{model_name}_{current_version}"
                return self.models.get(model_id)
        return None

    def get_model_versions(self, model_name: str) -> List[ModelVersion]:
        """
        Get all versions of a model.

        Args:
            model_name: Name of the model

        Returns:
            List[ModelVersion]: List of model versions
        """
        if model_name not in self.versions:
            return []

        return list(self.versions[model_name].values())

    def get_production_model(self, model_name: str) -> Optional[ModelMetadata]:
        """
        Get the current production model.

        Args:
            model_name: Name of the model

        Returns:
            ModelMetadata: Production model metadata
        """
        production_version = self.production_versions.get(model_name)
        if production_version:
            return self.get_model(model_name, production_version)
        return None

    def get_model_history(self, model_name: str) -> List[Dict[str, Any]]:
        """
        Get deployment history for a model.

        Args:
            model_name: Name of the model

        Returns:
            List[Dict[str, Any]]: Deployment history
        """
        history = []

        # Get promotion history
        for request in self.promotions.values():
            if request.model_id.startswith(model_name):
                history.append(
                    {
                        "type": "promotion",
                        "timestamp": request.requested_at,
                        "version": request.version,
                        "stage": request.target_stage,
                        "status": request.status,
                        "reason": request.promotion_reason,
                        "requested_by": request.requested_by,
                    }
                )

        # Sort by timestamp
        history.sort(key=lambda x: x["timestamp"], reverse=True)

        return history

    def _save_model_files(
        self, model_id: str, model_files: List[Union[str, Path]]
    ) -> None:
        """Save model files to registry."""
        model_dir = self.models_path / model_id
        model_dir.mkdir(parents=True, exist_ok=True)

        for file_path in model_files:
            file_path = Path(file_path)
            if file_path.exists():
                dest_path = model_dir / file_path.name
                shutil.copy2(file_path, dest_path)

    def _save_registry_data(self) -> None:
        """Save all registry data to files."""
        try:
            # Save models
            models_file = self.base_path / "models.json"
            with open(models_file, "w", encoding="utf-8") as f:
                json.dump(
                    [model.dict() for model in self.models.values()],
                    f,
                    indent=2,
                    default=str,
                )

            # Save versions
            versions_file = self.base_path / "versions.json"
            versions_data = {
                model_name: {
                    version: version_obj.dict()
                    for version, version_obj in versions.items()
                }
                for model_name, versions in self.versions.items()
            }
            with open(versions_file, "w", encoding="utf-8") as f:
                json.dump(versions_data, f, indent=2, default=str)

            # Save promotions
            promotions_file = self.base_path / "promotions.json"
            with open(promotions_file, "w", encoding="utf-8") as f:
                json.dump(
                    [promo.dict() for promo in self.promotions.values()],
                    f,
                    indent=2,
                    default=str,
                )

            # Save current versions
            current_versions_file = self.base_path / "current_versions.json"
            with open(current_versions_file, "w", encoding="utf-8") as f:
                json.dump(self.current_versions, f, indent=2)

            # Save production versions
            production_versions_file = self.base_path / "production_versions.json"
            with open(production_versions_file, "w", encoding="utf-8") as f:
                json.dump(self.production_versions, f, indent=2)

            self.logger.info("Saved model registry data")
        except Exception as e:
            self.logger.error(f"Failed to save registry data: {e}")

    def get_registry_summary(self) -> Dict[str, Any]:
        """Get summary of the model registry."""
        total_models = len(self.models)
        total_versions = sum(len(versions) for versions in self.versions.values())
        production_models = len(self.production_versions)

        return {
            "total_models": total_models,
            "total_versions": total_versions,
            "production_models": production_models,
            "pending_promotions": len(
                [p for p in self.promotions.values() if p.status == "pending"]
            ),
            "models_by_stage": {
                stage.value: len([m for m in self.models.values() if m.stage == stage])
                for stage in ModelStage
            },
            "models_by_status": {
                status.value: len(
                    [m for m in self.models.values() if m.status == status]
                )
                for status in ModelStatus
            },
        }
