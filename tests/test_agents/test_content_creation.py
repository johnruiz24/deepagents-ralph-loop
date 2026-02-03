"""Tests for Phase 3: Content Creation agents.

Tests the Synthesis Agent and HBR Editor Agent.
Quality bar: Harvard Business Review level - NON-NEGOTIABLE!
"""

import pytest
from pathlib import Path
import json

from src.state.shared_state import SharedState, create_shared_state


class TestSynthesisAgent:
    """Test the Synthesis & Narrative Agent."""

    @pytest.fixture
    def shared_state_with_research(self, tmp_path: Path) -> SharedState:
        """Create shared state with mock research data."""
        state = create_shared_state(
            topic="Universal Commerce Protocol (UCP)",
            target_audience="TUI Leadership and Strategy Teams",
            key_concepts=["Agentic AI", "Commerce Protocols", "Travel Technology"],
            output_base_dir=str(tmp_path),
        )

        # Add mock research data
        mock_research = {
            "Technical Architecture": [
                {
                    "filename": "article_1.md",
                    "content": "UCP enables AI agents to autonomously execute commerce transactions...",
                }
            ],
            "Business Implications": [
                {
                    "filename": "article_2.md",
                    "content": "Travel industry stands to benefit significantly from protocol standardization...",
                }
            ],
        }

        for subtopic, articles in mock_research.items():
            for article in articles:
                state.write_research_data(
                    subtopic=subtopic,
                    filename=article["filename"],
                    content=article["content"],
                )

        # Add TUI strategy summary
        state.write_tui_strategy_summary("""
# TUI Group Strategic Analysis

## Business Model
TUI operates as an integrated tourism group.

## Strategic Priorities
1. Digital transformation
2. Customer experience
3. Sustainability
""")

        return state

    def test_agent_initialization(self, shared_state_with_research: SharedState):
        """Test agent can be initialized."""
        from src.agents.synthesis_agent import SynthesisAgent

        agent = SynthesisAgent(shared_state_with_research)

        assert agent.agent_name == "SynthesisAgent"
        assert agent.phase == "synthesis"
        assert agent.MIN_WORDS == 2000
        assert agent.MAX_WORDS == 2500

    @pytest.mark.asyncio
    async def test_read_from_state(self, shared_state_with_research: SharedState):
        """Test reading research data from state."""
        from src.agents.synthesis_agent import SynthesisAgent

        agent = SynthesisAgent(shared_state_with_research)
        input_data = await agent.read_from_state()

        assert input_data.topic == "Universal Commerce Protocol (UCP)"
        assert input_data.target_audience == "TUI Leadership and Strategy Teams"
        assert len(input_data.research_data) > 0
        assert "TUI" in input_data.tui_strategy

    def test_word_count_constants(self, shared_state_with_research: SharedState):
        """Test word count constraints are correctly set."""
        from src.agents.synthesis_agent import SynthesisAgent

        agent = SynthesisAgent(shared_state_with_research)

        # Word count is NON-NEGOTIABLE!
        assert agent.MIN_WORDS == 2000
        assert agent.MAX_WORDS == 2500
        assert agent.TARGET_WORDS == 2200

    @pytest.mark.asyncio
    async def test_validate_output_word_count(self, shared_state_with_research: SharedState):
        """Test that validation catches word count issues."""
        from src.agents.synthesis_agent import SynthesisAgent, DraftArticle

        agent = SynthesisAgent(shared_state_with_research)

        # Too short should fail (with some tolerance for draft)
        short_draft = DraftArticle(
            title="Test",
            subtitle="Test subtitle",
            content="Too short " * 100,  # ~200 words
            word_count=200,
            sections=[],
            key_insights=[],
            counterintuitive_insights=[],
            citations=[],
            reading_time_minutes=1.0,
        )
        passes, msg = await agent.validate_output(short_draft)
        assert not passes
        assert "short" in msg.lower()

    @pytest.mark.asyncio
    async def test_validate_output_counterintuitive(self, shared_state_with_research: SharedState):
        """Test that validation checks for counterintuitive insights."""
        from src.agents.synthesis_agent import SynthesisAgent, DraftArticle

        agent = SynthesisAgent(shared_state_with_research)

        # No counterintuitive insights should fail
        no_insights_draft = DraftArticle(
            title="Test",
            subtitle="Test subtitle",
            content="Content " * 2200,
            word_count=2200,
            sections=[{"name": "Section 1"}, {"name": "Section 2"}, {"name": "Section 3"}, {"name": "Section 4"}],
            key_insights=["insight 1"],
            counterintuitive_insights=[],  # ESSENTIAL but missing!
            citations=[{"source": "test"}],
            reading_time_minutes=11.0,
        )
        passes, msg = await agent.validate_output(no_insights_draft)
        assert not passes
        assert "counterintuitive" in msg.lower()

    @pytest.mark.asyncio
    async def test_calculate_quality_score(self, shared_state_with_research: SharedState):
        """Test quality score calculation."""
        from src.agents.synthesis_agent import SynthesisAgent, DraftArticle

        agent = SynthesisAgent(shared_state_with_research)

        # Good draft should have high score
        good_draft = DraftArticle(
            title="Strategic Analysis",
            subtitle="Key insights for leaders",
            content="Content " * 2200,
            word_count=2200,
            sections=[{"name": f"Section {i}"} for i in range(5)],
            key_insights=[f"insight {i}" for i in range(5)],
            counterintuitive_insights=["counter 1", "counter 2"],
            citations=[{"source": "test"}],
            reading_time_minutes=11.0,
        )
        score = await agent.calculate_quality_score(good_draft)
        assert score >= 70  # Should be high quality


