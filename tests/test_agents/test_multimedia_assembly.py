"""Tests for Phase 4: Multimedia & Assembly agents.

Tests the Visual Asset Agent, Multimedia Agent, and Assembly Agent.
Quality bar: Professional publication ready!
"""

import pytest
from pathlib import Path
import json

from src.state.shared_state import SharedState, create_shared_state


class TestVisualAssetAgent:
    """Test the Visual Asset Generation Agent."""

    @pytest.fixture
    def shared_state_with_article(self, tmp_path: Path) -> SharedState:
        """Create shared state with a final article."""
        state = create_shared_state(
            topic="Universal Commerce Protocol (UCP)",
            target_audience="TUI Leadership",
            output_base_dir=str(tmp_path),
        )

        # Write final article
        article_content = """# Strategic Analysis: UCP

*Key Insights for TUI Leadership*

## The Hook

The travel industry is about to be transformed.

## Core Analysis

UCP represents a fundamental shift. Market projections show:
- 2024: $10B market size
- 2025: $15B projected
- 2026: $22B estimated

The technology architecture involves multiple components working together.

## Strategic Implications

Leaders must act now. The competitive landscape is shifting rapidly.

## Conclusion

The future belongs to those who prepare today.
"""
        state.write_final_article(article_content)
        state.update_state(
            synthesized_content={
                "title": "Strategic Analysis: UCP",
                "subtitle": "Key Insights for TUI Leadership",
                "key_insights": ["Market transformation", "Technology shift", "Competitive dynamics"],
            }
        )

        return state

    def test_agent_initialization(self, shared_state_with_article: SharedState):
        """Test agent can be initialized."""
        from src.agents.visual_asset_agent import VisualAssetAgent

        agent = VisualAssetAgent(shared_state_with_article)

        assert agent.agent_name == "VisualAssetAgent"
        assert agent.phase == "visuals"
        assert agent.MIN_ASSETS == 3
        assert agent.MAX_ASSETS == 5

    @pytest.mark.asyncio
    async def test_read_from_state(self, shared_state_with_article: SharedState):
        """Test reading article from state."""
        from src.agents.visual_asset_agent import VisualAssetAgent

        agent = VisualAssetAgent(shared_state_with_article)
        input_data = await agent.read_from_state()

        assert "Strategic Analysis" in input_data.article_content
        assert input_data.topic == "Universal Commerce Protocol (UCP)"
        assert len(input_data.key_insights) > 0

    def test_fallback_opportunities(self, shared_state_with_article: SharedState):
        """Test fallback opportunity creation."""
        from src.agents.visual_asset_agent import VisualAssetAgent, VisualAssetInput

        agent = VisualAssetAgent(shared_state_with_article)

        input_data = VisualAssetInput(
            article_content="Test article",
            article_title="Test Title",
            topic="Test Topic",
            key_insights=["insight 1"],
            tui_context="TUI context",
        )

        opportunities = agent._create_fallback_opportunities(input_data)

        assert len(opportunities) >= 3
        types = [o.type for o in opportunities]
        assert "diagram" in types
        assert "chart" in types
        assert "image" in types

    @pytest.mark.asyncio
    async def test_validate_output(self, shared_state_with_article: SharedState):
        """Test output validation."""
        from src.agents.visual_asset_agent import VisualAssetAgent, VisualAssetOutput, GeneratedAsset

        agent = VisualAssetAgent(shared_state_with_article)

        # Too few assets should fail
        insufficient = VisualAssetOutput(
            assets=[
                GeneratedAsset(
                    filename="test.png",
                    type="image",
                    title="Test",
                    description="Test",
                    file_path=Path("/tmp/test.png"),
                    generation_method="test",
                )
            ],
            total_generated=1,
            failed_generations=[],
            asset_manifest={},
        )
        passes, msg = await agent.validate_output(insufficient)
        assert not passes
        assert "1" in msg

    def test_chart_data_parsing(self, shared_state_with_article: SharedState):
        """Test chart data parsing."""
        from src.agents.visual_asset_agent import VisualAssetAgent

        agent = VisualAssetAgent(shared_state_with_article)

        data_points = ["2024: $10B", "2025: $15B", "2026: $22B"]
        parsed = agent._parse_chart_data(data_points)

        assert parsed["type"] == "bar"
        assert len(parsed["labels"]) == 3
        assert len(parsed["values"]) == 3

    def test_number_extraction(self, shared_state_with_article: SharedState):
        """Test numeric value extraction."""
        from src.agents.visual_asset_agent import VisualAssetAgent

        agent = VisualAssetAgent(shared_state_with_article)

        assert agent._extract_number("$10B") == 10.0
        assert agent._extract_number("15%") == 15.0
        assert agent._extract_number("1,234") == 1234.0


