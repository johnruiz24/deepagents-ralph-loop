"""Tests for SharedState hierarchical state management."""

import json
import pytest
from pathlib import Path
import tempfile
import shutil

from src.state.shared_state import SharedState, create_shared_state


class TestSharedStateDirectoryStructure:
    """Test that SharedState creates the correct directory hierarchy."""

    def test_creates_all_directories(self, tmp_path: Path):
        """Verify all required directories are created."""
        state = SharedState(output_dir=tmp_path / "test_output")

        # Check all directories exist
        assert state.input_dir.exists()
        assert state.research_dir.exists()
        assert state.raw_data_dir.exists()
        assert state.content_dir.exists()
        assert state.visuals_dir.exists()
        assert state.multimedia_dir.exists()
        assert state.final_deliverables_dir.exists()

    def test_directory_structure_matches_spec(self, tmp_path: Path):
        """Verify directory structure matches IMPLEMENTATION_GUIDE.md spec."""
        state = SharedState(output_dir=tmp_path / "test_output")

        # Verify relative paths
        assert state.input_dir == state.output_dir / "input"
        assert state.research_dir == state.output_dir / "research"
        assert state.raw_data_dir == state.output_dir / "research" / "raw_data"
        assert state.content_dir == state.output_dir / "content"
        assert state.visuals_dir == state.output_dir / "visuals"
        assert state.multimedia_dir == state.output_dir / "multimedia"
        assert state.final_deliverables_dir == state.output_dir / "final_deliverables"


class TestSharedStateInputOperations:
    """Test input read/write operations."""

    def test_write_user_prompt(self, tmp_path: Path):
        """Test writing user prompt to input directory."""
        state = SharedState(output_dir=tmp_path / "test_output")

        path = state.write_user_prompt(
            topic="Universal Commerce Protocol",
            target_audience="TUI Leadership",
            key_concepts=["Agentic AI", "Commerce"],
        )

        assert path.exists()
        data = json.loads(path.read_text())
        assert data["topic"] == "Universal Commerce Protocol"
        assert data["target_audience"] == "TUI Leadership"
        assert data["key_concepts"] == ["Agentic AI", "Commerce"]

    def test_write_topics_and_subtopics(self, tmp_path: Path):
        """Test writing topics and subtopics."""
        state = SharedState(output_dir=tmp_path / "test_output")

        sub_topics = [
            {"name": "Technical Architecture", "queries": ["UCP spec"]},
            {"name": "Business Impact", "queries": ["OTA implications"]},
        ]
        path = state.write_topics_and_subtopics(sub_topics)

        assert path.exists()
        data = json.loads(path.read_text())
        assert len(data["sub_topics"]) == 2


class TestSharedStateResearchOperations:
    """Test research read/write operations."""

    def test_write_research_plan(self, tmp_path: Path):
        """Test writing research plan."""
        state = SharedState(output_dir=tmp_path / "test_output")

        research_plan = {
            "research_plan": [
                {"sub_topic": "Tech", "queries": ["query1"]},
            ]
        }
        path = state.write_research_plan(research_plan)

        assert path.exists()
        assert state.read_research_plan() == research_plan

    def test_write_research_data(self, tmp_path: Path):
        """Test writing research data for subtopics."""
        state = SharedState(output_dir=tmp_path / "test_output")

        path = state.write_research_data(
            subtopic="Technical Architecture",
            filename="article_1.md",
            content="# Article 1\nContent here",
        )

        assert path.exists()
        assert "Technical_Architecture" in str(path) or "Technical Architecture" in str(path)
        assert path.read_text() == "# Article 1\nContent here"

    def test_read_all_research_data(self, tmp_path: Path):
        """Test reading all research data by subtopic."""
        state = SharedState(output_dir=tmp_path / "test_output")

        # Write some data
        state.write_research_data("Topic A", "article_1.md", "Content A1")
        state.write_research_data("Topic A", "article_2.md", "Content A2")
        state.write_research_data("Topic B", "article_1.md", "Content B1")

        data = state.read_all_research_data()

        assert len(data) == 2
        # Check Topic A has 2 files
        topic_a_key = [k for k in data.keys() if "Topic" in k and "A" in k][0]
        assert len(data[topic_a_key]) == 2

    def test_write_tui_strategy_summary(self, tmp_path: Path):
        """Test writing TUI strategy summary."""
        state = SharedState(output_dir=tmp_path / "test_output")

        content = "# TUI Strategy Summary\nKey priorities..."
        path = state.write_tui_strategy_summary(content)

        assert path.exists()
        assert state.read_tui_strategy_summary() == content


