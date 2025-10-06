"""
Agent-specific configuration templates.

This module contains configuration templates for different
types of agents that can be added to the system.
"""

from typing import Dict, Any, List
from models.task_models import AgentType


class AgentConfigTemplates:
    """
    Templates for configuring different types of agents.
    """
    
    @staticmethod
    def get_design_agent_template() -> Dict[str, Any]:
        """Template for design generation agents."""
        return {
            "agent_type": AgentType.DESIGN,
            "capabilities": [
                "collage_generation",
                "image_processing",
                "layout_arrangement",
                "grid_layout",
                "stacked_layout",
                "circular_layout",
                "freeform_layout",
                "mosaic_layout",
                "image_optimization",
                "format_conversion"
            ],
            "max_concurrent_tasks": 3,
            "processing_options": {
                "default_quality": 95,
                "default_resize_mode": "fit",
                "optimize": True,
                "preserve_aspect_ratio": True,
                "max_file_size_mb": 10
            },
            "layout_preferences": {
                "default_layout": "grid",
                "supported_layouts": ["grid", "stacked", "circular", "freeform", "mosaic"],
                "auto_layout_selection": True
            }
        }
    
    @staticmethod
    def get_effects_agent_template() -> Dict[str, Any]:
        """Template for effects processing agents (future)."""
        return {
            "agent_type": AgentType.EFFECTS,
            "capabilities": [
                "filter_application",
                "color_adjustment",
                "blur_effects",
                "sharpening",
                "noise_reduction",
                "style_transfer",
                "background_removal",
                "object_detection"
            ],
            "max_concurrent_tasks": 2,
            "processing_options": {
                "default_quality": 95,
                "preserve_original": True,
                "batch_processing": True
            },
            "effect_categories": {
                "basic": ["blur", "sharpen", "brightness", "contrast"],
                "advanced": ["style_transfer", "background_removal", "object_detection"],
                "ai_powered": ["style_transfer", "background_removal"]
            }
        }
    
    @staticmethod
    def get_optimization_agent_template() -> Dict[str, Any]:
        """Template for optimization agents (future)."""
        return {
            "agent_type": AgentType.OPTIMIZATION,
            "capabilities": [
                "file_size_optimization",
                "quality_optimization",
                "format_conversion",
                "compression",
                "batch_optimization",
                "progressive_loading",
                "web_optimization"
            ],
            "max_concurrent_tasks": 5,
            "processing_options": {
                "target_file_size_mb": 1,
                "quality_threshold": 80,
                "format_preference": "webp",
                "progressive": True
            },
            "optimization_strategies": {
                "aggressive": {"quality": 70, "compression": "high"},
                "balanced": {"quality": 85, "compression": "medium"},
                "quality": {"quality": 95, "compression": "low"}
            }
        }
    
    @staticmethod
    def get_huggingface_agent_template() -> Dict[str, Any]:
        """Template for Hugging Face integration agents (future)."""
        return {
            "agent_type": "huggingface",
            "capabilities": [
                "text_to_image",
                "image_to_image",
                "image_upscaling",
                "style_transfer",
                "background_generation",
                "object_inpainting",
                "prompt_optimization"
            ],
            "max_concurrent_tasks": 1,  # GPU intensive
            "model_config": {
                "base_model": "runwayml/stable-diffusion-v1-5",
                "scheduler": "DPMSolverMultistepScheduler",
                "safety_checker": True,
                "feature_extractor": True
            },
            "generation_options": {
                "default_steps": 20,
                "default_guidance_scale": 7.5,
                "default_width": 512,
                "default_height": 512,
                "max_steps": 50,
                "max_guidance_scale": 20
            },
            "hardware_requirements": {
                "gpu_memory_gb": 4,
                "cpu_cores": 4,
                "ram_gb": 8
            }
        }
    
    @staticmethod
    def get_all_templates() -> Dict[str, Dict[str, Any]]:
        """Get all available agent templates."""
        return {
            "design": AgentConfigTemplates.get_design_agent_template(),
            "effects": AgentConfigTemplates.get_effects_agent_template(),
            "optimization": AgentConfigTemplates.get_optimization_agent_template(),
            "huggingface": AgentConfigTemplates.get_huggingface_agent_template()
        }
    
    @staticmethod
    def create_agent_config(agent_type: str, custom_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create agent configuration from template with custom overrides.
        
        Args:
            agent_type: Type of agent
            custom_config: Custom configuration overrides
            
        Returns:
            Agent configuration dictionary
        """
        templates = AgentConfigTemplates.get_all_templates()
        
        if agent_type not in templates:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        config = templates[agent_type].copy()
        
        if custom_config:
            # Deep merge custom config
            config = AgentConfigTemplates._deep_merge(config, custom_config)
        
        return config
    
    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            override: Override dictionary
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = AgentConfigTemplates._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result


class AgentRegistry:
    """
    Registry for managing agent configurations.
    """
    
    def __init__(self):
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._templates = AgentConfigTemplates.get_all_templates()
    
    def register_agent(self, agent_id: str, config: Dict[str, Any]) -> None:
        """
        Register an agent configuration.
        
        Args:
            agent_id: Unique agent identifier
            config: Agent configuration
        """
        self._agents[agent_id] = config
    
    def get_agent_config(self, agent_id: str) -> Dict[str, Any]:
        """
        Get agent configuration.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent configuration
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not registered")
        
        return self._agents[agent_id]
    
    def list_agents(self) -> List[str]:
        """
        List all registered agent IDs.
        
        Returns:
            List of agent IDs
        """
        return list(self._agents.keys())
    
    def get_agents_by_type(self, agent_type: str) -> List[str]:
        """
        Get agents by type.
        
        Args:
            agent_type: Type of agents to find
            
        Returns:
            List of agent IDs of the specified type
        """
        return [
            agent_id for agent_id, config in self._agents.items()
            if config.get("agent_type") == agent_type
        ]
    
    def create_from_template(
        self,
        agent_id: str,
        template_type: str,
        custom_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create agent configuration from template.
        
        Args:
            agent_id: Unique agent identifier
            template_type: Type of template to use
            custom_config: Custom configuration overrides
            
        Returns:
            Created agent configuration
        """
        config = AgentConfigTemplates.create_agent_config(template_type, custom_config)
        config["agent_id"] = agent_id
        
        self.register_agent(agent_id, config)
        return config


# Global agent registry
agent_registry = AgentRegistry()
