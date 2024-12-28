"""
Visualization module for generating visual explanations of AI decisions.
Supports decision trees, Sankey diagrams, and other visualization types.
"""
from typing import Dict, List, Optional, Union
import logging
from dataclasses import dataclass
import json

from ..aot.reasoning_engine import ReasoningStep, ComplianceCheck

logger = logging.getLogger(__name__)

@dataclass
class VisualizationConfig:
    """Configuration for visualization generation."""
    type: str  # tree, sankey, network, metrics
    options: Dict
    theme: Optional[Dict] = None
    interactive: bool = True

class DecisionVisualizer:
    """
    Generates visual explanations for AI decisions.
    """
    
    def __init__(self):
        self.default_theme = {
            "colors": {
                "primary": "#1f77b4",
                "secondary": "#ff7f0e",
                "success": "#2ca02c",
                "warning": "#d62728",
                "neutral": "#7f7f7f"
            },
            "fonts": {
                "family": "Arial, sans-serif",
                "size": {
                    "small": 10,
                    "medium": 12,
                    "large": 14
                }
            }
        }
    
    def generate_decision_tree(
        self,
        steps: List[ReasoningStep],
        config: Optional[VisualizationConfig] = None
    ) -> Dict:
        """
        Generate a decision tree visualization.
        
        Args:
            steps: List of reasoning steps
            config: Visualization configuration
            
        Returns:
            Dictionary with visualization data
        """
        try:
            tree_data = {
                "type": "tree",
                "nodes": self._generate_tree_nodes(steps),
                "edges": self._generate_tree_edges(steps),
                "layout": self._get_tree_layout(config),
                "theme": config.theme if config else self.default_theme
            }
            
            return self._enrich_visualization(tree_data, config)
            
        except Exception as e:
            logger.error(f"Error generating decision tree: {str(e)}")
            return {}
    
    def generate_sankey_diagram(
        self,
        steps: List[ReasoningStep],
        config: Optional[VisualizationConfig] = None
    ) -> Dict:
        """
        Generate a Sankey diagram visualization.
        
        Args:
            steps: List of reasoning steps
            config: Visualization configuration
            
        Returns:
            Dictionary with visualization data
        """
        try:
            sankey_data = {
                "type": "sankey",
                "nodes": self._generate_sankey_nodes(steps),
                "links": self._generate_sankey_links(steps),
                "layout": self._get_sankey_layout(config),
                "theme": config.theme if config else self.default_theme
            }
            
            return self._enrich_visualization(sankey_data, config)
            
        except Exception as e:
            logger.error(f"Error generating Sankey diagram: {str(e)}")
            return {}
    
    def generate_evidence_network(
        self,
        evidence: List[Dict],
        config: Optional[VisualizationConfig] = None
    ) -> Dict:
        """
        Generate a network visualization for evidence relationships.
        
        Args:
            evidence: List of evidence items
            config: Visualization configuration
            
        Returns:
            Dictionary with visualization data
        """
        try:
            network_data = {
                "type": "network",
                "nodes": self._generate_network_nodes(evidence),
                "edges": self._generate_network_edges(evidence),
                "layout": self._get_network_layout(config),
                "theme": config.theme if config else self.default_theme
            }
            
            return self._enrich_visualization(network_data, config)
            
        except Exception as e:
            logger.error(f"Error generating evidence network: {str(e)}")
            return {}
    
    def generate_metrics_visualization(
        self,
        metrics: Dict[str, float],
        config: Optional[VisualizationConfig] = None
    ) -> Dict:
        """
        Generate a visualization for confidence metrics.
        
        Args:
            metrics: Dictionary of metrics
            config: Visualization configuration
            
        Returns:
            Dictionary with visualization data
        """
        try:
            metrics_data = {
                "type": "metrics",
                "data": self._prepare_metrics_data(metrics),
                "layout": self._get_metrics_layout(config),
                "theme": config.theme if config else self.default_theme
            }
            
            return self._enrich_visualization(metrics_data, config)
            
        except Exception as e:
            logger.error(f"Error generating metrics visualization: {str(e)}")
            return {}
    
    def _generate_tree_nodes(self, steps: List[ReasoningStep]) -> List[Dict]:
        """Generate nodes for decision tree visualization."""
        nodes = []
        for i, step in enumerate(steps):
            nodes.append({
                "id": f"step_{i}",
                "label": step.description,
                "type": step.type,
                "confidence": step.confidence,
                "metadata": step.metadata
            })
        return nodes
    
    def _generate_tree_edges(self, steps: List[ReasoningStep]) -> List[Dict]:
        """Generate edges for decision tree visualization."""
        edges = []
        for i in range(len(steps) - 1):
            edges.append({
                "source": f"step_{i}",
                "target": f"step_{i+1}",
                "weight": steps[i].confidence
            })
        return edges
    
    def _generate_sankey_nodes(self, steps: List[ReasoningStep]) -> List[Dict]:
        """Generate nodes for Sankey diagram."""
        nodes = []
        for i, step in enumerate(steps):
            nodes.append({
                "id": f"step_{i}",
                "label": step.description,
                "value": step.confidence
            })
        return nodes
    
    def _generate_sankey_links(self, steps: List[ReasoningStep]) -> List[Dict]:
        """Generate links for Sankey diagram."""
        links = []
        for i in range(len(steps) - 1):
            links.append({
                "source": i,
                "target": i + 1,
                "value": steps[i].confidence
            })
        return links
    
    def _generate_network_nodes(self, evidence: List[Dict]) -> List[Dict]:
        """Generate nodes for evidence network visualization."""
        nodes = []
        for i, item in enumerate(evidence):
            nodes.append({
                "id": f"evidence_{i}",
                "label": item.get("description", ""),
                "type": item.get("type", "evidence"),
                "weight": item.get("confidence", 0.5)
            })
        return nodes
    
    def _generate_network_edges(self, evidence: List[Dict]) -> List[Dict]:
        """Generate edges for evidence network visualization."""
        edges = []
        # TODO: Implement relationship detection between evidence items
        return edges
    
    def _prepare_metrics_data(self, metrics: Dict[str, float]) -> List[Dict]:
        """Prepare metrics data for visualization."""
        return [
            {
                "label": key,
                "value": value,
                "color": self._get_metric_color(value)
            }
            for key, value in metrics.items()
        ]
    
    def _get_metric_color(self, value: float) -> str:
        """Get color for metric based on value."""
        if value >= 0.8:
            return self.default_theme["colors"]["success"]
        elif value >= 0.6:
            return self.default_theme["colors"]["primary"]
        elif value >= 0.4:
            return self.default_theme["colors"]["secondary"]
        else:
            return self.default_theme["colors"]["warning"]
    
    def _get_tree_layout(self, config: Optional[VisualizationConfig]) -> Dict:
        """Get layout configuration for decision tree."""
        default_layout = {
            "orientation": "vertical",
            "nodeSpacing": 50,
            "levelSpacing": 100
        }
        
        if config and config.options.get("layout"):
            return {**default_layout, **config.options["layout"]}
        return default_layout
    
    def _get_sankey_layout(self, config: Optional[VisualizationConfig]) -> Dict:
        """Get layout configuration for Sankey diagram."""
        default_layout = {
            "nodeWidth": 15,
            "nodePadding": 10,
            "iterations": 32
        }
        
        if config and config.options.get("layout"):
            return {**default_layout, **config.options["layout"]}
        return default_layout
    
    def _get_network_layout(self, config: Optional[VisualizationConfig]) -> Dict:
        """Get layout configuration for network visualization."""
        default_layout = {
            "physics": {
                "enabled": True,
                "solver": "forceAtlas2Based"
            },
            "edges": {
                "smooth": True
            }
        }
        
        if config and config.options.get("layout"):
            return {**default_layout, **config.options["layout"]}
        return default_layout
    
    def _get_metrics_layout(self, config: Optional[VisualizationConfig]) -> Dict:
        """Get layout configuration for metrics visualization."""
        default_layout = {
            "type": "radial",
            "showLabels": True,
            "showValues": True
        }
        
        if config and config.options.get("layout"):
            return {**default_layout, **config.options["layout"]}
        return default_layout
    
    def _enrich_visualization(
        self,
        data: Dict,
        config: Optional[VisualizationConfig]
    ) -> Dict:
        """Enrich visualization data with additional information."""
        enriched = {
            **data,
            "metadata": {
                "timestamp": "",  # TODO: Add timestamp
                "version": "1.0",
                "interactive": config.interactive if config else True
            }
        }
        
        if config and config.options.get("annotations"):
            enriched["annotations"] = config.options["annotations"]
            
        return enriched 