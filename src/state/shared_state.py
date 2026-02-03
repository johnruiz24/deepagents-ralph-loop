"""
Hierarchical shared state management for the newsletter agent system.

Implements the file-based state structure from IMPLEMENTATION_GUIDE.md section 2.2:

    shared_state/
    ├── input/
    │   ├── user_prompt.json
    │   └── topics_and_subtopics.json
    ├── research/
    │   ├── research_plan.json
    │   ├── raw_data/
    │   │   ├── subtopic_1/
    │   │   └── subtopic_2/
    │   └── tui_strategy_summary.md
    ├── content/
    │   ├── draft_article.md
    │   └── final_article.md
    ├── visuals/
    │   ├── diagram_1.png
    │   └── chart_1.png
    ├── multimedia/
    │   ├── audio_version.mp3
    │   └── promo_video.mp4
    └── final_deliverables/
        ├── Leadership_Strategy_Newsletter.pdf
        └── Leadership_Strategy_Newsletter.html
"""

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Literal

from src.state.newsletter_state import NewsletterState, create_initial_newsletter_state, QUALITY_THRESHOLDS


@dataclass
class SharedState:
    """
    Hierarchical shared state manager for the newsletter workflow.

    Combines in-memory state tracking with file-based artifact storage.
    """

    # Base output directory
    output_dir: Path

    # In-memory state (for workflow tracking)
    state: NewsletterState = field(default_factory=lambda: create_initial_newsletter_state(""))

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Initialize directory structure."""
        self.output_dir = Path(self.output_dir)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create the hierarchical directory structure."""
        directories = [
            self.input_dir,
            self.research_dir,
            self.research_dir / "raw_data",
            self.content_dir,
            self.visuals_dir,
            self.multimedia_dir,
            self.final_deliverables_dir,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    # ============== Directory Properties ==============

    @property
    def input_dir(self) -> Path:
        """Input directory for user prompts and topics."""
        return self.output_dir / "input"

    @property
    def research_dir(self) -> Path:
        """Research directory for plans and raw data."""
        return self.output_dir / "research"

    @property
    def raw_data_dir(self) -> Path:
        """Raw research data directory."""
        return self.research_dir / "raw_data"

    @property
    def content_dir(self) -> Path:
        """Content directory for drafts and final article."""
        return self.output_dir / "content"

    @property
    def visuals_dir(self) -> Path:
        """Visuals directory for images and diagrams."""
        return self.output_dir / "visuals"

    @property
    def multimedia_dir(self) -> Path:
        """Multimedia directory for audio and video."""
        return self.output_dir / "multimedia"

    @property
    def final_deliverables_dir(self) -> Path:
        """Final deliverables directory for PDF and HTML."""
        return self.output_dir / "final_deliverables"

    # ============== State Read/Write Operations ==============

    def update_state(self, **kwargs: Any) -> None:
        """
        Update in-memory state with new values.

        Args:
            **kwargs: State fields to update
        """
        for key, value in kwargs.items():
            # Always set the value (allows adding new keys dynamically)
            self.state[key] = value  # type: ignore
        self.updated_at = datetime.now()

    def get_state_field(self, field: str) -> Any:
        """Get a specific state field value."""
        return self.state.get(field)

    # ============== Input Operations ==============

    def write_user_prompt(self, topic: str, target_audience: str, key_concepts: list[str]) -> Path:
        """Write user prompt to input directory."""
        data = {
            "topic": topic,
            "target_audience": target_audience,
            "key_concepts": key_concepts,
            "created_at": datetime.now().isoformat(),
        }
        path = self.input_dir / "user_prompt.json"
        path.write_text(json.dumps(data, indent=2))

        # Update in-memory state
        self.update_state(
            topic=topic,
            target_audience=target_audience,
            key_concepts=key_concepts,
        )
        return path

    def write_topics_and_subtopics(self, sub_topics: list[dict]) -> Path:
        """Write topics and subtopics to input directory."""
        data = {
            "sub_topics": sub_topics,
            "created_at": datetime.now().isoformat(),
        }
        path = self.input_dir / "topics_and_subtopics.json"
        path.write_text(json.dumps(data, indent=2))

        # Update in-memory state
        self.update_state(sub_topics=sub_topics)
        return path

    def read_user_prompt(self) -> Optional[dict]:
        """Read user prompt from input directory."""
        path = self.input_dir / "user_prompt.json"
        if path.exists():
            return json.loads(path.read_text())
        return None

    # ============== Research Operations ==============

    def write_research_plan(self, research_plan: dict) -> Path:
        """Write research plan to research directory."""
        path = self.research_dir / "research_plan.json"
        path.write_text(json.dumps(research_plan, indent=2))

        # Update in-memory state
        self.update_state(research_plan=research_plan)
        return path

    def read_research_plan(self) -> Optional[dict]:
        """Read research plan from research directory."""
        path = self.research_dir / "research_plan.json"
        if path.exists():
            return json.loads(path.read_text())
        return None

    def write_research_data(self, subtopic: str, filename: str, content: str) -> Path:
        """
        Write research data for a specific subtopic.

        Args:
            subtopic: The subtopic name (used as directory name)
            filename: The filename for the research data
            content: The content to write (markdown)

        Returns:
            Path to the written file
        """
        # Sanitize subtopic name for filesystem
        safe_subtopic = "".join(c if c.isalnum() or c in "._- " else "_" for c in subtopic)
        subtopic_dir = self.raw_data_dir / safe_subtopic
        subtopic_dir.mkdir(parents=True, exist_ok=True)

        path = subtopic_dir / filename
        path.write_text(content)
        return path

    def read_all_research_data(self) -> dict[str, list[dict]]:
        """
        Read all research data organized by subtopic.

        Returns:
            Dict mapping subtopic names to list of {filename, content}
        """
        result = {}
        if self.raw_data_dir.exists():
            for subtopic_dir in self.raw_data_dir.iterdir():
                if subtopic_dir.is_dir():
                    files = []
                    for file_path in subtopic_dir.glob("*.md"):
                        files.append({
                            "filename": file_path.name,
                            "content": file_path.read_text(),
                        })
                    result[subtopic_dir.name] = files
        return result

    def write_tui_strategy_summary(self, content: str) -> Path:
        """Write TUI strategy summary to research directory."""
        path = self.research_dir / "tui_strategy_summary.md"
        path.write_text(content)

        # Update in-memory state
        self.update_state(tui_analysis={"summary_path": str(path), "content": content})
        return path

    def read_tui_strategy_summary(self) -> Optional[str]:
        """Read TUI strategy summary from research directory."""
        path = self.research_dir / "tui_strategy_summary.md"
        if path.exists():
            return path.read_text()
        return None

    # ============== Content Operations ==============

    def write_draft_article(self, content: str) -> Path:
        """Write draft article to content directory."""
        path = self.content_dir / "draft_article.md"
        path.write_text(content)

        # Update in-memory state
        word_count = len(content.split())
        self.update_state(article_content=content, word_count=word_count)
        return path

    def write_final_article(self, content: str) -> Path:
        """Write final article to content directory."""
        path = self.content_dir / "final_article.md"
        path.write_text(content)

        # Update in-memory state
        word_count = len(content.split())
        self.update_state(article_content=content, word_count=word_count)
        return path

    def read_draft_article(self) -> Optional[str]:
        """Read draft article from content directory."""
        path = self.content_dir / "draft_article.md"
        if path.exists():
            return path.read_text()
        return None

    def read_final_article(self) -> Optional[str]:
        """Read final article from content directory."""
        path = self.content_dir / "final_article.md"
        if path.exists():
            return path.read_text()
        return None

    # ============== Visual Operations ==============

    def write_visual(self, filename: str, content: bytes) -> Path:
        """Write a visual asset (image/diagram) to visuals directory."""
        path = self.visuals_dir / filename
        path.write_bytes(content)

        # Update in-memory state
        images = self.state.get("generated_images", [])
        images.append({"path": str(path), "filename": filename})
        self.update_state(generated_images=images)
        return path

    def copy_visual(self, source_path: Path, filename: Optional[str] = None) -> Path:
        """Copy a visual asset from another location."""
        dest_filename = filename or source_path.name
        dest_path = self.visuals_dir / dest_filename
        shutil.copy2(source_path, dest_path)
        return dest_path

    def list_visuals(self) -> list[Path]:
        """List all visual assets."""
        return list(self.visuals_dir.glob("*"))

    # ============== Multimedia Operations ==============

    def write_audio(self, content: bytes, filename: str = "audio_version.mp3") -> Path:
        """Write audio file to multimedia directory."""
        path = self.multimedia_dir / filename
        path.write_bytes(content)

        # Update in-memory state
        self.update_state(audio_path=str(path))
        return path

    def write_video(self, content: bytes, filename: str = "promo_video.mp4") -> Path:
        """Write video file to multimedia directory."""
        path = self.multimedia_dir / filename
        path.write_bytes(content)

        # Update in-memory state
        self.update_state(video_path=str(path))
        return path

    # ============== Final Deliverables Operations ==============

    def write_pdf(self, content: bytes, filename: str = "Leadership_Strategy_Newsletter.pdf") -> Path:
        """Write PDF to final deliverables directory."""
        path = self.final_deliverables_dir / filename
        path.write_bytes(content)

        # Update in-memory state
        self.update_state(pdf_path=str(path))
        return path

    def write_html(self, content: str, filename: str = "Leadership_Strategy_Newsletter.html") -> Path:
        """Write HTML to final deliverables directory."""
        path = self.final_deliverables_dir / filename
        path.write_text(content)

        # Update in-memory state
        self.update_state(html_path=str(path))
        return path

    def create_archive(self, archive_name: str = "newsletter_package") -> Path:
        """Create a ZIP archive of all final deliverables."""
        archive_path = self.output_dir / archive_name
        shutil.make_archive(str(archive_path), "zip", self.final_deliverables_dir)

        # Update in-memory state
        self.update_state(archive_path=f"{archive_path}.zip")
        return Path(f"{archive_path}.zip")

    # ============== Quality Gate Operations ==============

    def record_gate_passed(self, gate_name: str) -> None:
        """Record that a quality gate was passed."""
        passed = list(self.state.get("quality_gates_passed", []))
        if gate_name not in passed:
            passed.append(gate_name)
        self.update_state(quality_gates_passed=passed)

    def record_gate_failed(self, gate_name: str, reason: str = "") -> None:
        """Record that a quality gate failed."""
        failed = list(self.state.get("quality_gates_failed", []))
        entry = f"{gate_name}: {reason}" if reason else gate_name
        failed.append(entry)
        self.update_state(quality_gates_failed=failed)

    def add_error(self, error_message: str) -> None:
        """Add an error message to the state."""
        errors = list(self.state.get("error_messages", []))
        errors.append(error_message)
        self.update_state(error_messages=errors)

    # ============== Workflow Control ==============

    def set_phase(self, phase: str) -> None:
        """Set the current workflow phase."""
        self.update_state(current_phase=phase)

    def increment_iteration(self, phase: str) -> int:
        """Increment the iteration counter for a phase."""
        iteration_field = f"{phase}_iteration"
        current = self.state.get(iteration_field, 0)
        new_value = current + 1
        self.update_state(**{iteration_field: new_value})
        return new_value

    def mark_complete(self) -> None:
        """Mark the workflow as complete."""
        self.update_state(is_complete=True, current_phase="complete")

    # ============== Serialization ==============

    def save_state_snapshot(self) -> Path:
        """Save a snapshot of the current in-memory state."""
        path = self.output_dir / "state_snapshot.json"
        snapshot = {
            "state": dict(self.state),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        path.write_text(json.dumps(snapshot, indent=2, default=str))
        return path

    def load_state_snapshot(self) -> bool:
        """Load state from snapshot if it exists."""
        path = self.output_dir / "state_snapshot.json"
        if path.exists():
            snapshot = json.loads(path.read_text())
            for key, value in snapshot["state"].items():
                if key in self.state:
                    self.state[key] = value  # type: ignore
            return True
        return False


def create_shared_state(
    topic: str,
    target_audience: str = "TUI Leadership and Strategy Teams",
    key_concepts: Optional[list[str]] = None,
    output_base_dir: str = "output",
) -> SharedState:
    """
    Create a new SharedState for a newsletter workflow.

    Args:
        topic: The newsletter topic
        target_audience: Target audience description
        key_concepts: Optional list of key concepts
        output_base_dir: Base directory for output

    Returns:
        Initialized SharedState instance
    """
    # Create timestamped output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = "".join(c if c.isalnum() or c in "._- " else "_" for c in topic)[:50]
    output_dir = Path(output_base_dir) / f"{timestamp}_{safe_topic}"

    # Initialize state
    initial_state = create_initial_newsletter_state(
        topic=topic,
        target_audience=target_audience,
        key_concepts=key_concepts,
    )

    shared_state = SharedState(output_dir=output_dir, state=initial_state)

    # Write initial input files
    shared_state.write_user_prompt(topic, target_audience, key_concepts or [])

    return shared_state
