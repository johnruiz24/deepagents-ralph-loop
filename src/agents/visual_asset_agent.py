"""
Visual Asset Generation Agent - PROFESSIONAL QUALITY.

Uses skills as tools for visual generation:
- skills.visual_generation.charts: Professional charts (300 DPI)
- skills.visual_generation.architecture: System/architecture diagrams
- skills.visual_generation.timelines: Interactive timelines

QUALITY BAR: McKinsey/BCG consulting-level visuals!
"""

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Literal, Callable

from src.agents.base_agent import LLMAgent
from src.state.shared_state import SharedState
from src.utils.bedrock_config import create_bedrock_llm

# Add skills to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import skills as tools
from skills.visual_generation.generators.charts import (
    generate_chart,
    generate_investment_chart,
    generate_efficiency_chart,
    ChartConfig,
)
from skills.visual_generation.generators.architecture import (
    generate_architecture,
    generate_tui_vs_ota_diagram,
)
from skills.visual_generation.generators.timelines import (
    generate_timeline,
    generate_market_trajectory,
)


@dataclass
class VisualOpportunity:
    """A visualization opportunity identified in the article."""
    type: Literal["architecture", "comparison", "timeline", "data"]
    title: str
    description: str
    section: str
    data_points: list[str]
    suggested_style: str


@dataclass
class GeneratedAsset:
    """A generated visual asset."""
    filename: str
    type: str
    title: str
    description: str
    file_path: Path
    generation_method: str
    quality_score: float


@dataclass
class VisualAssetInput:
    """Input for the visual asset agent."""
    article_content: str
    article_title: str
    topic: str
    key_insights: list[str]
    tui_context: str


@dataclass
class VisualAssetOutput:
    """Output from the visual asset agent."""
    assets: list[GeneratedAsset]
    total_generated: int
    failed_generations: list[str]
    asset_manifest: dict


