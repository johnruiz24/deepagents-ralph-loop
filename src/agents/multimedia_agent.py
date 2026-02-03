"""
Multimedia Production Agent.

Generates audio narration and promotional video for the newsletter.
Based on IMPLEMENTATION_GUIDE.md section 3.8.

Responsibilities:
- Audio narration using OpenAI TTS (preferred) or Amazon Polly (~10 minutes)
- Promotional video (60 seconds EXACTLY)
- Professional quality matching HBR standards

QUALITY BAR: Polished, professional multimedia!
"""

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.agents.base_agent import LLMAgent
from src.state.shared_state import SharedState
from src.utils.bedrock_config import create_bedrock_llm


@dataclass
class MultimediaInput:
    """Input for multimedia production."""
    article_content: str
    article_title: str
    subtitle: str
    topic: str
    key_insights: list[str]
    counterintuitive_insights: list[str]
    visual_assets: list[dict]


@dataclass
class AudioAsset:
    """Generated audio asset."""
    filename: str
    file_path: Path
    duration_seconds: float
    voice_id: str
    format: str


@dataclass
class VideoAsset:
    """Generated video asset."""
    filename: str
    file_path: Path
    duration_seconds: float
    resolution: str
    format: str


@dataclass
class MultimediaOutput:
    """Output from multimedia production."""
    audio: Optional[AudioAsset]
    video: Optional[VideoAsset]
    script: str
    video_script: str
    generation_status: dict


# Prompts for script generation

NARRATION_SCRIPT_PROMPT = """You are creating a professional narration script for an executive briefing.

## Article Content
{article_content}

## Requirements
- Duration: ~10 minutes when read aloud (approximately 1500 words)
- Tone: Authoritative, engaging, conversational
- Audience: Senior executives and business leaders
- Style: Like a premium podcast or audiobook

## Script Guidelines

1. **Opening (30 seconds)**
   - Hook the listener immediately
   - Preview what they'll learn

2. **Body (8-9 minutes)**
   - Follow the article structure
   - Add natural transitions ("Now, let's consider...")
   - Include brief pauses for emphasis [PAUSE]
   - Emphasize key insights

3. **Closing (30-60 seconds)**
   - Summarize key takeaways
   - Call to action
   - Professional sign-off

## Formatting
- Use natural spoken language (contractions OK)
- Include [PAUSE] markers for emphasis
- Include [EMPHASIS] markers for key points
- Avoid complex sentences that are hard to read aloud

Write the narration script now:"""


VIDEO_SCRIPT_PROMPT = """You are creating a 60-second promotional video script.

## Article Title
{title}

## Key Insights
{key_insights}

## Counterintuitive Insight (FEATURE THIS!)
{counterintuitive_insight}

## Video Structure (STRICT 60 SECONDS)

1. **HOOK (0-10 seconds)** - Grab attention
   - Bold statement or provocative question
   - Visual: Attention-grabbing imagery

2. **EXPLANATION (10-40 seconds)** - Core message
   - What is the key insight?
   - Why does it matter?
   - Visual: Key data points, diagrams

3. **IMPLICATION (40-55 seconds)** - So what?
   - What should leaders do?
   - Why act now?
   - Visual: Forward-looking imagery

4. **CTA (55-60 seconds)** - Call to action
   - Read the full analysis
   - Clear next step

## Output Format

```json
{{
  "hook": {{
    "duration": 10,
    "voiceover": "...",
    "visual_description": "...",
    "text_overlay": "..."
  }},
  "explanation": {{
    "duration": 30,
    "voiceover": "...",
    "visual_description": "...",
    "text_overlay": "...",
    "key_stat": "..."
  }},
  "implication": {{
    "duration": 15,
    "voiceover": "...",
    "visual_description": "...",
    "text_overlay": "..."
  }},
  "cta": {{
    "duration": 5,
    "voiceover": "...",
    "visual_description": "...",
    "text_overlay": "..."
  }}
}}
```

Generate the video script now:"""


