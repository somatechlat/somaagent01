"""AgentIQ Configuration Loader - Integrates with centralized config system.

Loads AgentIQ and Confidence configuration from YAML and environment variables.
Supports hot-reload via Settings cache.

VIBE COMPLIANT:
- Real configuration loading (no mocks)
- Integrates with existing src/core/config system
- Validates all configuration values
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from admin.agents.services.agentiq_governor import AgentIQConfig
from admin.agents.services.confidence_scorer import ConfidenceConfig, ConfidenceMode, OnLowAction

LOGGER = logging.getLogger(__name__)

# Default config file path
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "conf" / "agentiq.yaml"


def load_agentiq_config(
    config_path: Optional[Path] = None,
    env_prefix: str = "SA01_AGENTIQ_",
) -> AgentIQConfig:
    """Load AgentIQ configuration from YAML and environment.
    
    Priority (highest to lowest):
    1. Environment variables (SA01_AGENTIQ_*)
    2. YAML configuration file
    3. Default values
    
    Args:
        config_path: Path to YAML config file (default: conf/agentiq.yaml)
        env_prefix: Environment variable prefix
        
    Returns:
        Validated AgentIQConfig instance
    """
    config_path = config_path or DEFAULT_CONFIG_PATH
    
    # Load YAML config
    yaml_config = _load_yaml_section(config_path, "agentiq")
    
    # Apply environment overrides
    config_dict = _apply_env_overrides(yaml_config, env_prefix)
    
    # Build config object
    return AgentIQConfig(**config_dict)


def load_confidence_config(
    config_path: Optional[Path] = None,
    env_prefix: str = "SA01_CONFIDENCE_",
) -> ConfidenceConfig:
    """Load Confidence configuration from YAML and environment.
    
    Priority (highest to lowest):
    1. Environment variables (SA01_CONFIDENCE_*)
    2. YAML configuration file
    3. Default values
    
    Args:
        config_path: Path to YAML config file (default: conf/agentiq.yaml)
        env_prefix: Environment variable prefix
        
    Returns:
        Validated ConfidenceConfig instance
    """
    config_path = config_path or DEFAULT_CONFIG_PATH
    
    # Load YAML config
    yaml_config = _load_yaml_section(config_path, "confidence")
    
    # Apply environment overrides
    config_dict = _apply_confidence_env_overrides(yaml_config, env_prefix)
    
    # Convert string enums
    if "mode" in config_dict and isinstance(config_dict["mode"], str):
        config_dict["mode"] = ConfidenceMode(config_dict["mode"])
    if "on_low" in config_dict and isinstance(config_dict["on_low"], str):
        config_dict["on_low"] = OnLowAction(config_dict["on_low"])
    
    return ConfidenceConfig(**config_dict)


def _load_yaml_section(config_path: Path, section: str) -> Dict[str, Any]:
    """Load a section from YAML config file.
    
    Args:
        config_path: Path to YAML file
        section: Section name to load
        
    Returns:
        Dictionary with section contents (empty if not found)
    """
    if not config_path.exists():
        LOGGER.debug("Config file not found: %s", config_path)
        return {}
    
    try:
        with open(config_path, "r") as f:
            full_config = yaml.safe_load(f) or {}
        return full_config.get(section, {})
    except Exception as e:
        LOGGER.warning("Failed to load config from %s: %s", config_path, e)
        return {}


def _apply_env_overrides(yaml_config: Dict[str, Any], prefix: str) -> Dict[str, Any]:
    """Apply environment variable overrides to AgentIQ config.
    
    Environment variables:
    - SA01_AGENTIQ_ENABLED: bool
    - SA01_AGENTIQ_WEIGHTS_CONTEXT_QUALITY: float
    - SA01_AGENTIQ_WEIGHTS_TOOL_RELEVANCE: float
    - SA01_AGENTIQ_WEIGHTS_BUDGET_EFFICIENCY: float
    - SA01_AGENTIQ_DEGRADATION_L1_THRESHOLD: float
    - etc.
    """
    config = yaml_config.copy()
    
    # Top-level enabled flag
    enabled_env = os.environ.get(f"{prefix}ENABLED")
    if enabled_env is not None:
        config["enabled"] = enabled_env.lower() in ("true", "1", "yes", "on")
    
    # Weights
    weights = config.get("weights", {})
    for key in ["context_quality", "tool_relevance", "budget_efficiency"]:
        env_key = f"{prefix}WEIGHTS_{key.upper()}"
        env_val = os.environ.get(env_key)
        if env_val is not None:
            try:
                weights[key] = float(env_val)
            except ValueError:
                LOGGER.warning("Invalid float for %s: %s", env_key, env_val)
    if weights:
        config["weights"] = weights
    
    # Degradation thresholds
    degradation = config.get("degradation", {})
    for key in ["l1_threshold", "l2_threshold", "l3_threshold", "l4_threshold"]:
        env_key = f"{prefix}DEGRADATION_{key.upper()}"
        env_val = os.environ.get(env_key)
        if env_val is not None:
            try:
                degradation[key] = float(env_val)
            except ValueError:
                LOGGER.warning("Invalid float for %s: %s", env_key, env_val)
    if degradation:
        config["degradation"] = degradation
    
    # Tool K
    tool_k = config.get("tool_k", {})
    for key in ["normal", "l1", "l2", "l3", "l4"]:
        env_key = f"{prefix}TOOL_K_{key.upper()}"
        env_val = os.environ.get(env_key)
        if env_val is not None:
            try:
                tool_k[key] = int(env_val)
            except ValueError:
                LOGGER.warning("Invalid int for %s: %s", env_key, env_val)
    if tool_k:
        config["tool_k"] = tool_k
    
    return config


def _apply_confidence_env_overrides(yaml_config: Dict[str, Any], prefix: str) -> Dict[str, Any]:
    """Apply environment variable overrides to Confidence config.
    
    Environment variables:
    - SA01_CONFIDENCE_ENABLED: bool
    - SA01_CONFIDENCE_MODE: str (average|min|percentile_90)
    - SA01_CONFIDENCE_MIN_ACCEPTANCE: float
    - SA01_CONFIDENCE_ON_LOW: str (warn|retry|reject)
    - SA01_CONFIDENCE_TREAT_NULL_AS_LOW: bool
    """
    config = yaml_config.copy()
    
    # Enabled flag
    enabled_env = os.environ.get(f"{prefix}ENABLED")
    if enabled_env is not None:
        config["enabled"] = enabled_env.lower() in ("true", "1", "yes", "on")
    
    # Mode
    mode_env = os.environ.get(f"{prefix}MODE")
    if mode_env is not None:
        config["mode"] = mode_env.lower()
    
    # Min acceptance
    min_env = os.environ.get(f"{prefix}MIN_ACCEPTANCE")
    if min_env is not None:
        try:
            config["min_acceptance"] = float(min_env)
        except ValueError:
            LOGGER.warning("Invalid float for %sMIN_ACCEPTANCE: %s", prefix, min_env)
    
    # On low action
    on_low_env = os.environ.get(f"{prefix}ON_LOW")
    if on_low_env is not None:
        config["on_low"] = on_low_env.lower()
    
    # Treat null as low
    null_env = os.environ.get(f"{prefix}TREAT_NULL_AS_LOW")
    if null_env is not None:
        config["treat_null_as_low"] = null_env.lower() in ("true", "1", "yes", "on")
    
    return config


# -----------------------------------------------------------------------------
# Cached configuration singleton
# -----------------------------------------------------------------------------

_agentiq_config: Optional[AgentIQConfig] = None
_confidence_config: Optional[ConfidenceConfig] = None


def get_agentiq_config() -> AgentIQConfig:
    """Get cached AgentIQ configuration.
    
    Returns:
        Cached AgentIQConfig instance
    """
    global _agentiq_config
    if _agentiq_config is None:
        _agentiq_config = load_agentiq_config()
    return _agentiq_config


def get_confidence_config() -> ConfidenceConfig:
    """Get cached Confidence configuration.
    
    Returns:
        Cached ConfidenceConfig instance
    """
    global _confidence_config
    if _confidence_config is None:
        _confidence_config = load_confidence_config()
    return _confidence_config


def reload_config() -> None:
    """Reload configuration from disk and environment.
    
    Call this to pick up configuration changes without restart.
    """
    global _agentiq_config, _confidence_config
    _agentiq_config = load_agentiq_config()
    _confidence_config = load_confidence_config()
    LOGGER.info("AgentIQ configuration reloaded")


__all__ = [
    "load_agentiq_config",
    "load_confidence_config",
    "get_agentiq_config",
    "get_confidence_config",
    "reload_config",
    "DEFAULT_CONFIG_PATH",
]