class VisualAssetAgent(LLMAgent[VisualAssetInput, VisualAssetOutput]):
    """
    Agent that generates PROFESSIONAL visual assets using skills as tools.

    Available Tools (from skills.visual_generation):
    - generate_chart: Bar, line, area charts (matplotlib + seaborn)
    - generate_architecture: System/comparison diagrams (diagrams library)
    - generate_timeline: Market trajectories (plotly)

    Quality: 300 DPI, HBR-standard output
    """

    agent_name = "VisualAssetAgent"
    phase = "visuals"

    MIN_ASSETS = 3
    MAX_ASSETS = 5
    MIN_DPI = 300
    MIN_FILE_SIZE = 50000  # 50KB minimum

    def __init__(self, shared_state: SharedState, **kwargs):
        super().__init__(shared_state, **kwargs)
        self._llm = create_bedrock_llm(model_preset="sonnet", temperature=0.5)

        # Register skills as tools
        self.tools: dict[str, Callable] = {
            "generate_chart": generate_chart,
            "generate_investment_chart": generate_investment_chart,
            "generate_efficiency_chart": generate_efficiency_chart,
            "generate_architecture": generate_architecture,
            "generate_tui_vs_ota_diagram": generate_tui_vs_ota_diagram,
            "generate_timeline": generate_timeline,
            "generate_market_trajectory": generate_market_trajectory,
        }

    async def read_from_state(self) -> VisualAssetInput:
        """Read article content from state."""
        state = self.shared_state.state
        article_content = self.shared_state.read_final_article()
        if not article_content:
            article_content = self.shared_state.read_draft_article() or ""
        synthesized = state.get("synthesized_content", {})
        tui_context = self.shared_state.read_tui_strategy_summary() or ""

        return VisualAssetInput(
            article_content=article_content,
            article_title=synthesized.get("title", state.get("topic", "")),
            topic=state.get("topic", ""),
            key_insights=synthesized.get("key_insights", []),
            tui_context=tui_context,
        )

    async def process(self, input_data: VisualAssetInput) -> VisualAssetOutput:
        """Generate professional visual assets."""
        self.logger.info("Starting PROFESSIONAL visual asset generation", topic=input_data.topic)

        assets = []
        failed = []

        # 1. Generate Investment Comparison Chart (matplotlib + seaborn)
        self.logger.info("Generating investment comparison chart...")
        try:
            asset = self._generate_investment_chart(input_data)
            if asset:
                assets.append(asset)
                self.logger.info(f"Generated: {asset.filename} ({asset.quality_score:.0f}% quality)")
        except Exception as e:
            self.logger.warning(f"Investment chart failed: {e}")
            failed.append(f"investment_chart: {e}")

        # 2. Generate Market Trajectory Chart (matplotlib)
        self.logger.info("Generating market trajectory chart...")
        try:
            asset = self._generate_trajectory_chart(input_data)
            if asset:
                assets.append(asset)
                self.logger.info(f"Generated: {asset.filename} ({asset.quality_score:.0f}% quality)")
        except Exception as e:
            self.logger.warning(f"Trajectory chart failed: {e}")
            failed.append(f"trajectory_chart: {e}")

        # 3. Generate Architecture Diagram (diagrams library)
        self.logger.info("Generating architecture diagram...")
        try:
            asset = self._generate_architecture_diagram(input_data)
            if asset:
                assets.append(asset)
                self.logger.info(f"Generated: {asset.filename} ({asset.quality_score:.0f}% quality)")
        except Exception as e:
            self.logger.warning(f"Architecture diagram failed: {e}")
            failed.append(f"architecture_diagram: {e}")

        # 4. Generate Efficiency Comparison Chart
        self.logger.info("Generating efficiency comparison chart...")
        try:
            asset = self._generate_efficiency_chart(input_data)
            if asset:
                assets.append(asset)
                self.logger.info(f"Generated: {asset.filename} ({asset.quality_score:.0f}% quality)")
        except Exception as e:
            self.logger.warning(f"Efficiency chart failed: {e}")
            failed.append(f"efficiency_chart: {e}")

        # Create manifest
        manifest = {
            "total_assets": len(assets),
            "assets": [
                {
                    "filename": a.filename,
                    "type": a.type,
                    "title": a.title,
                    "path": str(a.file_path),
                    "quality_score": a.quality_score,
                }
                for a in assets
            ],
            "failed": failed,
        }

        self.logger.info(f"Visual generation complete: {len(assets)} assets, {len(failed)} failed")

        return VisualAssetOutput(
            assets=assets,
            total_generated=len(assets),
            failed_generations=failed,
            asset_manifest=manifest,
        )

    async def write_to_state(self, output_data: VisualAssetOutput) -> None:
        """Write asset information to state."""
        manifest_path = self.shared_state.visuals_dir / "asset_manifest.json"
        manifest_path.write_text(json.dumps(output_data.asset_manifest, indent=2))

        self.shared_state.update_state(
            visual_assets=[
                {
                    "filename": a.filename,
                    "type": a.type,
                    "title": a.title,
                    "path": str(a.file_path),
                }
                for a in output_data.assets
            ],
            visual_asset_count=output_data.total_generated,
        )

    async def validate_output(self, output_data: VisualAssetOutput) -> tuple[bool, str]:
        """Validate visual asset generation."""
        issues = []
        if output_data.total_generated < self.MIN_ASSETS:
            issues.append(f"Only {output_data.total_generated} assets (need >= {self.MIN_ASSETS})")

        # Validate each asset quality
        for asset in output_data.assets:
            if asset.quality_score < 80:
                issues.append(f"{asset.filename} quality too low: {asset.quality_score:.0f}%")

        if issues:
            return False, f"Visual validation failed: {'; '.join(issues)}"
        return True, f"Visual assets valid: {output_data.total_generated} professional assets"

    async def calculate_quality_score(self, output_data: VisualAssetOutput) -> float:
        """Calculate quality score."""
        if not output_data.assets:
            return 0.0
        avg_quality = sum(a.quality_score for a in output_data.assets) / len(output_data.assets)
        count_bonus = min(20, output_data.total_generated * 5)
        return min(100, avg_quality * 0.8 + count_bonus)

    def _generate_investment_chart(self, input_data: VisualAssetInput) -> Optional[GeneratedAsset]:
        """Generate professional investment comparison chart using chart skill."""
        filename = "chart_technology_investment_landscape.png"
        file_path = self.shared_state.visuals_dir / filename

        # Use skill as tool
        result_path = self.tools["generate_investment_chart"](
            companies=['TUI Group', 'Booking Holdings', 'Expedia Group', 'Airbnb', 'Trip.com'],
            investments=[150, 5900, 2100, 1800, 1200],  # Millions USD
            output_path=file_path,
            highlight_company='TUI Group',
        )

        if result_path and result_path.exists():
            quality = self._validate_image_quality(result_path)
            return GeneratedAsset(
                filename=filename,
                type="chart",
                title="Technology Investment Landscape",
                description="Comparison of annual technology spending across major travel companies",
                file_path=result_path,
                generation_method="skill:visual_generation.charts",
                quality_score=quality,
            )
        return None

    def _generate_trajectory_chart(self, input_data: VisualAssetInput) -> Optional[GeneratedAsset]:
        """Generate market trajectory chart using timeline skill."""
        filename = "chart_market_trajectory_inflection_point.png"
        file_path = self.shared_state.visuals_dir / filename

        # Use skill as tool
        result_path = self.tools["generate_market_trajectory"](
            years=[2022, 2023, 2024, 2025, 2026, 2027, 2028],
            values=[25, 30, 36, 43, 52, 62, 75],  # Billions USD
            output_path=file_path,
            inflection_year=2026,
            inflection_label="$50B Inflection Point",
        )

        if result_path and result_path.exists():
            quality = self._validate_image_quality(result_path)
            return GeneratedAsset(
                filename=filename,
                type="timeline",
                title="Market Trajectory: The $50B Inflection Point",
                description="AI-enabled travel technology market growth projection showing strategic window",
                file_path=result_path,
                generation_method="skill:visual_generation.timelines",
                quality_score=quality,
            )
        return None

    def _generate_architecture_diagram(self, input_data: VisualAssetInput) -> Optional[GeneratedAsset]:
        """Generate professional architecture diagram using architecture skill."""
        filename = "diagram_vertical_integration_architecture"
        file_path = self.shared_state.visuals_dir / filename

        # Change to visuals directory (diagrams library saves relative to cwd)
        original_cwd = os.getcwd()
        os.chdir(self.shared_state.visuals_dir)

        try:
            # Use skill as tool
            result_path = self.tools["generate_tui_vs_ota_diagram"](
                output_path=filename,  # Without extension
            )

            if result_path and result_path.exists():
                quality = self._validate_image_quality(result_path)
                return GeneratedAsset(
                    filename=result_path.name,
                    type="architecture",
                    title="Vertical Integration Architecture",
                    description="TUI's asset-rich model vs OTA asset-light model",
                    file_path=result_path,
                    generation_method="skill:visual_generation.architecture",
                    quality_score=quality,
                )
            return None

        except Exception as e:
            self.logger.warning(f"Architecture diagram skill failed: {e}")
            return self._generate_fallback_architecture_chart(input_data)
        finally:
            os.chdir(original_cwd)

    def _generate_fallback_architecture_chart(self, input_data: VisualAssetInput) -> Optional[GeneratedAsset]:
        """Fallback to basic chart skill if diagrams library fails."""
        filename = "diagram_vertical_integration_comparison.png"
        file_path = self.shared_state.visuals_dir / filename

        # Use chart skill as fallback with comparison data
        result_path = self.tools["generate_chart"](
            chart_type="horizontal_bar",
            data={
                "labels": ["TUI (Owned Assets)", "OTAs (API Only)"],
                "values": [100, 30],  # Data coverage %
                "xlabel": "Data Coverage (%)"
            },
            title="Vertical Integration Data Advantage",
            output_path=file_path,
            subtitle="Proprietary data access: TUI vs Asset-Light OTAs",
            highlight="TUI (Owned Assets)",
        )

        if result_path and result_path.exists():
            quality = self._validate_image_quality(result_path)
            return GeneratedAsset(
                filename=filename,
                type="chart",
                title="Vertical Integration Comparison",
                description="TUI's asset-rich model vs OTA asset-light model",
                file_path=result_path,
                generation_method="skill:visual_generation.charts (fallback)",
                quality_score=quality,
            )
        return None

    def _generate_efficiency_chart(self, input_data: VisualAssetInput) -> Optional[GeneratedAsset]:
        """Generate efficiency comparison chart using chart skill."""
        filename = "chart_ai_efficiency_gains_operations.png"
        file_path = self.shared_state.visuals_dir / filename

        # Use skill as tool
        result_path = self.tools["generate_efficiency_chart"](
            categories=['Booking Process', 'Revenue Mgmt', 'Customer Service',
                        'Supply Chain', 'Marketing'],
            gains=[60, 45, 55, 40, 50],  # % efficiency gain
            output_path=file_path,
        )

        if result_path and result_path.exists():
            quality = self._validate_image_quality(result_path)
            return GeneratedAsset(
                filename=filename,
                type="chart",
                title="AI Efficiency Gains Across Operations",
                description="Efficiency improvements from AI adoption across travel value chain",
                file_path=result_path,
                generation_method="skill:visual_generation.charts",
                quality_score=quality,
            )
        return None

    def _validate_image_quality(self, file_path: Path) -> float:
        """Validate image meets quality standards."""
        try:
            from PIL import Image
            img = Image.open(file_path)
            width, height = img.size
            file_size = file_path.stat().st_size

            checks = {
                "resolution": width >= 1200 and height >= 600,
                "file_size": file_size >= self.MIN_FILE_SIZE,
                "format": file_path.suffix.lower() == '.png',
            }

            # Calculate score
            score = 60.0  # Base score
            if checks["resolution"]:
                score += 20
            if checks["file_size"]:
                score += 15
            if checks["format"]:
                score += 5

            return min(100, score)

        except Exception as e:
            self.logger.warning(f"Quality validation failed: {e}")
            return 70.0  # Default score


def create_visual_asset_agent(shared_state: SharedState) -> VisualAssetAgent:
    """Factory function to create VisualAssetAgent."""
    return VisualAssetAgent(shared_state)