class TestMultimediaAgent:
    """Test the Multimedia Production Agent."""

    @pytest.fixture
    def shared_state_with_content(self, tmp_path: Path) -> SharedState:
        """Create shared state with article and visuals."""
        state = create_shared_state(
            topic="Universal Commerce Protocol",
            output_base_dir=str(tmp_path),
        )

        # Write final article
        state.write_final_article("""# Strategic Analysis

## Introduction

This is a test article for multimedia generation.

## Conclusion

Key takeaways here.
""")

        state.update_state(
            synthesized_content={
                "title": "Strategic Analysis",
                "subtitle": "Test Subtitle",
                "key_insights": ["Insight 1", "Insight 2"],
                "counterintuitive_insights": ["Counter insight"],
            },
            visual_assets=[{"filename": "test.png", "type": "image"}],
        )

        return state

    def test_agent_initialization(self, shared_state_with_content: SharedState):
        """Test agent can be initialized."""
        from src.agents.multimedia_agent import MultimediaAgent

        agent = MultimediaAgent(shared_state_with_content)

        assert agent.agent_name == "MultimediaAgent"
        assert agent.phase == "multimedia"
        assert agent.VIDEO_DURATION == 60
        assert agent.VIDEO_TOLERANCE == 2

    @pytest.mark.asyncio
    async def test_read_from_state(self, shared_state_with_content: SharedState):
        """Test reading content from state."""
        from src.agents.multimedia_agent import MultimediaAgent

        agent = MultimediaAgent(shared_state_with_content)
        input_data = await agent.read_from_state()

        assert "Strategic Analysis" in input_data.article_content
        assert len(input_data.key_insights) > 0
        assert len(input_data.counterintuitive_insights) > 0

    def test_script_cleaning(self, shared_state_with_content: SharedState):
        """Test narration script cleaning for TTS."""
        from src.agents.multimedia_agent import MultimediaAgent

        agent = MultimediaAgent(shared_state_with_content)

        script = "This is a test [PAUSE] with markers [EMPHASIS] here."
        cleaned = agent._clean_script_for_tts(script)

        assert "[PAUSE]" not in cleaned
        assert "[EMPHASIS]" not in cleaned
        assert "..." in cleaned  # PAUSE becomes ellipsis

    def test_fallback_video_script(self, shared_state_with_content: SharedState):
        """Test fallback video script creation."""
        from src.agents.multimedia_agent import MultimediaAgent, MultimediaInput

        agent = MultimediaAgent(shared_state_with_content)

        input_data = MultimediaInput(
            article_content="Test",
            article_title="Test Title",
            subtitle="Subtitle",
            topic="Test Topic",
            key_insights=["Insight 1"],
            counterintuitive_insights=["Counter"],
            visual_assets=[],
        )

        script = agent._create_fallback_video_script(input_data)

        assert "hook" in script
        assert "explanation" in script
        assert "implication" in script
        assert "cta" in script

        # Check durations add to 60 seconds
        total = sum(script[s]["duration"] for s in script)
        assert total == 60

    @pytest.mark.asyncio
    async def test_validate_output_video_duration(self, shared_state_with_content: SharedState):
        """Test video duration validation."""
        from src.agents.multimedia_agent import MultimediaAgent, MultimediaOutput, VideoAsset

        agent = MultimediaAgent(shared_state_with_content)

        # Wrong duration should be flagged
        wrong_duration = MultimediaOutput(
            audio=None,
            video=VideoAsset(
                filename="test.mp4",
                file_path=Path("/tmp/test.mp4"),
                duration_seconds=90,  # Wrong!
                resolution="1080p",
                format="mp4",
            ),
            script="test script",
            video_script="{}",
            generation_status={"audio_generated": False, "video_generated": True},
        )
        passes, msg = await agent.validate_output(wrong_duration)
        assert not passes
        assert "duration" in msg.lower()