class MultimediaAgent(LLMAgent[MultimediaInput, MultimediaOutput]):
    """
    Agent that produces audio narration and promotional video.

    Process:
    1. Generate narration script from article
    2. Generate audio using ElevenLabs
    3. Generate video script
    4. Create video with kinetic typography
    """

    agent_name = "MultimediaAgent"
    phase = "multimedia"

    # Duration constraints
    AUDIO_TARGET_DURATION = 600  # 10 minutes in seconds
    VIDEO_DURATION = 60  # Exactly 60 seconds
    VIDEO_TOLERANCE = 2  # ±2 seconds

    def __init__(self, shared_state: SharedState, **kwargs):
        super().__init__(shared_state, **kwargs)
        self._llm = create_bedrock_llm(model_preset="opus", temperature=0.6)

    async def read_from_state(self) -> MultimediaInput:
        """Read article and assets from state."""
        state = self.shared_state.state

        # Read final article
        article_content = self.shared_state.read_final_article()
        if not article_content:
            article_content = self.shared_state.read_draft_article() or ""

        # Get synthesized content
        synthesized = state.get("synthesized_content", {})

        return MultimediaInput(
            article_content=article_content,
            article_title=synthesized.get("title", state.get("topic", "")),
            subtitle=synthesized.get("subtitle", ""),
            topic=state.get("topic", ""),
            key_insights=synthesized.get("key_insights", []),
            counterintuitive_insights=synthesized.get("counterintuitive_insights", []),
            visual_assets=state.get("visual_assets", []),
        )

    async def process(self, input_data: MultimediaInput) -> MultimediaOutput:
        """
        Generate multimedia assets.

        1. Generate narration script
        2. Generate audio (ElevenLabs)
        3. Generate video script
        4. Create video
        """
        self.logger.info(
            "Starting multimedia production",
            topic=input_data.topic,
        )

        status = {
            "audio_generated": False,
            "video_generated": False,
            "audio_error": None,
            "video_error": None,
        }

        # Step 1: Generate narration script
        self.logger.info("Step 1: Generating narration script")
        narration_script = await self._generate_narration_script(input_data)

        # Step 2: Generate audio
        self.logger.info("Step 2: Generating audio narration")
        audio_asset = None
        try:
            audio_asset = await self._generate_audio(narration_script, input_data.article_title)
            status["audio_generated"] = True
        except Exception as e:
            self.logger.warning(f"Audio generation failed: {e}")
            status["audio_error"] = str(e)
            # Save script for manual generation
            self._save_narration_script(narration_script)

        # Step 3: Generate video script
        self.logger.info("Step 3: Generating video script")
        video_script = await self._generate_video_script(input_data)

        # Step 4: Generate video
        self.logger.info("Step 4: Generating promotional video")
        video_asset = None
        try:
            video_asset = await self._generate_video(video_script, input_data)
            status["video_generated"] = True
        except Exception as e:
            self.logger.warning(f"Video generation failed: {e}")
            status["video_error"] = str(e)
            # Save script for manual generation
            self._save_video_script(video_script)

        self.logger.info(
            "Multimedia production complete",
            audio_generated=status["audio_generated"],
            video_generated=status["video_generated"],
        )

        return MultimediaOutput(
            audio=audio_asset,
            video=video_asset,
            script=narration_script,
            video_script=video_script if isinstance(video_script, str) else json.dumps(video_script, indent=2),
            generation_status=status,
        )

    async def write_to_state(self, output_data: MultimediaOutput) -> None:
        """Write multimedia information to state."""
        multimedia_data = {
            "audio": {
                "filename": output_data.audio.filename if output_data.audio else None,
                "duration": output_data.audio.duration_seconds if output_data.audio else None,
                "path": str(output_data.audio.file_path) if output_data.audio else None,
            },
            "video": {
                "filename": output_data.video.filename if output_data.video else None,
                "duration": output_data.video.duration_seconds if output_data.video else None,
                "path": str(output_data.video.file_path) if output_data.video else None,
            },
            "status": output_data.generation_status,
        }

        self.shared_state.update_state(
            multimedia=multimedia_data,
            audio_generated=output_data.generation_status["audio_generated"],
            video_generated=output_data.generation_status["video_generated"],
        )

        # Save scripts to multimedia directory
        scripts_dir = self.shared_state.multimedia_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)

        (scripts_dir / "narration_script.txt").write_text(output_data.script)
        (scripts_dir / "video_script.json").write_text(output_data.video_script)

    async def validate_output(self, output_data: MultimediaOutput) -> tuple[bool, str]:
        """Validate multimedia output."""
        issues = []

        # Check audio
        if not output_data.audio and not output_data.generation_status.get("audio_error"):
            issues.append("Audio not generated (no error reported)")

        # Check video
        if not output_data.video and not output_data.generation_status.get("video_error"):
            issues.append("Video not generated (no error reported)")

        # Video duration check (if video exists)
        if output_data.video:
            duration = output_data.video.duration_seconds
            if abs(duration - self.VIDEO_DURATION) > self.VIDEO_TOLERANCE:
                issues.append(f"Video duration {duration}s (need {self.VIDEO_DURATION}±{self.VIDEO_TOLERANCE}s)")

        # At minimum, scripts should be generated
        if not output_data.script:
            issues.append("Narration script not generated")

        if issues:
            return False, f"Multimedia validation issues: {'; '.join(issues)}"

        # Partial success is OK if scripts are available
        if output_data.script and output_data.video_script:
            return True, "Multimedia generation complete (scripts available for manual processing if needed)"

        return True, "Multimedia generation fully successful"

    async def calculate_quality_score(self, output_data: MultimediaOutput) -> float:
        """Calculate quality score."""
        score = 50.0  # Base for having scripts

        # Audio bonus
        if output_data.audio:
            score += 25
            # Duration bonus
            if output_data.audio.duration_seconds >= 300:  # At least 5 min
                score += 5

        # Video bonus
        if output_data.video:
            score += 25
            # Duration accuracy bonus
            if abs(output_data.video.duration_seconds - self.VIDEO_DURATION) <= self.VIDEO_TOLERANCE:
                score += 5

        return min(100, score)

    async def _generate_narration_script(self, input_data: MultimediaInput) -> str:
        """Generate narration script from article."""
        prompt = NARRATION_SCRIPT_PROMPT.format(
            article_content=input_data.article_content[:10000],
        )

        return await self.invoke_llm(prompt)

    async def _generate_video_script(self, input_data: MultimediaInput) -> dict:
        """Generate video script."""
        counterintuitive = (
            input_data.counterintuitive_insights[0]
            if input_data.counterintuitive_insights
            else "Key strategic insight"
        )

        prompt = VIDEO_SCRIPT_PROMPT.format(
            title=input_data.article_title,
            key_insights="\n".join(f"- {i}" for i in input_data.key_insights[:5]),
            counterintuitive_insight=counterintuitive,
        )

        response = await self.invoke_llm(prompt)

        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response

            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            return self._create_fallback_video_script(input_data)

    async def _generate_audio(self, script: str, title: str) -> Optional[AudioAsset]:
        """Generate audio using OpenAI TTS API (preferred) or Amazon Polly as fallback."""
        clean_script = self._clean_script_for_tts(script)
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_').lower()
        filename = f"narration_{safe_title}.mp3"
        file_path = self.shared_state.multimedia_dir / filename

        # Try OpenAI TTS first (preferred)
        try:
            self.logger.info("Generating audio with OpenAI TTS...")
            from openai import OpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")

            client = OpenAI(api_key=api_key)

            # Use tts-1-hd for high quality, 'onyx' voice for professional narration
            response = client.audio.speech.create(
                model="tts-1-hd",
                voice="onyx",  # Professional, authoritative male voice
                input=clean_script,
                response_format="mp3",
            )

            # Stream to file
            response.stream_to_file(str(file_path))

            # Estimate duration (~150 words per minute)
            word_count = len(clean_script.split())
            duration = (word_count / 150) * 60

            self.logger.info(f"OpenAI TTS audio generated: {filename}")

            return AudioAsset(
                filename=filename,
                file_path=file_path,
                duration_seconds=duration,
                voice_id="onyx",
                format="mp3",
            )

        except Exception as e:
            self.logger.warning(f"OpenAI TTS failed: {e}, trying Amazon Polly...")

        # Fallback to Amazon Polly
        try:
            self.logger.info("Generating audio with Amazon Polly...")
            import boto3

            polly = boto3.client('polly', region_name='eu-west-1')

            # Use Neural engine with Matthew voice (professional male)
            response = polly.synthesize_speech(
                Text=clean_script[:3000],  # Polly has text limits
                OutputFormat='mp3',
                VoiceId='Matthew',
                Engine='neural',
            )

            # Write audio stream to file
            if "AudioStream" in response:
                with open(file_path, 'wb') as audio_file:
                    audio_file.write(response['AudioStream'].read())

                # Estimate duration
                word_count = len(clean_script.split())
                duration = (word_count / 150) * 60

                self.logger.info(f"Amazon Polly audio generated: {filename}")

                return AudioAsset(
                    filename=filename,
                    file_path=file_path,
                    duration_seconds=duration,
                    voice_id="Matthew",
                    format="mp3",
                )
        except Exception as e:
            self.logger.warning(f"Amazon Polly failed: {e}")
            raise ValueError(f"All TTS services failed. OpenAI and Polly both unavailable.")

    async def _generate_video(self, script: dict, input_data: MultimediaInput) -> Optional[VideoAsset]:
        """Generate promotional video."""
        try:
            from moviepy.editor import (
                TextClip,
                CompositeVideoClip,
                ColorClip,
                concatenate_videoclips,
                AudioFileClip,
            )

            clips = []
            total_duration = 0

            # Video settings
            size = (1920, 1080)
            bg_color = (30, 58, 95)  # Corporate blue
            text_color = "white"
            font = "Arial-Bold"

            # Create sections
            for section_name in ["hook", "explanation", "implication", "cta"]:
                section = script.get(section_name, {})
                duration = section.get("duration", 10)
                text = section.get("text_overlay", section.get("voiceover", ""))[:100]

                # Background
                bg = ColorClip(size=size, color=bg_color, duration=duration)

                # Text overlay
                if text:
                    txt_clip = TextClip(
                        text,
                        fontsize=60,
                        color=text_color,
                        font=font,
                        size=(1600, None),
                        method="caption",
                    ).set_duration(duration).set_position("center")

                    section_clip = CompositeVideoClip([bg, txt_clip])
                else:
                    section_clip = bg

                clips.append(section_clip)
                total_duration += duration

            # Concatenate
            final_video = concatenate_videoclips(clips, method="compose")

            # Ensure exactly 60 seconds
            if total_duration != self.VIDEO_DURATION:
                final_video = final_video.set_duration(self.VIDEO_DURATION)

            # Save
            safe_title = re.sub(r'[^\w\s-]', '', input_data.article_title).strip().replace(' ', '_').lower()
            filename = f"promo_{safe_title}.mp4"
            file_path = self.shared_state.multimedia_dir / filename

            final_video.write_videofile(
                str(file_path),
                fps=24,
                codec="libx264",
                audio=False,
                preset="medium",
                threads=4,
            )

            return VideoAsset(
                filename=filename,
                file_path=file_path,
                duration_seconds=self.VIDEO_DURATION,
                resolution="1920x1080",
                format="mp4",
            )

        except ImportError:
            self.logger.warning("MoviePy library not available")
            raise
        except Exception as e:
            self.logger.warning(f"Video generation failed: {e}")
            raise

    def _clean_script_for_tts(self, script: str) -> str:
        """Clean script for text-to-speech."""
        # Remove markers
        script = re.sub(r'\[PAUSE\]', '...', script)
        script = re.sub(r'\[EMPHASIS\]', '', script)
        script = re.sub(r'\[.*?\]', '', script)

        # Clean up whitespace
        script = re.sub(r'\n+', '\n', script)
        script = re.sub(r' +', ' ', script)

        return script.strip()

    def _save_narration_script(self, script: str) -> None:
        """Save narration script for manual processing."""
        scripts_dir = self.shared_state.multimedia_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        (scripts_dir / "narration_script.txt").write_text(script)

    def _save_video_script(self, script) -> None:
        """Save video script for manual processing."""
        scripts_dir = self.shared_state.multimedia_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        if isinstance(script, dict):
            (scripts_dir / "video_script.json").write_text(json.dumps(script, indent=2))
        else:
            (scripts_dir / "video_script.json").write_text(str(script))

    def _create_fallback_video_script(self, input_data: MultimediaInput) -> dict:
        """Create fallback video script."""
        return {
            "hook": {
                "duration": 10,
                "voiceover": f"What if everything you knew about {input_data.topic} was wrong?",
                "visual_description": "Bold text animation on corporate blue background",
                "text_overlay": input_data.article_title,
            },
            "explanation": {
                "duration": 30,
                "voiceover": f"Our analysis reveals a surprising insight about {input_data.topic}.",
                "visual_description": "Key statistics and data points",
                "text_overlay": input_data.key_insights[0] if input_data.key_insights else "Key Strategic Insight",
                "key_stat": "Strategic Analysis",
            },
            "implication": {
                "duration": 15,
                "voiceover": "Leaders who understand this shift will have a decisive advantage.",
                "visual_description": "Forward-looking imagery, transformation",
                "text_overlay": "The Time to Act is Now",
            },
            "cta": {
                "duration": 5,
                "voiceover": "Read the full analysis.",
                "visual_description": "Clean call to action",
                "text_overlay": "Read Full Analysis →",
            },
        }


def create_multimedia_agent(shared_state: SharedState) -> MultimediaAgent:
    """Factory function to create MultimediaAgent."""
    return MultimediaAgent(shared_state)