class TestHBREditorAgent:
    """Test the HBR Style Editor Agent."""

    @pytest.fixture
    def shared_state_with_draft(self, tmp_path: Path) -> SharedState:
        """Create shared state with a draft article."""
        state = create_shared_state(
            topic="Universal Commerce Protocol (UCP)",
            target_audience="TUI Leadership and Strategy Teams",
            output_base_dir=str(tmp_path),
        )

        # Write a mock draft article
        draft_content = """# Strategic Analysis: UCP

*Insights for TUI Leadership*

## The Hook

The travel industry is at a crossroads.

## Core Analysis

UCP represents a fundamental shift in how commerce happens.

## Strategic Implications

TUI must act now.

## Conclusion

The future is clear.
"""
        state.write_draft_article(draft_content)

        # Add synthesized content metadata
        state.update_state(
            synthesized_content={
                "title": "Strategic Analysis: UCP",
                "subtitle": "Insights for TUI Leadership",
                "key_insights": ["Key insight 1"],
                "counterintuitive_insights": ["Counter insight 1"],
            }
        )

        # Add TUI strategy summary
        state.write_tui_strategy_summary("# TUI Strategy\n\nDigital transformation focus.")

        return state

    def test_agent_initialization(self, shared_state_with_draft: SharedState):
        """Test agent can be initialized."""
        from src.agents.hbr_editor_agent import HBREditorAgent

        agent = HBREditorAgent(shared_state_with_draft)

        assert agent.agent_name == "HBREditorAgent"
        assert agent.phase == "editing"

    @pytest.mark.asyncio
    async def test_read_from_state(self, shared_state_with_draft: SharedState):
        """Test reading draft from state."""
        from src.agents.hbr_editor_agent import HBREditorAgent

        agent = HBREditorAgent(shared_state_with_draft)
        input_data = await agent.read_from_state()

        assert "Strategic Analysis" in input_data.draft_content
        assert input_data.topic == "Universal Commerce Protocol (UCP)"
        assert len(input_data.key_insights) > 0

    def test_word_count_constraints(self, shared_state_with_draft: SharedState):
        """Test HBR word count constraints."""
        from src.agents.hbr_editor_agent import HBREditorAgent

        agent = HBREditorAgent(shared_state_with_draft)

        # NON-NEGOTIABLE constraints
        assert agent.MIN_WORDS == 2000
        assert agent.MAX_WORDS == 2500
        assert agent.TARGET_WORDS == 2250

    @pytest.mark.asyncio
    async def test_validate_output_word_count(self, shared_state_with_draft: SharedState):
        """Test word count validation is strict."""
        from src.agents.hbr_editor_agent import HBREditorAgent, EditedArticle

        agent = HBREditorAgent(shared_state_with_draft)

        # Too short should fail
        short_article = EditedArticle(
            content="Short " * 500,  # ~500 words
            word_count=500,
            title="Test",
            subtitle="",
            readability_score=70.0,
            hbr_quality_score=80.0,
            editing_passes=["clarity", "tone"],
            improvements_made=["clarity improved"],
        )
        passes, msg = await agent.validate_output(short_article)
        assert not passes
        assert "short" in msg.lower()

        # Too long should fail
        long_article = EditedArticle(
            content="Long " * 3000,  # ~3000 words
            word_count=3000,
            title="Test",
            subtitle="",
            readability_score=70.0,
            hbr_quality_score=80.0,
            editing_passes=["clarity", "tone"],
            improvements_made=["clarity improved"],
        )
        passes, msg = await agent.validate_output(long_article)
        assert not passes
        assert "long" in msg.lower()

    @pytest.mark.asyncio
    async def test_validate_output_hbr_quality(self, shared_state_with_draft: SharedState):
        """Test HBR quality score validation."""
        from src.agents.hbr_editor_agent import HBREditorAgent, EditedArticle

        agent = HBREditorAgent(shared_state_with_draft)

        # Low quality should fail
        low_quality = EditedArticle(
            content="Content " * 2200,
            word_count=2200,
            title="Test",
            subtitle="",
            readability_score=70.0,
            hbr_quality_score=50.0,  # Below threshold
            editing_passes=["clarity"],
            improvements_made=[],
        )
        passes, msg = await agent.validate_output(low_quality)
        assert not passes
        assert "quality" in msg.lower()

    def test_readability_calculation(self, shared_state_with_draft: SharedState):
        """Test readability score calculation."""
        from src.agents.hbr_editor_agent import HBREditorAgent

        agent = HBREditorAgent(shared_state_with_draft)

        # Simple content should have high readability
        simple_content = "This is a simple sentence. Another simple sentence follows. Clear and direct."
        score = agent._calculate_readability(simple_content)
        assert score > 50  # Should be readable

    def test_title_subtitle_extraction(self, shared_state_with_draft: SharedState):
        """Test title and subtitle extraction from content."""
        from src.agents.hbr_editor_agent import HBREditorAgent

        agent = HBREditorAgent(shared_state_with_draft)

        content = """# My Title Here

*This is the subtitle*

Content follows here.
"""
        title, subtitle = agent._extract_title_subtitle(content)
        assert title == "My Title Here"
        assert subtitle == "This is the subtitle"

    def test_syllable_counting(self, shared_state_with_draft: SharedState):
        """Test syllable counting approximation."""
        from src.agents.hbr_editor_agent import HBREditorAgent

        agent = HBREditorAgent(shared_state_with_draft)

        assert agent._count_syllables("hello") >= 2
        assert agent._count_syllables("cat") == 1
        assert agent._count_syllables("beautiful") >= 3