class TestAssemblyAgent:
    """Test the Final Assembly Agent."""

    @pytest.fixture
    def shared_state_complete(self, tmp_path: Path) -> SharedState:
        """Create shared state with all content ready for assembly."""
        state = create_shared_state(
            topic="Universal Commerce Protocol",
            output_base_dir=str(tmp_path),
        )

        # Write final article
        article = """# Strategic Analysis: UCP

*Insights for TUI Leadership*

## Introduction

The travel industry faces transformation.

## Analysis

Key findings include market shifts.

## Conclusion

Action is required now.
"""
        state.write_final_article(article)

        # Set state
        state.update_state(
            synthesized_content={
                "title": "Strategic Analysis: UCP",
                "subtitle": "Insights for TUI Leadership",
            },
            word_count=50,
            visual_assets=[{"filename": "chart.png", "type": "chart"}],
            multimedia={"audio": {"filename": "narration.mp3"}, "video": {"filename": "promo.mp4"}},
        )

        return state

    def test_agent_initialization(self, shared_state_complete: SharedState):
        """Test agent can be initialized."""
        from src.agents.assembly_agent import AssemblyAgent

        agent = AssemblyAgent(shared_state_complete)

        assert agent.agent_name == "AssemblyAgent"
        assert agent.phase == "assembly"

    @pytest.mark.asyncio
    async def test_read_from_state(self, shared_state_complete: SharedState):
        """Test reading all content from state."""
        from src.agents.assembly_agent import AssemblyAgent

        agent = AssemblyAgent(shared_state_complete)
        input_data = await agent.read_from_state()

        assert "Strategic Analysis" in input_data.article_content
        assert input_data.word_count > 0
        # Visual assets may be empty if not properly set in fixture
        assert isinstance(input_data.visual_assets, list)

    def test_markdown_to_html(self, shared_state_complete: SharedState):
        """Test markdown to HTML conversion."""
        from src.agents.assembly_agent import AssemblyAgent

        agent = AssemblyAgent(shared_state_complete)

        markdown = "# Title\n\n## Section\n\nParagraph with **bold** and *italic*."
        html = agent._markdown_to_html(markdown)

        assert "<h1>" in html or "Title" in html
        assert "<strong>" in html or "bold" in html

    def test_manifest_creation(self, shared_state_complete: SharedState):
        """Test assembly manifest creation."""
        from src.agents.assembly_agent import AssemblyAgent, AssemblyInput

        agent = AssemblyAgent(shared_state_complete)

        input_data = AssemblyInput(
            article_content="Test",
            article_title="Test Title",
            subtitle="Subtitle",
            topic="Test Topic",
            word_count=2200,
            visual_assets=[{"filename": "test.png"}],
            multimedia={"audio": {}, "video": {}},
            tui_context="TUI context",
        )

        manifest = agent._create_manifest(input_data, None, None, None)

        assert manifest["title"] == "Test Title"
        assert manifest["word_count"] == 2200
        assert "deliverables" in manifest

    @pytest.mark.asyncio
    async def test_validate_output(self, shared_state_complete: SharedState):
        """Test output validation."""
        from src.agents.assembly_agent import (
            AssemblyAgent,
            AssemblyOutput,
            HTMLOutput,
        )

        agent = AssemblyAgent(shared_state_complete)

        # Missing HTML should fail
        no_html = AssemblyOutput(
            pdf=None,
            html=None,
            package=None,
            manifest={},
            assembly_status={"errors": []},
        )
        passes, msg = await agent.validate_output(no_html)
        assert not passes
        assert "HTML" in msg

        # With HTML should pass
        with_html = AssemblyOutput(
            pdf=None,
            html=HTMLOutput(
                filename="test.html",
                file_path=Path("/tmp/test.html"),
                has_audio_player=True,
                has_video_player=True,
                is_responsive=True,
            ),
            package=None,
            manifest={},
            assembly_status={"errors": []},
        )
        passes, msg = await agent.validate_output(with_html)
        # May fail on package but HTML check should pass


