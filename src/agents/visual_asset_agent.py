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
        """Generate professional visual assets dynamically for ANY topic."""
        self.logger.info("Starting ADAPTIVE visual asset generation", topic=input_data.topic)

        assets = []
        failed = []

        # STEP 1: Extract structured data from article using LLM
        self.logger.info("Extracting chart data from article content...")
        chart_data = await self._extract_article_chart_data(input_data)

        # STEP 2: Generate 5 strategic charts using templates + extracted data
        chart_generators = [
            ("framework_dimensions", self._generate_framework_chart),
            ("transformation_comparison", self._generate_transformation_chart),
            ("roi_timeline", self._generate_roi_timeline_chart),
            ("competitive_advantage", self._generate_competitive_chart),
            ("implementation_roadmap", self._generate_roadmap_chart),
        ]

        for i, (chart_type, generator) in enumerate(chart_generators):
            self.logger.info(f"Generating chart {i+1}/5: {chart_type}")
            try:
                asset = await generator(input_data, chart_data, i)
                if asset:
                    assets.append(asset)
                    self.logger.info(f"Generated: {asset.filename} ({asset.quality_score:.0f}% quality)")
            except Exception as e:
                self.logger.warning(f"Chart {chart_type} failed: {e}")
                failed.append(f"{chart_type}: {e}")

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

    # ============== ADAPTIVE CHART GENERATION ==============

    async def _extract_article_chart_data(self, input_data: VisualAssetInput) -> dict:
        """Use LLM to extract structured chart data from article content."""
        prompt = f"""Analyze this strategic article and extract data for 5 professional charts.

ARTICLE TITLE: {input_data.article_title}
TOPIC: {input_data.topic}
TARGET AUDIENCE: TUI Leadership

ARTICLE CONTENT:
{input_data.article_content[:6000]}

Extract the following data structures. Use ACTUAL content from the article.
If specific numbers aren't mentioned, make reasonable estimates based on context.

Return JSON:
{{
    "topic_short": "3-5 word summary of main topic",
    "company": "main company discussed (e.g., TUI)",

    "dimensions": {{
        "title": "Framework name (e.g., 'Digital Transformation Framework')",
        "items": [
            {{"name": "Dimension 1 name", "score": 65, "description": "brief desc"}},
            {{"name": "Dimension 2 name", "score": 45, "description": "brief desc"}}
        ]
    }},

    "transformation": {{
        "title": "What is being transformed",
        "before_label": "Current State",
        "after_label": "Target State",
        "categories": ["Category 1", "Category 2", "Category 3", "Category 4", "Category 5"],
        "before_values": [85, 78, 82, 70, 65],
        "after_values": [95, 92, 90, 88, 94]
    }},

    "timeline": {{
        "title": "Investment/Implementation Timeline",
        "breakeven_month": 15,
        "total_months": 36,
        "roi_percentage": 310
    }},

    "competitive": {{
        "title": "Competitive Advantage Analysis",
        "protagonist": "TUI",
        "competitor": "Competitors",
        "categories": ["Advantage 1", "Advantage 2", "Advantage 3", "Advantage 4", "Advantage 5"],
        "protagonist_scores": [95, 85, 90, 80, 88],
        "competitor_scores": [25, 35, 20, 45, 15],
        "moat_label": "Key Advantage"
    }},

    "roadmap": {{
        "title": "Implementation Roadmap",
        "phases": [
            {{"name": "Phase 1: Foundation", "duration": 6, "items": ["Item 1", "Item 2", "Item 3"]}},
            {{"name": "Phase 2: Expansion", "duration": 12, "items": ["Item 1", "Item 2", "Item 3"]}},
            {{"name": "Phase 3: Transformation", "duration": 18, "items": ["Item 1", "Item 2", "Item 3"]}}
        ],
        "milestones": [
            {{"month": 6, "label": "Pilot Complete"}},
            {{"month": 18, "label": "Core Live"}},
            {{"month": 36, "label": "Full Rollout"}}
        ]
    }}
}}

Extract REAL dimensions, categories, and phases from the article content.
Make the data specific to the actual topic discussed, not generic.
"""
        try:
            response = await self._llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                self.logger.info(f"Extracted chart data for topic: {data.get('topic_short', 'unknown')}")
                return data
        except Exception as e:
            self.logger.warning(f"Chart data extraction failed: {e}")

        # Fallback with generic structure
        return self._get_fallback_chart_data(input_data)

    def _get_fallback_chart_data(self, input_data: VisualAssetInput) -> dict:
        """Fallback chart data when LLM extraction fails."""
        topic_words = input_data.topic.split()[:3]
        topic_short = " ".join(topic_words)

        return {
            "topic_short": topic_short,
            "company": "TUI",
            "dimensions": {
                "title": f"{topic_short} Framework",
                "items": [
                    {"name": "Strategic Alignment", "score": 65},
                    {"name": "Technology Readiness", "score": 55},
                    {"name": "Organizational Capability", "score": 60},
                    {"name": "Data Infrastructure", "score": 50},
                    {"name": "Process Maturity", "score": 70},
                ]
            },
            "transformation": {
                "title": f"{topic_short} Transformation",
                "before_label": "Current State",
                "after_label": "Target State",
                "categories": ["Operations", "Technology", "Customer Experience", "Data", "Integration"],
                "before_values": [65, 55, 60, 50, 45],
                "after_values": [90, 88, 92, 85, 90]
            },
            "timeline": {
                "title": "Implementation ROI",
                "breakeven_month": 15,
                "total_months": 36,
                "roi_percentage": 250
            },
            "competitive": {
                "title": "Competitive Position",
                "protagonist": "TUI",
                "competitor": "Industry Average",
                "categories": ["Capability 1", "Capability 2", "Capability 3", "Capability 4", "Capability 5"],
                "protagonist_scores": [85, 80, 75, 70, 85],
                "competitor_scores": [50, 55, 45, 60, 40],
                "moat_label": "Competitive Advantage"
            },
            "roadmap": {
                "title": "Implementation Roadmap",
                "phases": [
                    {"name": "Phase 1: Foundation", "duration": 6, "items": ["Assessment", "Planning", "Quick Wins"]},
                    {"name": "Phase 2: Build", "duration": 12, "items": ["Core Implementation", "Integration", "Testing"]},
                    {"name": "Phase 3: Scale", "duration": 18, "items": ["Full Rollout", "Optimization", "Expansion"]}
                ],
                "milestones": [
                    {"month": 6, "label": "Foundation Complete"},
                    {"month": 18, "label": "Core Live"},
                    {"month": 36, "label": "Full Scale"}
                ]
            }
        }

    async def _generate_framework_chart(self, input_data: VisualAssetInput, chart_data: dict, index: int) -> Optional[GeneratedAsset]:
        """Generate framework/dimensions chart dynamically based on article content."""
        dims = chart_data.get("dimensions", {})
        topic_short = chart_data.get("topic_short", "Strategic")
        company = chart_data.get("company", "TUI")

        items = dims.get("items", [])
        if not items:
            items = [{"name": f"Dimension {i+1}", "score": 50 + i*5} for i in range(6)]

        labels = [f"{i+1}. {item['name']}" for i, item in enumerate(items)]
        values = [item.get("score", 50) for item in items]

        # Find highest score for highlight
        max_idx = values.index(max(values))
        highlight_label = labels[max_idx]

        safe_topic = topic_short.lower().replace(' ', '_')[:20]
        filename = f"chart_1_{safe_topic}_framework.png"
        file_path = self.shared_state.visuals_dir / filename

        result_path = self.tools["generate_chart"](
            chart_type="horizontal_bar",
            data={
                "labels": labels,
                "values": values,
                "xlabel": f"{company} Readiness Score (%)",
            },
            title=dims.get("title", f"{topic_short} Framework"),
            subtitle=f"Current {company} readiness assessment across key dimensions",
            output_path=file_path,
            highlight=highlight_label,
        )

        if result_path and result_path.exists():
            quality = self._validate_image_quality(result_path)
            return GeneratedAsset(
                filename=filename,
                type="chart",
                title=dims.get("title", f"{topic_short} Framework"),
                description=f"Strategic overview of {company}'s readiness across all dimensions",
                file_path=result_path,
                generation_method="adaptive:framework_chart",
                quality_score=quality,
            )
        return None

    async def _generate_transformation_chart(self, input_data: VisualAssetInput, chart_data: dict, index: int) -> Optional[GeneratedAsset]:
        """Generate Before/After transformation comparison dynamically."""
        trans = chart_data.get("transformation", {})
        topic_short = chart_data.get("topic_short", "Strategic")
        company = chart_data.get("company", "TUI")

        safe_topic = topic_short.lower().replace(' ', '_')[:20]
        filename = f"chart_2_{safe_topic}_transformation.png"
        file_path = self.shared_state.visuals_dir / filename

        # Get dynamic data
        categories = trans.get("categories", ["Operations", "Technology", "Customer", "Data", "Integration"])
        before_values = trans.get("before_values", [65, 55, 60, 50, 45])
        after_values = trans.get("after_values", [90, 88, 92, 85, 90])
        before_label = trans.get("before_label", "Current State")
        after_label = trans.get("after_label", "Target State")
        title = trans.get("title", f"{topic_short} Transformation")

        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

        # Before - Current State
        colors_before = ['#E57373'] * len(categories)
        ax1.barh(categories, before_values, color=colors_before, edgecolor='white', linewidth=2)
        ax1.set_xlabel('Current Score', fontsize=12, fontweight='bold')
        ax1.set_title(f'BEFORE\n{before_label}', fontsize=14, fontweight='bold', color='#D32F2F')
        ax1.set_xlim(0, 100)
        for i, v in enumerate(before_values):
            ax1.text(v + 2, i, f'{v}%', va='center', fontweight='bold', fontsize=11)

        # After - Target State
        colors_after = ['#66BB6A'] * len(categories)
        ax2.barh(categories, after_values, color=colors_after, edgecolor='white', linewidth=2)
        ax2.set_xlabel('Target Score', fontsize=12, fontweight='bold')
        ax2.set_title(f'AFTER\n{after_label}', fontsize=14, fontweight='bold', color='#388E3C')
        ax2.set_xlim(0, 100)
        for i, v in enumerate(after_values):
            ax2.text(v + 2, i, f'{v}%', va='center', fontweight='bold', fontsize=11)

        fig.suptitle(f'{company}: {title}', fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(file_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        if file_path.exists():
            quality = self._validate_image_quality(file_path)
            return GeneratedAsset(
                filename=filename,
                type="chart",
                title=f"{title} - Before/After",
                description=f"Comparison of {company}'s state before and after transformation",
                file_path=file_path,
                generation_method="adaptive:transformation_chart",
                quality_score=quality,
            )
        return None

    async def _generate_roi_timeline_chart(self, input_data: VisualAssetInput, chart_data: dict, index: int) -> Optional[GeneratedAsset]:
        """Generate ROI Timeline chart dynamically."""
        timeline = chart_data.get("timeline", {})
        topic_short = chart_data.get("topic_short", "Strategic")
        company = chart_data.get("company", "TUI")

        breakeven = timeline.get("breakeven_month", 15)
        total_months = timeline.get("total_months", 36)
        roi_pct = timeline.get("roi_percentage", 250)
        title = timeline.get("title", "Implementation ROI")

        safe_topic = topic_short.lower().replace(' ', '_')[:20]
        filename = f"chart_3_{safe_topic}_roi_timeline.png"
        file_path = self.shared_state.visuals_dir / filename

        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np

        fig, ax = plt.subplots(figsize=(12, 7))

        # Generate timeline data based on parameters
        num_points = 7
        months = [f'M{int(i * total_months / (num_points-1))}' for i in range(num_points)]
        investment = [100, 85, 70, 50, 30, 15, 10]
        returns = [0, roi_pct * 0.05, roi_pct * 0.15, roi_pct * 0.3, roi_pct * 0.5, roi_pct * 0.7, roi_pct]

        x = np.arange(len(months))
        breakeven_x = (breakeven / total_months) * (num_points - 1)

        ax.fill_between(x, investment, alpha=0.3, color='#E57373', label='Cumulative Investment')
        ax.fill_between(x, returns, alpha=0.3, color='#66BB6A', label='Cumulative Returns')
        ax.plot(x, investment, 'o-', color='#D32F2F', linewidth=2.5, markersize=8, label='Investment Trajectory')
        ax.plot(x, returns, 'o-', color='#388E3C', linewidth=2.5, markersize=8, label='ROI Trajectory')

        ax.axvline(x=breakeven_x, color='#1976D2', linestyle='--', linewidth=2, alpha=0.8)
        ax.annotate(f'BREAKEVEN\nMONTH {breakeven}', xy=(breakeven_x, max(returns)*0.3), fontsize=11, fontweight='bold',
                    ha='center', color='#1976D2',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#E3F2FD', edgecolor='#1976D2'))

        ax.annotate(f'{roi_pct}% ROI\nby Month {total_months}', xy=(num_points-1, roi_pct), fontsize=12, fontweight='bold',
                    ha='center', color='#388E3C',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#E8F5E9', edgecolor='#388E3C'))

        ax.set_xticks(x)
        ax.set_xticklabels(months, fontsize=11)
        ax.set_xlabel('Implementation Timeline', fontsize=12, fontweight='bold')
        ax.set_ylabel('Value Index (Base = 100)', fontsize=12, fontweight='bold')
        ax.set_title(f'{title}: ROI Trajectory', fontsize=16, fontweight='bold', pad=20)
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_ylim(0, roi_pct * 1.15)

        plt.tight_layout()
        plt.savefig(file_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        if file_path.exists():
            quality = self._validate_image_quality(file_path)
            return GeneratedAsset(
                filename=filename,
                type="timeline",
                title=f"{title} Timeline",
                description=f"Investment trajectory and ROI projections for {topic_short}",
                file_path=file_path,
                generation_method="adaptive:roi_timeline",
                quality_score=quality,
            )
        return None

    async def _generate_competitive_chart(self, input_data: VisualAssetInput, chart_data: dict, index: int) -> Optional[GeneratedAsset]:
        """Generate competitive advantage comparison chart dynamically."""
        comp = chart_data.get("competitive", {})
        topic_short = chart_data.get("topic_short", "Strategic")
        company = chart_data.get("company", "TUI")

        protagonist = comp.get("protagonist", company)
        competitor = comp.get("competitor", "Competitors")
        categories = comp.get("categories", ["Cap 1", "Cap 2", "Cap 3", "Cap 4", "Cap 5"])
        prot_scores = comp.get("protagonist_scores", [85, 80, 75, 70, 85])
        comp_scores = comp.get("competitor_scores", [50, 55, 45, 60, 40])
        moat_label = comp.get("moat_label", "Competitive Advantage")
        title = comp.get("title", "Competitive Position")

        safe_topic = topic_short.lower().replace(' ', '_')[:20]
        filename = f"chart_4_{safe_topic}_competitive.png"
        file_path = self.shared_state.visuals_dir / filename

        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np

        fig, ax = plt.subplots(figsize=(12, 7))

        # Format categories for display (add line breaks if needed)
        display_cats = [cat.replace(' ', '\n') if len(cat) > 15 else cat for cat in categories]

        x = np.arange(len(categories))
        width = 0.35

        bars1 = ax.bar(x - width/2, prot_scores, width, label=protagonist,
                       color='#1976D2', edgecolor='white', linewidth=2)
        bars2 = ax.bar(x + width/2, comp_scores, width, label=competitor,
                       color='#FF7043', edgecolor='white', linewidth=2)

        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f'{int(height)}%', xy=(bar.get_x() + bar.get_width()/2, height),
                        xytext=(0, 3), textcoords="offset points", ha='center', va='bottom',
                        fontweight='bold', fontsize=10, color='#1976D2')
        for bar in bars2:
            height = bar.get_height()
            ax.annotate(f'{int(height)}%', xy=(bar.get_x() + bar.get_width()/2, height),
                        xytext=(0, 3), textcoords="offset points", ha='center', va='bottom',
                        fontweight='bold', fontsize=10, color='#FF7043')

        # Add moat annotation at highest point
        max_score = max(prot_scores)
        max_idx = prot_scores.index(max_score)
        ax.annotate(f'{moat_label}', xy=(max_idx - width/2, max_score), xytext=(max_idx - width/2, max_score + 10),
                    fontsize=11, fontweight='bold', ha='center', color='#1565C0',
                    arrowprops=dict(arrowstyle='->', color='#1565C0', lw=2),
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#E3F2FD', edgecolor='#1565C0'))

        ax.set_ylabel('Capability Score (%)', fontsize=12, fontweight='bold')
        ax.set_title(f'{protagonist}\'s {title}', fontsize=16, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(display_cats, fontsize=10)
        ax.legend(loc='upper right', fontsize=11)
        ax.set_ylim(0, max(max(prot_scores), max(comp_scores)) * 1.3)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()
        plt.savefig(file_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        if file_path.exists():
            quality = self._validate_image_quality(file_path)
            return GeneratedAsset(
                filename=filename,
                type="chart",
                title=f"{protagonist} vs {competitor}",
                description=f"Comparison of {protagonist}'s capabilities vs {competitor}",
                file_path=file_path,
                generation_method="adaptive:competitive_chart",
                quality_score=quality,
            )
        return None

    async def _generate_roadmap_chart(self, input_data: VisualAssetInput, chart_data: dict, index: int) -> Optional[GeneratedAsset]:
        """Generate implementation roadmap chart dynamically."""
        roadmap = chart_data.get("roadmap", {})
        topic_short = chart_data.get("topic_short", "Strategic")
        company = chart_data.get("company", "TUI")

        phases = roadmap.get("phases", [
            {"name": "Phase 1: Foundation", "duration": 6, "items": ["Assessment", "Planning", "Quick Wins"]},
            {"name": "Phase 2: Build", "duration": 12, "items": ["Implementation", "Integration", "Testing"]},
            {"name": "Phase 3: Scale", "duration": 18, "items": ["Rollout", "Optimization", "Expansion"]}
        ])
        milestones = roadmap.get("milestones", [
            {"month": 6, "label": "Foundation"},
            {"month": 18, "label": "Core Live"},
            {"month": 36, "label": "Complete"}
        ])
        title = roadmap.get("title", "Implementation Roadmap")

        safe_topic = topic_short.lower().replace(' ', '_')[:20]
        filename = f"chart_5_{safe_topic}_roadmap.png"
        file_path = self.shared_state.visuals_dir / filename

        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(14, 8))

        colors = ['#1976D2', '#388E3C', '#F57C00']
        y_positions = list(range(len(phases), 0, -1))
        start = 0

        for i, (phase, y_pos) in enumerate(zip(phases, y_positions)):
            duration = phase.get("duration", 6)
            phase_name = phase.get("name", f"Phase {i+1}")
            items = phase.get("items", [])

            color = colors[i % len(colors)]
            ax.barh(y_pos, duration, left=start, height=0.6,
                    color=color, alpha=0.8, edgecolor='white', linewidth=2)

            ax.text(start + duration/2, y_pos, f'{phase_name}\n({start}-{start+duration} months)',
                    ha='center', va='center', fontsize=10, fontweight='bold', color='white')

            for j, item in enumerate(items[:3]):
                ax.text(start + 0.5, y_pos - 0.35 - (j * 0.12), f'• {item}',
                        fontsize=8, color='#333', va='top')

            start += duration

        for ms in milestones:
            month = ms.get("month", 6)
            label = ms.get("label", "Milestone")
            ax.axvline(x=month, color='#D32F2F', linestyle='--', linewidth=2, alpha=0.7)
            ax.annotate(label, xy=(month, max(y_positions) + 0.5), fontsize=9, fontweight='bold', ha='center',
                        color='#D32F2F', bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFEBEE', edgecolor='#D32F2F'))

        total_duration = sum(p.get("duration", 6) for p in phases)
        ax.set_xlim(-1, total_duration + 5)
        ax.set_ylim(0, max(y_positions) + 1)
        ax.set_xlabel('Months from Start', fontsize=12, fontweight='bold')
        ax.set_yticks([])
        ax.set_title(f'{title}: {topic_short}', fontsize=16, fontweight='bold', pad=20)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)

        plt.tight_layout()
        plt.savefig(file_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        if file_path.exists():
            quality = self._validate_image_quality(file_path)
            return GeneratedAsset(
                filename=filename,
                type="timeline",
                title=title,
                description=f"Phased implementation approach for {topic_short}",
                file_path=file_path,
                generation_method="adaptive:roadmap_chart",
                quality_score=quality,
            )
        return None

    # ============== DYNAMIC VISUALIZATION METHODS ==============

    async def _analyze_visualization_opportunities(
        self, input_data: VisualAssetInput
    ) -> list[VisualOpportunity]:
        """Use LLM to analyze article and identify visualization opportunities."""
        prompt = f"""Analyze this article and identify 3-5 visualization opportunities.

ARTICLE TITLE: {input_data.article_title}
TOPIC: {input_data.topic}

ARTICLE CONTENT:
{input_data.article_content[:4000]}

For each visualization opportunity, provide:
1. type: one of "comparison", "timeline", "architecture", "data"
2. title: short title for the chart
3. description: what it should show
4. section: which article section it relates to
5. data_points: list of specific numbers/entities to visualize (extract from article!)
6. suggested_style: "horizontal_bar", "vertical_bar", "line", "area", "diagram"

IMPORTANT: Extract ACTUAL data from the article. Do NOT make up numbers.
If the article mentions "$50 billion market by 2027", use those exact numbers.

Return as JSON array:
[
  {{
    "type": "comparison",
    "title": "Market Share Comparison",
    "description": "Compare market positions of key players",
    "section": "Core Analysis",
    "data_points": ["Company A: $500M", "Company B: $300M"],
    "suggested_style": "horizontal_bar"
  }}
]
"""
        try:
            response = await self._llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            # Extract JSON from response
            import re
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                opportunities_data = json.loads(json_match.group())
                return [
                    VisualOpportunity(
                        type=opp.get("type", "data"),
                        title=opp.get("title", "Chart"),
                        description=opp.get("description", ""),
                        section=opp.get("section", ""),
                        data_points=opp.get("data_points", []),
                        suggested_style=opp.get("suggested_style", "horizontal_bar"),
                    )
                    for opp in opportunities_data
                ]
        except Exception as e:
            self.logger.warning(f"LLM visualization analysis failed: {e}")

        return []

    def _get_default_opportunities(self, input_data: VisualAssetInput) -> list[VisualOpportunity]:
        """Fallback: Generate generic opportunities based on topic keywords."""
        opportunities = []
        topic_lower = input_data.topic.lower()

        # Always add a comparison chart
        opportunities.append(VisualOpportunity(
            type="comparison",
            title=f"Key Players in {input_data.topic[:30]}",
            description="Comparison of major entities discussed in the article",
            section="Core Analysis",
            data_points=["Entity A", "Entity B", "Entity C"],
            suggested_style="horizontal_bar",
        ))

        # Add timeline if topic suggests temporal data
        if any(word in topic_lower for word in ["trend", "growth", "market", "future", "2025", "2026", "2027"]):
            opportunities.append(VisualOpportunity(
                type="timeline",
                title="Market Evolution Timeline",
                description="Projected growth trajectory",
                section="Strategic Implications",
                data_points=["2024", "2025", "2026", "2027"],
                suggested_style="line",
            ))

        # Add architecture if topic suggests systems/models
        if any(word in topic_lower for word in ["model", "architecture", "system", "integration", "platform"]):
            opportunities.append(VisualOpportunity(
                type="architecture",
                title="System Architecture Overview",
                description="Key components and relationships",
                section="Context Setting",
                data_points=["Component A", "Component B", "Component C"],
                suggested_style="diagram",
            ))

        return opportunities[:self.MAX_ASSETS]

    async def _generate_from_opportunity(
        self,
        opportunity: VisualOpportunity,
        input_data: VisualAssetInput,
        index: int,
    ) -> Optional[GeneratedAsset]:
        """Generate a visualization from an identified opportunity."""
        safe_title = "".join(c if c.isalnum() or c in "._- " else "_" for c in opportunity.title)[:40]
        filename = f"chart_{index+1}_{safe_title.lower().replace(' ', '_')}.png"
        file_path = self.shared_state.visuals_dir / filename

        # Parse data points into structured data
        data = await self._extract_chart_data(opportunity, input_data)

        if opportunity.type == "timeline" or opportunity.suggested_style == "line":
            return self._generate_timeline_from_data(data, opportunity, file_path)
        elif opportunity.type == "architecture" or opportunity.suggested_style == "diagram":
            return self._generate_architecture_from_data(data, opportunity, file_path)
        else:
            return self._generate_chart_from_data(data, opportunity, file_path)

    async def _extract_chart_data(
        self, opportunity: VisualOpportunity, input_data: VisualAssetInput
    ) -> dict:
        """Use LLM to extract structured chart data from opportunity."""
        prompt = f"""Extract chart data from these data points for a {opportunity.suggested_style} chart.

Title: {opportunity.title}
Description: {opportunity.description}
Raw data points: {opportunity.data_points}

Article context (for verification):
{input_data.article_content[:2000]}

Return JSON with:
- labels: list of category/entity names
- values: list of numeric values (same order as labels)
- xlabel: label for x-axis
- ylabel: label for y-axis
- highlight: which label to highlight (optional)

Example:
{{"labels": ["Company A", "Company B"], "values": [500, 300], "xlabel": "Investment ($M)", "highlight": "Company A"}}

If you cannot extract numeric values, estimate reasonable ones based on context.
Return ONLY the JSON object, no explanation.
"""
        try:
            response = await self._llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            self.logger.warning(f"Data extraction failed: {e}")

        # Fallback: create dummy data
        return {
            "labels": opportunity.data_points[:5] if opportunity.data_points else ["A", "B", "C"],
            "values": [100, 75, 50, 25, 10][:len(opportunity.data_points) or 3],
            "xlabel": "Value",
            "ylabel": "Category",
        }

    def _generate_chart_from_data(
        self, data: dict, opportunity: VisualOpportunity, file_path: Path
    ) -> Optional[GeneratedAsset]:
        """Generate chart from extracted data."""
        chart_type = "horizontal_bar" if opportunity.suggested_style in ["horizontal_bar", "bar"] else "vertical_bar"

        result_path = self.tools["generate_chart"](
            chart_type=chart_type,
            data=data,
            title=opportunity.title,
            output_path=file_path,
            subtitle=opportunity.description[:100] if opportunity.description else None,
            highlight=data.get("highlight"),
        )

        if result_path and result_path.exists():
            quality = self._validate_image_quality(result_path)
            return GeneratedAsset(
                filename=file_path.name,
                type="chart",
                title=opportunity.title,
                description=opportunity.description,
                file_path=result_path,
                generation_method="skill:visual_generation.charts (dynamic)",
                quality_score=quality,
            )
        return None

    def _generate_timeline_from_data(
        self, data: dict, opportunity: VisualOpportunity, file_path: Path
    ) -> Optional[GeneratedAsset]:
        """Generate timeline from extracted data."""
        labels = data.get("labels", [])
        values = data.get("values", [])

        # Convert labels to years if they look like years
        try:
            years = [int(l) for l in labels if str(l).isdigit()]
        except:
            years = list(range(2024, 2024 + len(values)))

        milestones = [
            {"year": y, "value": v, "label": "" if i != len(years)//2 else "Key Point"}
            for i, (y, v) in enumerate(zip(years, values))
        ]

        result_path = self.tools["generate_timeline"](
            milestones=milestones,
            output_path=file_path,
            title=opportunity.title,
            subtitle=opportunity.description[:100] if opportunity.description else None,
        )

        if result_path and result_path.exists():
            quality = self._validate_image_quality(result_path)
            return GeneratedAsset(
                filename=file_path.name,
                type="timeline",
                title=opportunity.title,
                description=opportunity.description,
                file_path=result_path,
                generation_method="skill:visual_generation.timelines (dynamic)",
                quality_score=quality,
            )
        return None

    def _generate_architecture_from_data(
        self, data: dict, opportunity: VisualOpportunity, file_path: Path
    ) -> Optional[GeneratedAsset]:
        """Generate architecture diagram from extracted data."""
        labels = data.get("labels", ["Component A", "Component B", "Component C"])

        # Build entities for comparison diagram
        mid = len(labels) // 2
        entities = {
            "left": {
                "name": labels[0] if labels else "Model A",
                "components": labels[1:mid+1] if len(labels) > 1 else ["Part 1", "Part 2"],
            },
            "right": {
                "name": labels[mid+1] if len(labels) > mid+1 else "Model B",
                "components": labels[mid+2:] if len(labels) > mid+2 else ["Part 3", "Part 4"],
            }
        }

        original_cwd = os.getcwd()
        os.chdir(self.shared_state.visuals_dir)

        try:
            result_path = self.tools["generate_architecture"](
                diagram_type="comparison",
                entities=entities,
                output_path=file_path.stem,  # Without extension
                title=opportunity.title,
            )

            if result_path and result_path.exists():
                quality = self._validate_image_quality(result_path)
                return GeneratedAsset(
                    filename=result_path.name,
                    type="architecture",
                    title=opportunity.title,
                    description=opportunity.description,
                    file_path=result_path,
                    generation_method="skill:visual_generation.architecture (dynamic)",
                    quality_score=quality,
                )
        except Exception as e:
            self.logger.warning(f"Architecture generation failed: {e}")
        finally:
            os.chdir(original_cwd)

        return None

    # ============== LEGACY METHODS (kept for backwards compatibility) ==============

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