class TestContentCreationIntegration:
    """Integration tests for Phase 3 content creation."""

    @pytest.fixture
    def full_shared_state(self, tmp_path: Path) -> SharedState:
        """Create shared state with all necessary data."""
        state = create_shared_state(
            topic="Universal Commerce Protocol (UCP)",
            target_audience="TUI Leadership and Strategy Teams",
            key_concepts=["Agentic AI", "Commerce Protocols"],
            output_base_dir=str(tmp_path),
        )

        # Add research data
        state.write_research_data(
            subtopic="Technical",
            filename="tech_1.md",
            content="Technical analysis of UCP architecture.",
        )

        # Add TUI strategy
        state.write_tui_strategy_summary("# TUI Strategy\n\nDigital transformation.")

        return state

    def test_synthesis_to_editing_flow(self, full_shared_state: SharedState):
        """Test that synthesis output can be read by editor."""
        # Write mock synthesis output
        draft_content = "# Test Article\n\n*Subtitle*\n\n" + "Content. " * 500
        full_shared_state.write_draft_article(draft_content)

        full_shared_state.update_state(
            synthesized_content={
                "title": "Test Article",
                "subtitle": "Subtitle",
                "key_insights": ["insight 1"],
                "counterintuitive_insights": ["counter 1"],
            }
        )

        # Editor should be able to read it
        from src.agents.hbr_editor_agent import HBREditorAgent

        editor = HBREditorAgent(full_shared_state)
        # This should not raise
        import asyncio
        input_data = asyncio.get_event_loop().run_until_complete(editor.read_from_state())

        assert input_data.draft_content == draft_content
        assert len(input_data.key_insights) > 0

    def test_content_directories_exist(self, full_shared_state: SharedState):
        """Test that content directories are properly created."""
        assert full_shared_state.content_dir.exists()
        assert full_shared_state.research_dir.exists()

    def test_draft_article_file_path(self, full_shared_state: SharedState):
        """Test draft article file path is correct."""
        content = "# Test Draft"
        path = full_shared_state.write_draft_article(content)

        assert path.exists()
        assert "draft_article.md" in path.name
        assert full_shared_state.read_draft_article() == content

    def test_final_article_file_path(self, full_shared_state: SharedState):
        """Test final article file path is correct."""
        content = "# Final Article"
        path = full_shared_state.write_final_article(content)

        assert path.exists()
        assert "final_article.md" in path.name