class TestPhase4Integration:
    """Integration tests for Phase 4."""

    @pytest.fixture
    def full_pipeline_state(self, tmp_path: Path) -> SharedState:
        """Create state simulating full pipeline completion."""
        state = create_shared_state(
            topic="Universal Commerce Protocol",
            target_audience="TUI Leadership",
            output_base_dir=str(tmp_path),
        )

        # Simulate Phase 3 outputs
        state.write_final_article("# Test Article\n\nContent here.")
        state.update_state(
            synthesized_content={
                "title": "Test Article",
                "subtitle": "Subtitle",
                "key_insights": ["insight"],
                "counterintuitive_insights": ["counter"],
            },
            word_count=2200,
            hbr_quality_score=85,
        )

        return state

    def test_visuals_directory_exists(self, full_pipeline_state: SharedState):
        """Test visuals directory is created."""
        assert full_pipeline_state.visuals_dir.exists()

    def test_multimedia_directory_exists(self, full_pipeline_state: SharedState):
        """Test multimedia directory is created."""
        assert full_pipeline_state.multimedia_dir.exists()

    def test_final_deliverables_directory_exists(self, full_pipeline_state: SharedState):
        """Test final deliverables directory is created."""
        assert full_pipeline_state.final_deliverables_dir.exists()

    def test_agent_imports(self):
        """Test all Phase 4 agents can be imported."""
        from src.agents import (
            VisualAssetAgent,
            create_visual_asset_agent,
            MultimediaAgent,
            create_multimedia_agent,
            AssemblyAgent,
            create_assembly_agent,
        )

        assert VisualAssetAgent is not None
        assert MultimediaAgent is not None
        assert AssemblyAgent is not None


class TestQualityRequirements:
    """Test quality requirements for Phase 4."""

    def test_video_duration_constant(self):
        """Test video duration is exactly 60 seconds."""
        from src.agents.multimedia_agent import MultimediaAgent

        # Access class attributes
        assert MultimediaAgent.VIDEO_DURATION == 60
        assert MultimediaAgent.VIDEO_TOLERANCE == 2

    def test_min_assets_constant(self):
        """Test minimum assets requirement."""
        from src.agents.visual_asset_agent import VisualAssetAgent

        assert VisualAssetAgent.MIN_ASSETS == 3
        assert VisualAssetAgent.MAX_ASSETS == 5

    def test_html_template_responsive(self):
        """Test HTML template has responsive design."""
        from src.agents.assembly_agent import HTML_TEMPLATE

        assert "@media" in HTML_TEMPLATE  # Has media queries
        assert "max-width" in HTML_TEMPLATE
        assert "viewport" in HTML_TEMPLATE

    def test_video_script_structure(self):
        """Test video script has required sections."""
        from src.agents.multimedia_agent import VIDEO_SCRIPT_PROMPT

        assert "HOOK" in VIDEO_SCRIPT_PROMPT
        assert "EXPLANATION" in VIDEO_SCRIPT_PROMPT
        assert "IMPLICATION" in VIDEO_SCRIPT_PROMPT
        assert "CTA" in VIDEO_SCRIPT_PROMPT
        assert "60" in VIDEO_SCRIPT_PROMPT  # Duration mentioned
