"""
Professional architecture diagram generation using the diagrams library.

Generates cloud-style architecture diagrams with icons for
system components, data flows, and business model comparisons.
"""

import os
from pathlib import Path
from typing import Any, Literal, Optional
from dataclasses import dataclass


@dataclass
class DiagramConfig:
    """Configuration for diagram generation."""
    direction: Literal["LR", "TB", "RL", "BT"] = "LR"
    show: bool = False
    graph_attr: dict = None
    
    def __post_init__(self):
        if self.graph_attr is None:
            self.graph_attr = {
                "fontsize": "14",
                "bgcolor": "white",
                "pad": "0.5",
                "dpi": "300",
            }


def generate_architecture(
    diagram_type: Literal["comparison", "system", "data_flow", "business_model"],
    entities: dict[str, Any],
    output_path: str | Path,
    title: Optional[str] = None,
    config: Optional[DiagramConfig] = None,
) -> Path:
    """
    Generate a professional architecture diagram.
    
    Args:
        diagram_type: Type of diagram to generate
        entities: Dictionary describing the diagram entities
        output_path: Path to save the diagram (without extension)
        title: Optional diagram title
        config: Optional diagram configuration
        
    Returns:
        Path to the generated diagram PNG
    """
    config = config or DiagramConfig()
    output_path = Path(output_path)
    
    # Remove extension if present (diagrams library adds it)
    if output_path.suffix:
        output_path = output_path.with_suffix("")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if diagram_type == "comparison":
        return _generate_comparison_diagram(entities, output_path, title, config)
    elif diagram_type == "system":
        return _generate_system_diagram(entities, output_path, title, config)
    elif diagram_type == "data_flow":
        return _generate_data_flow_diagram(entities, output_path, title, config)
    elif diagram_type == "business_model":
        return _generate_business_model_diagram(entities, output_path, title, config)
    else:
        raise ValueError(f"Unknown diagram type: {diagram_type}")


def _generate_comparison_diagram(
    entities: dict[str, Any],
    output_path: Path,
    title: Optional[str],
    config: DiagramConfig,
) -> Path:
    """Generate a comparison diagram (e.g., TUI vs OTA)."""
    from diagrams import Diagram, Cluster, Edge
    from diagrams.generic.storage import Storage
    from diagrams.generic.compute import Rack
    from diagrams.generic.database import SQL
    from diagrams.generic.network import Firewall
    from diagrams.aws.analytics import DataLake
    
    diagram_title = title or "Business Model Comparison"
    
    with Diagram(
        diagram_title,
        filename=str(output_path),
        show=config.show,
        direction=config.direction,
        graph_attr=config.graph_attr,
    ):
        left = entities.get("left", {})
        right = entities.get("right", {})
        
        # Left side (e.g., Vertically Integrated)
        with Cluster(left.get("name", "Model A"), graph_attr={"bgcolor": "#E3F2FD"}):
            left_components = []
            for comp in left.get("components", []):
                if "hotel" in comp.lower():
                    left_components.append(Rack(comp))
                elif "aircraft" in comp.lower() or "flight" in comp.lower():
                    left_components.append(Firewall(comp))
                elif "cruise" in comp.lower() or "ship" in comp.lower():
                    left_components.append(Storage(comp))
                else:
                    left_components.append(Rack(comp))
            
            if left_components:
                left_lake = DataLake("Integrated\nData Lake")
                for comp in left_components:
                    comp >> Edge(color="#1976D2", style="bold") >> left_lake
        
        # Right side (e.g., Asset-Light)
        with Cluster(right.get("name", "Model B"), graph_attr={"bgcolor": "#FFF3E0"}):
            right_components = []
            for comp in right.get("components", []):
                right_components.append(SQL(comp))
            
            if right_components:
                right_db = SQL("Limited\nData Access")
                for comp in right_components:
                    comp >> Edge(color="#F57C00", style="dashed") >> right_db
    
    return Path(str(output_path) + ".png")


def _generate_system_diagram(
    entities: dict[str, Any],
    output_path: Path,
    title: Optional[str],
    config: DiagramConfig,
) -> Path:
    """Generate a system architecture diagram."""
    from diagrams import Diagram, Cluster, Edge
    from diagrams.aws.compute import EC2, Lambda
    from diagrams.aws.database import RDS, ElastiCache
    from diagrams.aws.network import ELB, APIGateway
    from diagrams.aws.ml import Sagemaker
    
    diagram_title = title or "System Architecture"
    
    with Diagram(
        diagram_title,
        filename=str(output_path),
        show=config.show,
        direction=config.direction,
        graph_attr=config.graph_attr,
    ):
        # Entry point
        lb = ELB("Load Balancer")
        api = APIGateway("API Gateway")
        
        # Application layer
        with Cluster("Application Layer", graph_attr={"bgcolor": "#E8F5E9"}):
            services = []
            for svc in entities.get("services", ["Service A", "Service B"]):
                services.append(EC2(svc))
        
        # Data layer
        with Cluster("Data Layer", graph_attr={"bgcolor": "#E3F2FD"}):
            db = RDS("Database")
            cache = ElastiCache("Cache")
        
        # ML layer (optional)
        if entities.get("ml_enabled", False):
            with Cluster("ML Layer", graph_attr={"bgcolor": "#FFF3E0"}):
                ml = Sagemaker("ML Models")
        
        # Connections
        lb >> api
        api >> services
        for svc in services:
            svc >> db
            svc >> cache
            if entities.get("ml_enabled", False):
                svc >> ml
    
    return Path(str(output_path) + ".png")


def _generate_data_flow_diagram(
    entities: dict[str, Any],
    output_path: Path,
    title: Optional[str],
    config: DiagramConfig,
) -> Path:
    """Generate a data flow diagram."""
    from diagrams import Diagram, Cluster, Edge
    from diagrams.aws.analytics import Kinesis, Glue, Athena
    from diagrams.aws.storage import S3
    from diagrams.aws.ml import Sagemaker
    
    diagram_title = title or "Data Flow Architecture"
    
    with Diagram(
        diagram_title,
        filename=str(output_path),
        show=config.show,
        direction="LR",
        graph_attr=config.graph_attr,
    ):
        sources = entities.get("sources", ["Source A", "Source B"])
        
        with Cluster("Data Sources"):
            source_nodes = [Kinesis(src) for src in sources]
        
        with Cluster("Processing"):
            glue = Glue("ETL")
            lake = S3("Data Lake")
        
        with Cluster("Analytics"):
            athena = Athena("Query")
            ml = Sagemaker("ML")
        
        for src in source_nodes:
            src >> glue
        glue >> lake
        lake >> athena
        lake >> ml
    
    return Path(str(output_path) + ".png")


def _generate_business_model_diagram(
    entities: dict[str, Any],
    output_path: Path,
    title: Optional[str],
    config: DiagramConfig,
) -> Path:
    """Generate a business model diagram."""
    # Delegates to comparison for now, can be extended
    return _generate_comparison_diagram(entities, output_path, title, config)


# Convenience functions
def generate_tui_vs_ota_diagram(output_path: str | Path) -> Path:
    """Generate TUI vs OTA comparison diagram."""
    return generate_architecture(
        diagram_type="comparison",
        entities={
            "left": {
                "name": "TUI Vertically Integrated",
                "components": ["400+ Hotels", "130+ Aircraft", "16 Cruise Ships"]
            },
            "right": {
                "name": "OTA Asset-Light",
                "components": ["API Aggregation", "Third-Party Inventory", "Limited Data"]
            }
        },
        output_path=output_path,
        title="Business Model Comparison: Vertical Integration vs Asset-Light",
    )