class TestHBRQualityRequirements:
    """Tests specifically for HBR quality requirements."""

    def test_five_core_qualities_prompt_coverage(self):
        """Test that HBR Five Core Qualities are addressed in prompts."""
        from src.agents.hbr_editor_agent import FINAL_QUALITY_CHECK_PROMPT

        # All five qualities must be in the quality check
        assert "EXPERTISE" in FINAL_QUALITY_CHECK_PROMPT
        assert "EVIDENCE" in FINAL_QUALITY_CHECK_PROMPT
        assert "ORIGINALITY" in FINAL_QUALITY_CHECK_PROMPT
        assert "USEFULNESS" in FINAL_QUALITY_CHECK_PROMPT
        assert "GOOD WRITING" in FINAL_QUALITY_CHECK_PROMPT or "WRITING" in FINAL_QUALITY_CHECK_PROMPT

    def test_editing_passes_defined(self):
        """Test that all editing passes are defined."""
        from src.agents.hbr_editor_agent import (
            CLARITY_PASS_PROMPT,
            EVIDENCE_PASS_PROMPT,
            TONE_PASS_PROMPT,
            FLOW_PASS_PROMPT,
        )

        # All passes must exist
        assert "CLARITY" in CLARITY_PASS_PROMPT
        assert "EVIDENCE" in EVIDENCE_PASS_PROMPT
        assert "TONE" in TONE_PASS_PROMPT
        assert "FLOW" in FLOW_PASS_PROMPT

    def test_counterintuitive_insight_emphasis(self):
        """Test that counterintuitive insights are emphasized."""
        from src.agents.synthesis_agent import INSIGHT_EXTRACTION_PROMPT

        # Counterintuitive must be emphasized
        assert "counterintuitive" in INSIGHT_EXTRACTION_PROMPT.lower()
        assert "CRITICAL" in INSIGHT_EXTRACTION_PROMPT or "ESSENTIAL" in INSIGHT_EXTRACTION_PROMPT

    def test_word_count_in_prompts(self):
        """Test that word count targets are in prompts."""
        from src.agents.synthesis_agent import ARTICLE_STRUCTURE_PROMPT
        from src.agents.hbr_editor_agent import WORD_COUNT_ADJUSTMENT_PROMPT

        # Word count guidance should be present
        assert "2200" in ARTICLE_STRUCTURE_PROMPT or "target" in ARTICLE_STRUCTURE_PROMPT.lower()
        assert "word" in WORD_COUNT_ADJUSTMENT_PROMPT.lower()