class TestSharedStateContentOperations:
    """Test content read/write operations."""

    def test_write_draft_article(self, tmp_path: Path):
        """Test writing draft article."""
        state = SharedState(output_dir=tmp_path / "test_output")

        content = "# Draft Article\n" + "word " * 2000
        path = state.write_draft_article(content)

        assert path.exists()
        assert state.read_draft_article() == content
        # Check word count updated
        assert state.state["word_count"] > 2000

    def test_write_final_article(self, tmp_path: Path):
        """Test writing final article."""
        state = SharedState(output_dir=tmp_path / "test_output")

        content = "# Final Article\nPolished content"
        path = state.write_final_article(content)

        assert path.exists()
        assert state.read_final_article() == content


class TestSharedStateQualityGates:
    """Test quality gate operations."""

    def test_record_gate_passed(self, tmp_path: Path):
        """Test recording a passed quality gate."""
        state = SharedState(output_dir=tmp_path / "test_output")

        state.record_gate_passed("research")
        state.record_gate_passed("tui_analysis")

        assert "research" in state.state["quality_gates_passed"]
        assert "tui_analysis" in state.state["quality_gates_passed"]

    def test_record_gate_failed(self, tmp_path: Path):
        """Test recording a failed quality gate."""
        state = SharedState(output_dir=tmp_path / "test_output")

        state.record_gate_failed("research", "Score too low: 70/85")

        assert len(state.state["quality_gates_failed"]) == 1
        assert "Score too low" in state.state["quality_gates_failed"][0]

    def test_add_error(self, tmp_path: Path):
        """Test adding error messages."""
        state = SharedState(output_dir=tmp_path / "test_output")

        state.add_error("Connection timeout")
        state.add_error("API rate limited")

        assert len(state.state["error_messages"]) == 2


class TestSharedStateWorkflowControl:
    """Test workflow control operations."""

    def test_set_phase(self, tmp_path: Path):
        """Test setting workflow phase."""
        state = SharedState(output_dir=tmp_path / "test_output")

        state.set_phase("research")
        assert state.state["current_phase"] == "research"

        state.set_phase("synthesis")
        assert state.state["current_phase"] == "synthesis"

    def test_increment_iteration(self, tmp_path: Path):
        """Test incrementing phase iteration."""
        state = SharedState(output_dir=tmp_path / "test_output")

        iter1 = state.increment_iteration("research")
        iter2 = state.increment_iteration("research")

        assert iter1 == 1
        assert iter2 == 2
        assert state.state["research_iteration"] == 2

    def test_mark_complete(self, tmp_path: Path):
        """Test marking workflow complete."""
        state = SharedState(output_dir=tmp_path / "test_output")

        state.mark_complete()

        assert state.state["is_complete"] is True
        assert state.state["current_phase"] == "complete"


class TestSharedStateSerialization:
    """Test state serialization operations."""

    def test_save_and_load_snapshot(self, tmp_path: Path):
        """Test saving and loading state snapshot."""
        state = SharedState(output_dir=tmp_path / "test_output")

        # Modify state
        state.update_state(
            topic="Test Topic",
            research_quality_score=85.0,
        )
        state.record_gate_passed("research")

        # Save snapshot
        path = state.save_state_snapshot()
        assert path.exists()

        # Create new state and load
        new_state = SharedState(output_dir=tmp_path / "test_output")
        loaded = new_state.load_state_snapshot()

        assert loaded is True
        assert new_state.state["topic"] == "Test Topic"
        assert new_state.state["research_quality_score"] == 85.0


class TestCreateSharedState:
    """Test the create_shared_state factory function."""

    def test_creates_timestamped_directory(self, tmp_path: Path):
        """Test that factory creates timestamped output directory."""
        state = create_shared_state(
            topic="Test Topic",
            output_base_dir=str(tmp_path),
        )

        # Check directory name contains timestamp
        dir_name = state.output_dir.name
        assert dir_name.startswith("202")  # Year prefix

    def test_initializes_state_correctly(self, tmp_path: Path):
        """Test that state is initialized with provided values."""
        state = create_shared_state(
            topic="Universal Commerce Protocol",
            target_audience="TUI Executives",
            key_concepts=["AI", "Commerce"],
            output_base_dir=str(tmp_path),
        )

        assert state.state["topic"] == "Universal Commerce Protocol"
        assert state.state["target_audience"] == "TUI Executives"
        assert state.state["key_concepts"] == ["AI", "Commerce"]

    def test_writes_initial_input_files(self, tmp_path: Path):
        """Test that factory writes initial input files."""
        state = create_shared_state(
            topic="Test",
            output_base_dir=str(tmp_path),
        )

        # Check user_prompt.json was created
        assert (state.input_dir / "user_prompt.json").exists()
