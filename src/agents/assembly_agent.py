"""
Final Assembly Agent.

Produces the final newsletter package with all deliverables.
Based on IMPLEMENTATION_GUIDE.md section 3.9.

Responsibilities:
- Generate professional PDF
- Generate responsive HTML
- Create ZIP archive with all assets
- Quality: Premium publication level

QUALITY BAR: Professional publication ready!
"""

import json
import re
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.agents.base_agent import LLMAgent
from src.state.shared_state import SharedState
from src.utils.bedrock_config import create_bedrock_llm
from src.utils.hbr_content_processor import (
    generate_hbr_content,
    format_idea_in_brief_html,
    format_pull_quotes_html,
    format_author_byline_html,
)


@dataclass
class AssemblyInput:
    """Input for final assembly."""
    article_content: str
    article_title: str
    subtitle: str
    topic: str
    word_count: int
    visual_assets: list[dict]
    multimedia: dict
    tui_context: str
    # HBR structural elements
    idea_in_brief: Optional[dict] = None  # {problem, argument, solution}
    pull_quotes: Optional[list[str]] = None
    author_name: str = "TUI Strategy Group"
    author_credentials: str = "Specialists in travel industry transformation and competitive strategy."


@dataclass
class PDFOutput:
    """Generated PDF."""
    filename: str
    file_path: Path
    page_count: int


@dataclass
class HTMLOutput:
    """Generated HTML."""
    filename: str
    file_path: Path
    has_audio_player: bool
    has_video_player: bool
    is_responsive: bool


@dataclass
class PackageOutput:
    """Final package."""
    filename: str
    file_path: Path
    total_files: int
    total_size_mb: float


@dataclass
class AssemblyOutput:
    """Output from final assembly."""
    pdf: Optional[PDFOutput]
    html: Optional[HTMLOutput]
    package: Optional[PackageOutput]
    manifest: dict
    assembly_status: dict


# HTML Template - HBR Professional Style

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --primary-color: #1E3A5F;
            --secondary-color: #3D7EAA;
            --text-color: #333;
            --bg-color: #FAFAFA;
            --accent-color: #E8F4F8;
            --hbr-red: #C41E3A;
            --sidebar-bg: #F5F5F5;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        /* HBR Author Byline */
        .author-byline {{
            text-align: center;
            margin: 20px 0 40px 0;
            padding-bottom: 20px;
            border-bottom: 1px solid #ddd;
        }}
        .author-byline .author-name {{
            font-size: 1.1rem;
            color: var(--text-color);
            margin-bottom: 5px;
        }}
        .author-byline .author-credentials {{
            font-size: 0.9rem;
            color: #666;
            font-style: italic;
        }}

        /* HBR Idea in Brief Sidebar */
        .idea-in-brief {{
            background: var(--sidebar-bg);
            border-left: 4px solid var(--hbr-red);
            padding: 25px;
            margin: 30px 0;
            border-radius: 0 8px 8px 0;
        }}
        .idea-in-brief h3 {{
            color: var(--hbr-red);
            font-size: 1.3rem;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .idea-in-brief .iib-section {{
            margin-bottom: 15px;
        }}
        .idea-in-brief .iib-section:last-child {{
            margin-bottom: 0;
        }}
        .idea-in-brief h4 {{
            color: var(--primary-color);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}
        .idea-in-brief p {{
            font-size: 0.95rem;
            line-height: 1.5;
            margin-bottom: 0;
            text-align: left;
        }}

        /* HBR Pull Quotes */
        .pull-quote {{
            border-left: 4px solid var(--hbr-red);
            padding: 20px 25px;
            margin: 30px 0;
            background: linear-gradient(to right, var(--sidebar-bg) 0%, transparent 100%);
            font-size: 1.25rem;
            font-style: italic;
            color: var(--primary-color);
            line-height: 1.5;
        }}
        .pull-quote::before {{
            content: '"';
            font-size: 3rem;
            color: var(--hbr-red);
            opacity: 0.3;
            position: relative;
            top: 15px;
            left: -10px;
        }}

        body {{
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.8;
            color: var(--text-color);
            background-color: var(--bg-color);
            max-width: 100%;
            overflow-x: hidden;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
        }}

        header {{
            text-align: center;
            padding: 60px 20px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            margin-bottom: 40px;
        }}

        h1 {{
            font-size: 2.5rem;
            margin-bottom: 15px;
            font-weight: 700;
            line-height: 1.2;
        }}

        .subtitle {{
            font-size: 1.2rem;
            font-style: italic;
            opacity: 0.9;
        }}

        .meta {{
            margin-top: 20px;
            font-size: 0.9rem;
            opacity: 0.8;
        }}

        article {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 40px;
        }}

        h2 {{
            font-size: 1.6rem;
            color: var(--primary-color);
            margin: 30px 0 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--accent-color);
        }}

        p {{
            margin-bottom: 20px;
            text-align: justify;
        }}

        .insight-box {{
            background: var(--accent-color);
            border-left: 4px solid var(--secondary-color);
            padding: 20px;
            margin: 25px 0;
            font-style: italic;
        }}

        .visual-asset, figure {{
            margin: 30px 0;
            text-align: center;
            max-width: 100%;
            overflow: hidden;
        }}

        .visual-asset img, figure img, article img, p img {{
            max-width: 100%;
            width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: block;
            margin: 20px auto;
        }}

        .visual-asset figcaption, figure figcaption {{
            margin-top: 12px;
            font-size: 0.95rem;
            color: #555;
            font-style: italic;
            text-align: center;
        }}

        /* Ensure images in paragraphs are properly contained */
        p:has(img) {{
            text-align: center;
            margin: 30px 0;
        }}

        .media-section {{
            background: var(--accent-color);
            padding: 30px;
            border-radius: 8px;
            margin: 40px 0;
        }}

        .media-section h3 {{
            color: var(--primary-color);
            margin-bottom: 20px;
        }}

        audio {{
            width: 100%;
            margin-top: 10px;
        }}

        video {{
            width: 100%;
            max-width: 100%;
            border-radius: 4px;
            margin-top: 10px;
        }}

        footer {{
            text-align: center;
            padding: 40px 20px;
            color: #666;
            font-size: 0.9rem;
        }}

        @media (max-width: 768px) {{
            h1 {{
                font-size: 1.8rem;
            }}

            article {{
                padding: 20px;
            }}

            .container {{
                padding: 20px 15px;
            }}
        }}

        @media print {{
            header {{
                background: var(--primary-color);
                -webkit-print-color-adjust: exact;
            }}

            article {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>{title}</h1>
            <p class="subtitle">{subtitle}</p>
            <p class="meta">
                {date} · {word_count} words · {reading_time} min read
            </p>
        </div>
    </header>

    <main class="container">
        {author_byline}

        {idea_in_brief}

        <article>
            {pull_quote_1}

            {article_html}

            {pull_quote_2}
        </article>

        {media_section}

        {visuals_section}
    </main>

    <footer>
        <p>© {year} Leadership Strategy Newsletter</p>
        <p>Generated with AI assistance for TUI Group</p>
    </footer>
</body>
</html>
"""

MEDIA_SECTION_TEMPLATE = """
<section class="media-section">
    <h3>Multimedia Content</h3>
    {audio_player}
    {video_player}
</section>
"""

AUDIO_PLAYER_TEMPLATE = """
<div class="audio-container">
    <h4>Audio Narration</h4>
    <audio controls>
        <source src="{audio_path}" type="audio/mpeg">
        Your browser does not support the audio element.
    </audio>
</div>
"""

VIDEO_PLAYER_TEMPLATE = """
<div class="video-container">
    <h4>Promotional Video</h4>
    <video controls>
        <source src="{video_path}" type="video/mp4">
        Your browser does not support the video element.
    </video>
</div>
"""


class AssemblyAgent(LLMAgent[AssemblyInput, AssemblyOutput]):
    """
    Agent that assembles the final newsletter package.

    Process:
    1. Generate professional PDF
    2. Generate responsive HTML
    3. Create ZIP archive with all assets
    """

    agent_name = "AssemblyAgent"
    phase = "assembly"

    def __init__(self, shared_state: SharedState, **kwargs):
        super().__init__(shared_state, **kwargs)
        self._llm = create_bedrock_llm(model_preset="haiku", temperature=0.3)

    async def read_from_state(self) -> AssemblyInput:
        """Read all content from state."""
        state = self.shared_state.state

        # Read final article
        article_content = self.shared_state.read_final_article()
        if not article_content:
            article_content = self.shared_state.read_draft_article() or ""

        # Get synthesized content
        synthesized = state.get("synthesized_content", {})

        # Get TUI context
        tui_context = self.shared_state.read_tui_strategy_summary() or ""

        # Generate HBR structural elements
        self.logger.info("Generating HBR structural elements (Idea in Brief, Pull Quotes)")
        try:
            hbr_content = await generate_hbr_content(article_content)
            idea_in_brief = {
                "problem": hbr_content.idea_in_brief.problem,
                "argument": hbr_content.idea_in_brief.argument,
                "solution": hbr_content.idea_in_brief.solution,
            }
            pull_quotes = hbr_content.pull_quotes
            author_name = hbr_content.author_name
            author_credentials = hbr_content.author_credentials
            self.logger.info(f"Generated {len(pull_quotes)} pull quotes")
        except Exception as e:
            self.logger.warning(f"HBR content generation failed: {e}, using defaults")
            idea_in_brief = {
                "problem": "Organizations face critical decisions about technology adoption.",
                "argument": "Success requires balancing innovation with operational excellence.",
                "solution": "Leaders must act decisively while maintaining strategic flexibility.",
            }
            pull_quotes = [
                "The biggest risk isn't failing to adopt new technology—it's losing sight of what makes your business unique.",
            ]
            author_name = "TUI Strategy Group"
            author_credentials = "Specialists in travel industry transformation and competitive strategy."

        return AssemblyInput(
            article_content=article_content,
            article_title=synthesized.get("title", state.get("topic", "")),
            subtitle=synthesized.get("subtitle", ""),
            topic=state.get("topic", ""),
            word_count=state.get("word_count", len(article_content.split())),
            visual_assets=state.get("visual_assets", []),
            multimedia=state.get("multimedia", {}),
            tui_context=tui_context,
            idea_in_brief=idea_in_brief,
            pull_quotes=pull_quotes,
            author_name=author_name,
            author_credentials=author_credentials,
        )

    async def process(self, input_data: AssemblyInput) -> AssemblyOutput:
        """
        Assemble final deliverables.

        1. Generate PDF
        2. Generate HTML
        3. Create ZIP package
        """
        self.logger.info(
            "Starting final assembly",
            topic=input_data.topic,
            word_count=input_data.word_count,
        )

        status = {
            "pdf_generated": False,
            "html_generated": False,
            "package_created": False,
            "errors": [],
        }

        # Step 1: Generate PDF
        self.logger.info("Step 1: Generating PDF")
        pdf_output = None
        try:
            pdf_output = await self._generate_pdf(input_data)
            status["pdf_generated"] = True
        except Exception as e:
            self.logger.warning(f"PDF generation failed: {e}")
            status["errors"].append(f"PDF: {str(e)}")

        # Step 2: Generate HTML
        self.logger.info("Step 2: Generating HTML")
        html_output = None
        try:
            html_output = await self._generate_html(input_data)
            status["html_generated"] = True
        except Exception as e:
            self.logger.warning(f"HTML generation failed: {e}")
            status["errors"].append(f"HTML: {str(e)}")

        # Step 3: Create package
        self.logger.info("Step 3: Creating ZIP package")
        package_output = None
        try:
            package_output = await self._create_package(input_data, pdf_output, html_output)
            status["package_created"] = True
        except Exception as e:
            self.logger.warning(f"Package creation failed: {e}")
            status["errors"].append(f"Package: {str(e)}")

        # Create manifest
        manifest = self._create_manifest(input_data, pdf_output, html_output, package_output)

        self.logger.info(
            "Final assembly complete",
            pdf=status["pdf_generated"],
            html=status["html_generated"],
            package=status["package_created"],
        )

        return AssemblyOutput(
            pdf=pdf_output,
            html=html_output,
            package=package_output,
            manifest=manifest,
            assembly_status=status,
        )

    async def write_to_state(self, output_data: AssemblyOutput) -> None:
        """Write assembly results to state."""
        # Save manifest
        manifest_path = self.shared_state.final_deliverables_dir / "manifest.json"
        manifest_path.write_text(json.dumps(output_data.manifest, indent=2))

        # Update state
        self.shared_state.update_state(
            final_deliverables={
                "pdf": str(output_data.pdf.file_path) if output_data.pdf else None,
                "html": str(output_data.html.file_path) if output_data.html else None,
                "package": str(output_data.package.file_path) if output_data.package else None,
                "manifest": str(manifest_path),
            },
            assembly_complete=True,
        )

        # Mark state as complete
        self.shared_state.mark_complete()
        self.shared_state.save_state_snapshot()

    async def validate_output(self, output_data: AssemblyOutput) -> tuple[bool, str]:
        """Validate assembly output."""
        issues = []

        # Need at least HTML output
        if not output_data.html:
            issues.append("HTML not generated")

        # PDF is important but optional
        if not output_data.pdf and not output_data.assembly_status.get("errors"):
            issues.append("PDF not generated (no error reported)")

        # Package should exist
        if not output_data.package:
            issues.append("Package not created")

        if issues:
            return False, f"Assembly validation issues: {'; '.join(issues)}"

        return True, f"Assembly complete: PDF={output_data.pdf is not None}, HTML={output_data.html is not None}, Package={output_data.package is not None}"

    async def calculate_quality_score(self, output_data: AssemblyOutput) -> float:
        """Calculate quality score."""
        score = 50.0

        # PDF bonus
        if output_data.pdf:
            score += 20

        # HTML bonus
        if output_data.html:
            score += 15
            if output_data.html.is_responsive:
                score += 5
            if output_data.html.has_audio_player:
                score += 3
            if output_data.html.has_video_player:
                score += 2

        # Package bonus
        if output_data.package:
            score += 10

        # Penalty for errors
        score -= len(output_data.assembly_status.get("errors", [])) * 5

        return max(0, min(100, score))

    async def _generate_pdf(self, input_data: AssemblyInput) -> Optional[PDFOutput]:
        """Generate professional PDF with inline images (HBR style).

        Key improvements:
        1. Strip title from article to avoid duplication (template adds title)
        2. Insert images INLINE in article sections (not at end)
        3. Same content structure as HTML
        """
        try:
            from weasyprint import HTML, CSS

            # Strip title from article content (template adds <h1>title</h1>)
            article_content = self._strip_title_from_article(input_data.article_content)

            # Insert images inline (same as HTML)
            article_with_images = self._insert_inline_images(
                article_content,
                input_data.visual_assets
            )

            # Convert markdown to HTML
            html_content = self._markdown_to_html(article_with_images)

            # Convert markdown image syntax to HTML img tags with proper paths
            html_content = self._convert_inline_images_to_html(html_content)

            # NO separate images section - images are inline now
            images_html = ""

            # Create PDF-optimized HTML
            pdf_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        @page {{
            size: A4;
            margin: 2.5cm;
            @top-center {{
                content: "{input_data.article_title}";
                font-size: 9pt;
                color: #666;
            }}
            @bottom-center {{
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #666;
            }}
        }}
        body {{
            font-family: 'Georgia', serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            font-size: 24pt;
            color: #1E3A5F;
            margin-bottom: 10pt;
            text-align: center;
        }}
        .subtitle {{
            font-size: 14pt;
            font-style: italic;
            text-align: center;
            color: #666;
            margin-bottom: 30pt;
        }}
        h2, h3 {{
            font-size: 14pt;
            color: #1E3A5F;
            margin-top: 20pt;
            margin-bottom: 10pt;
            border-bottom: 1pt solid #ccc;
            padding-bottom: 5pt;
        }}
        p {{
            margin-bottom: 12pt;
            text-align: justify;
        }}
        .visual-asset {{
            page-break-inside: avoid;
            margin: 20pt 0;
            text-align: center;
        }}
        .visual-asset img {{
            max-width: 100%;
            max-height: 400pt;
            height: auto;
            display: block;
            margin: 10pt auto;
            border: 1pt solid #ddd;
            border-radius: 4pt;
        }}
        .visual-asset figcaption {{
            font-size: 10pt;
            color: #666;
            font-style: italic;
            margin-top: 8pt;
        }}
        .insight {{
            background: #E8F4F8;
            padding: 15pt;
            margin: 15pt 0;
            border-left: 3pt solid #3D7EAA;
        }}
        .visuals-section {{
            margin-top: 30pt;
            padding-top: 20pt;
            border-top: 2pt solid #1E3A5F;
        }}
        .visuals-section h2 {{
            color: #1E3A5F;
            text-align: center;
            border-bottom: none;
        }}
        /* HBR Elements for PDF */
        .author-byline {{
            text-align: center;
            margin: 15pt 0 30pt 0;
            padding-bottom: 15pt;
            border-bottom: 1pt solid #ddd;
        }}
        .author-byline .author-name {{
            font-size: 11pt;
            color: #333;
        }}
        .author-byline .author-credentials {{
            font-size: 9pt;
            color: #666;
            font-style: italic;
        }}
        .idea-in-brief {{
            background: #F5F5F5;
            border-left: 3pt solid #C41E3A;
            padding: 15pt;
            margin: 20pt 0;
            page-break-inside: avoid;
        }}
        .idea-in-brief h3 {{
            color: #C41E3A;
            font-size: 12pt;
            margin-bottom: 12pt;
            text-transform: uppercase;
            letter-spacing: 1pt;
            border-bottom: none;
        }}
        .idea-in-brief h4 {{
            color: #1E3A5F;
            font-size: 9pt;
            text-transform: uppercase;
            margin-bottom: 3pt;
            margin-top: 10pt;
        }}
        .idea-in-brief p {{
            font-size: 10pt;
            margin-bottom: 0;
            text-align: left;
        }}
        .pull-quote {{
            border-left: 3pt solid #C41E3A;
            padding: 12pt 15pt;
            margin: 20pt 0;
            background: linear-gradient(to right, #F5F5F5 0%, transparent 100%);
            font-size: 12pt;
            font-style: italic;
            color: #1E3A5F;
        }}
    </style>
</head>
<body>
    <h1>{input_data.article_title}</h1>
    <p class="subtitle">{input_data.subtitle}</p>

    <div class="author-byline">
        <p class="author-name">by <strong>{input_data.author_name}</strong></p>
        <p class="author-credentials">{input_data.author_credentials}</p>
    </div>

    <aside class="idea-in-brief">
        <h3>Idea in Brief</h3>
        <h4>THE PROBLEM</h4>
        <p>{input_data.idea_in_brief.get('problem', '') if input_data.idea_in_brief else ''}</p>
        <h4>THE ARGUMENT</h4>
        <p>{input_data.idea_in_brief.get('argument', '') if input_data.idea_in_brief else ''}</p>
        <h4>THE SOLUTION</h4>
        <p>{input_data.idea_in_brief.get('solution', '') if input_data.idea_in_brief else ''}</p>
    </aside>

    {f'<blockquote class="pull-quote">"{input_data.pull_quotes[0]}"</blockquote>' if input_data.pull_quotes and len(input_data.pull_quotes) > 0 else ''}

    {html_content}

    {f'<blockquote class="pull-quote">"{input_data.pull_quotes[1]}"</blockquote>' if input_data.pull_quotes and len(input_data.pull_quotes) > 1 else ''}

    {images_html}
</body>
</html>
"""

            # Generate PDF
            safe_title = re.sub(r'[^\w\s-]', '', input_data.article_title).strip().replace(' ', '_').lower()
            filename = f"newsletter_{safe_title}.pdf"
            file_path = self.shared_state.final_deliverables_dir / filename

            # Use base_url to resolve relative paths
            base_url = str(self.shared_state.output_dir)
            html_doc = HTML(string=pdf_html, base_url=base_url)
            html_doc.write_pdf(str(file_path))

            # Estimate page count (rough estimate: ~500 words per page)
            page_count = max(1, input_data.word_count // 500)

            self.logger.info(f"PDF generated with {len(input_data.visual_assets)} images embedded")

            return PDFOutput(
                filename=filename,
                file_path=file_path,
                page_count=page_count,
            )

        except ImportError:
            self.logger.warning("WeasyPrint not available, trying alternative")
            return await self._generate_pdf_fallback(input_data)
        except Exception as e:
            self.logger.warning(f"PDF generation error: {e}")
            return await self._generate_pdf_fallback(input_data)

    def _build_images_html_for_pdf(self, visual_assets: list[dict]) -> str:
        """Build HTML for images using relative paths for WeasyPrint.

        ROBUST: Scans visuals_dir directly if visual_assets list is empty,
        ensuring images are always embedded regardless of state management issues.

        Uses relative paths (visuals/filename.png) which are resolved by
        WeasyPrint using the base_url set to the output directory.
        """
        parts = ['<div class="visuals-section">', '<h2>Visual Assets</h2>']
        images_found = 0

        # First, try to get images from visual_assets list
        image_assets = [a for a in visual_assets if a.get("filename", "").endswith((".png", ".jpg", ".jpeg"))]

        for asset in image_assets:
            filename = asset.get("filename", "")
            title = asset.get("title", "Visual Asset")
            abs_path = self.shared_state.visuals_dir / filename
            if abs_path.exists():
                # Use relative path - WeasyPrint resolves via base_url
                relative_path = f"visuals/{filename}"
                parts.append(f'''
                <figure class="visual-asset">
                    <img src="{relative_path}" alt="{title}">
                    <figcaption>{title}</figcaption>
                </figure>
                ''')
                images_found += 1
                self.logger.info(f"Added image from state: {filename} (path: {relative_path})")

        # FALLBACK: If no images from state, scan visuals directory directly
        if images_found == 0 and self.shared_state.visuals_dir.exists():
            self.logger.info("No images from state, scanning visuals directory directly...")
            for img_file in sorted(self.shared_state.visuals_dir.glob("*.png")):
                # Use relative path - WeasyPrint resolves via base_url
                relative_path = f"visuals/{img_file.name}"
                # Extract title from filename
                title = img_file.stem.replace("_", " ").replace("chart ", "").title()
                parts.append(f'''
                <figure class="visual-asset">
                    <img src="{relative_path}" alt="{title}">
                    <figcaption>{title}</figcaption>
                </figure>
                ''')
                images_found += 1
                self.logger.info(f"Added image from directory scan: {img_file.name} (path: {relative_path})")

        if images_found == 0:
            self.logger.warning("No images found for PDF embedding")
            return ""

        self.logger.info(f"Total images embedded in PDF: {images_found}")
        parts.append('</div>')
        return "\n".join(parts)

    async def _generate_pdf_fallback(self, input_data: AssemblyInput) -> Optional[PDFOutput]:
        """Fallback PDF generation using markdown file."""
        # Save as markdown for manual PDF conversion
        safe_title = re.sub(r'[^\w\s-]', '', input_data.article_title).strip().replace(' ', '_').lower()
        filename = f"newsletter_{safe_title}.md"
        file_path = self.shared_state.final_deliverables_dir / filename

        file_path.write_text(input_data.article_content)

        self.logger.info(f"PDF fallback: saved markdown to {filename}")
        return None

    async def _generate_html(self, input_data: AssemblyInput) -> HTMLOutput:
        """Generate responsive HTML with inline images (HBR style).

        Key improvements:
        1. Copy assets to final_deliverables for self-contained package
        2. Insert images INLINE in article sections (not at end)
        3. Fix audio/video paths
        4. Ensure same content as PDF
        """
        # Step 1: Copy visuals and multimedia to final_deliverables
        self._copy_assets_to_deliverables()

        # Step 2: Strip title from article (template adds its own <h1>)
        article_content = self._strip_title_from_article(input_data.article_content)

        # Step 3: Get article content with inline images inserted
        article_with_images = self._insert_inline_images(
            article_content,
            input_data.visual_assets
        )

        # Convert to HTML
        article_html = self._markdown_to_html(article_with_images)

        # Convert markdown image syntax to HTML img tags (paths are same dir now)
        article_html = self._convert_inline_images_to_html_for_web(article_html)

        # Step 3: Build media section with CORRECT paths (files are in same dir now)
        has_audio = False
        has_video = False
        media_html = ""

        multimedia = input_data.multimedia
        if multimedia:
            audio_player = ""
            video_player = ""

            if multimedia.get("audio", {}).get("path"):
                audio_path = Path(multimedia["audio"]["path"]).name
                # Audio is now in final_deliverables/
                audio_player = AUDIO_PLAYER_TEMPLATE.format(audio_path=audio_path)
                has_audio = True

            if multimedia.get("video", {}).get("path"):
                video_path = Path(multimedia["video"]["path"]).name
                video_player = VIDEO_PLAYER_TEMPLATE.format(video_path=video_path)
                has_video = True

            if audio_player or video_player:
                media_html = MEDIA_SECTION_TEMPLATE.format(
                    audio_player=audio_player,
                    video_player=video_player,
                )

        # NO separate visuals section - images are now inline in article_html

        # Calculate reading time
        reading_time = max(1, input_data.word_count // 200)

        # Build HBR structural elements HTML
        from src.utils.hbr_content_processor import IdeaInBrief

        # Author byline
        author_byline_html = f"""
        <div class="author-byline">
            <p class="author-name">by <strong>{input_data.author_name}</strong></p>
            <p class="author-credentials">{input_data.author_credentials}</p>
        </div>
        """

        # Idea in Brief sidebar
        iib = input_data.idea_in_brief or {}
        idea_in_brief_html = f"""
        <aside class="idea-in-brief">
            <h3>Idea in Brief</h3>
            <div class="iib-section">
                <h4>THE PROBLEM</h4>
                <p>{iib.get('problem', '')}</p>
            </div>
            <div class="iib-section">
                <h4>THE ARGUMENT</h4>
                <p>{iib.get('argument', '')}</p>
            </div>
            <div class="iib-section">
                <h4>THE SOLUTION</h4>
                <p>{iib.get('solution', '')}</p>
            </div>
        </aside>
        """

        # Pull quotes (distribute in article)
        quotes = input_data.pull_quotes or []
        pull_quote_1 = ""
        pull_quote_2 = ""
        if len(quotes) > 0:
            pull_quote_1 = f'<blockquote class="pull-quote">"{quotes[0]}"</blockquote>'
        if len(quotes) > 1:
            pull_quote_2 = f'<blockquote class="pull-quote">"{quotes[1]}"</blockquote>'

        # Fill template
        html_content = HTML_TEMPLATE.format(
            title=input_data.article_title,
            subtitle=input_data.subtitle,
            date=datetime.now().strftime("%B %d, %Y"),
            word_count=input_data.word_count,
            reading_time=reading_time,
            year=datetime.now().year,
            article_html=article_html,
            media_section=media_html,
            visuals_section="",  # Empty - images are inline now
            author_byline=author_byline_html,
            idea_in_brief=idea_in_brief_html,
            pull_quote_1=pull_quote_1,
            pull_quote_2=pull_quote_2,
        )

        # Save HTML
        safe_title = re.sub(r'[^\w\s-]', '', input_data.article_title).strip().replace(' ', '_').lower()
        filename = f"newsletter_{safe_title}.html"
        file_path = self.shared_state.final_deliverables_dir / filename

        file_path.write_text(html_content)

        return HTMLOutput(
            filename=filename,
            file_path=file_path,
            has_audio_player=has_audio,
            has_video_player=has_video,
            is_responsive=True,
        )

    async def _create_package(
        self,
        input_data: AssemblyInput,
        pdf: Optional[PDFOutput],
        html: Optional[HTMLOutput],
    ) -> PackageOutput:
        """Create ZIP package with all assets."""
        safe_title = re.sub(r'[^\w\s-]', '', input_data.article_title).strip().replace(' ', '_').lower()
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"newsletter_{safe_title}_{timestamp}.zip"
        file_path = self.shared_state.final_deliverables_dir / filename

        total_files = 0
        total_size = 0

        with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add PDF
            if pdf and pdf.file_path.exists():
                zf.write(pdf.file_path, f"pdf/{pdf.filename}")
                total_files += 1
                total_size += pdf.file_path.stat().st_size

            # Add HTML
            if html and html.file_path.exists():
                zf.write(html.file_path, f"html/{html.filename}")
                total_files += 1
                total_size += html.file_path.stat().st_size

            # Add article markdown
            article_path = self.shared_state.content_dir / "final_article.md"
            if article_path.exists():
                zf.write(article_path, "content/final_article.md")
                total_files += 1
                total_size += article_path.stat().st_size

            # Add visuals
            if self.shared_state.visuals_dir.exists():
                for visual_file in self.shared_state.visuals_dir.iterdir():
                    if visual_file.is_file():
                        zf.write(visual_file, f"visuals/{visual_file.name}")
                        total_files += 1
                        total_size += visual_file.stat().st_size

            # Add multimedia
            if self.shared_state.multimedia_dir.exists():
                for media_file in self.shared_state.multimedia_dir.iterdir():
                    if media_file.is_file():
                        zf.write(media_file, f"multimedia/{media_file.name}")
                        total_files += 1
                        total_size += media_file.stat().st_size

            # Add manifest
            manifest = {
                "title": input_data.article_title,
                "topic": input_data.topic,
                "created": datetime.now().isoformat(),
                "word_count": input_data.word_count,
                "files": total_files,
            }
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            total_files += 1

        return PackageOutput(
            filename=filename,
            file_path=file_path,
            total_files=total_files,
            total_size_mb=round(total_size / (1024 * 1024), 2),
        )

    def _markdown_to_html(self, markdown_text: str) -> str:
        """Convert markdown to HTML."""
        try:
            import markdown
            return markdown.markdown(
                markdown_text,
                extensions=['extra', 'smarty', 'tables'],
            )
        except ImportError:
            # Simple fallback conversion
            html = markdown_text

            # Headers
            html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
            html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
            html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

            # Bold and italic
            html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
            html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

            # Paragraphs
            paragraphs = html.split('\n\n')
            html = '\n'.join(
                f'<p>{p}</p>' if not p.startswith('<') else p
                for p in paragraphs
                if p.strip()
            )

            return html

    def _copy_assets_to_deliverables(self) -> None:
        """Copy visuals and multimedia to final_deliverables for self-contained HTML."""
        # Copy PNG images
        if self.shared_state.visuals_dir.exists():
            for img_file in self.shared_state.visuals_dir.glob("*.png"):
                dest = self.shared_state.final_deliverables_dir / img_file.name
                shutil.copy2(img_file, dest)
                self.logger.info(f"Copied visual asset: {img_file.name}")

        # Copy audio files
        if self.shared_state.multimedia_dir.exists():
            for audio_file in self.shared_state.multimedia_dir.glob("*.mp3"):
                dest = self.shared_state.final_deliverables_dir / audio_file.name
                shutil.copy2(audio_file, dest)
                self.logger.info(f"Copied audio: {audio_file.name}")

            # Copy video files
            for video_file in self.shared_state.multimedia_dir.glob("*.mp4"):
                dest = self.shared_state.final_deliverables_dir / video_file.name
                shutil.copy2(video_file, dest)
                self.logger.info(f"Copied video: {video_file.name}")

    def _insert_inline_images(self, article_content: str, visual_assets: list[dict]) -> str:
        """Insert images INLINE in article sections (HBR style).

        Images are inserted after key sections rather than at the end.
        This creates a professional magazine-like layout.
        """
        # Get PNG images (from state or directory scan)
        image_files = []
        for asset in visual_assets:
            if asset.get("filename", "").endswith((".png", ".jpg", ".jpeg")):
                image_files.append({
                    "filename": asset["filename"],
                    "title": asset.get("title", "Figure"),
                })

        # Fallback: scan directory if state is empty
        if not image_files and self.shared_state.visuals_dir.exists():
            for img in sorted(self.shared_state.visuals_dir.glob("*.png")):
                image_files.append({
                    "filename": img.name,
                    "title": img.stem.replace("_", " ").replace("chart ", "").title(),
                })

        if not image_files:
            return article_content

        # Split article into sections by ## headers
        sections = re.split(r'(\n## [^\n]+\n)', article_content)

        # Distribute images across sections (skip first/intro and last/conclusion)
        result_parts = []
        image_idx = 0
        figure_num = 1
        total_sections = len([s for s in sections if s.startswith('\n## ')])

        for i, section in enumerate(sections):
            result_parts.append(section)

            # Insert image after section content (not after header itself)
            # Skip intro (first section) and conclusion (last major section)
            if (section.startswith('\n## ') and
                'conclusion' not in section.lower() and
                'hook' not in section.lower() and
                image_idx < len(image_files)):

                # Find the next content section and insert image after it
                if i + 1 < len(sections):
                    img = image_files[image_idx]
                    # Insert figure with caption (HBR style)
                    figure_html = f'''

![Figure {figure_num}: {img["title"]}]({img["filename"]})
*Figure {figure_num}: {img["title"]}*

'''
                    result_parts.append(figure_html)
                    image_idx += 1
                    figure_num += 1

        # If we still have unused images, add them before conclusion
        while image_idx < len(image_files):
            img = image_files[image_idx]
            figure_html = f'''

![Figure {figure_num}: {img["title"]}]({img["filename"]})
*Figure {figure_num}: {img["title"]}*

'''
            # Find conclusion section and insert before it
            for j in range(len(result_parts) - 1, -1, -1):
                if 'conclusion' in result_parts[j].lower() and result_parts[j].startswith('\n## '):
                    result_parts.insert(j, figure_html)
                    break
            else:
                # No conclusion found, append before last section
                result_parts.insert(-1, figure_html)
            image_idx += 1
            figure_num += 1

        return ''.join(result_parts)

    def _strip_title_from_article(self, content: str) -> str:
        """Remove the leading title and fix duplicate headers.

        The PDF/HTML templates add their own title, so we strip the markdown title.
        Also removes duplicate section headers (e.g., ## The Hook followed by # The Hook).
        """
        # Remove leading # Title line
        lines = content.split('\n')
        start_idx = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            # Skip empty lines and the title line
            if not stripped:
                continue
            if stripped.startswith('# ') and i < 5:  # Title is usually in first 5 lines
                start_idx = i + 1
                # Also skip the subtitle if it's an italic line right after
                if start_idx < len(lines) and lines[start_idx].strip().startswith('*'):
                    start_idx += 1
                break
            else:
                break  # Non-empty line that's not a title, keep everything

        content = '\n'.join(lines[start_idx:]).strip()

        # Remove consecutive duplicate headers
        # Pattern 1: ## Header followed by # Header (same or similar text)
        # Pattern 2: ## Header followed by ## Header (exact duplicate)
        lines = content.split('\n')
        result_lines = []
        seen_headers = set()
        prev_header_text = None
        prev_header_level = None

        for line in lines:
            stripped = line.strip()

            # Check if this is a header line
            if stripped.startswith('## '):
                header_text = stripped[3:].strip().lower()
                # Normalize: remove colons and what follows (e.g., "Conclusion: The 18-Month Window" -> "conclusion")
                header_base = header_text.split(':')[0].strip()

                # Skip if we've seen this header recently (within last 5 lines)
                if header_base in seen_headers:
                    continue

                seen_headers.add(header_base)
                result_lines.append(line)
                prev_header_text = header_base
                prev_header_level = 2

            elif stripped.startswith('# '):
                header_text = stripped[2:].strip().lower()
                header_base = header_text.split(':')[0].strip()

                # Skip if matches previous h2 header
                if prev_header_text and header_base == prev_header_text:
                    continue

                # Skip if we've seen this header
                if header_base in seen_headers:
                    continue

                seen_headers.add(header_base)
                result_lines.append(line)
                prev_header_text = header_base
                prev_header_level = 1

            else:
                result_lines.append(line)
                # Reset seen headers after non-header content (new section)
                if stripped and len(stripped) > 50:  # Substantial content
                    seen_headers.clear()

        return '\n'.join(result_lines)

    def _convert_inline_images_to_html(self, html_content: str) -> str:
        """Fix image paths in HTML for PDF generation.

        Adds visuals/ prefix to img src for WeasyPrint base_url resolution.
        Works on already-converted HTML (from markdown library).
        """
        # Pattern for img tags with just filename (no path)
        # Match: src="chart_xxx.png" but NOT src="visuals/chart_xxx.png"
        img_pattern = r'<img([^>]*)\ssrc="([^"/]+\.png)"([^>]*)>'

        def replace_img(match):
            before = match.group(1)
            filename = match.group(2)
            after = match.group(3)
            # Add visuals/ prefix for WeasyPrint
            return f'<img{before} src="visuals/{filename}"{after}>'

        html_content = re.sub(img_pattern, replace_img, html_content)

        # Wrap standalone img tags in figure with caption
        html_content = re.sub(
            r'<p><img([^>]+)alt="([^"]*)"([^>]*)>\s*\n?<em>([^<]+)</em></p>',
            r'<figure class="visual-asset"><img\1alt="\2"\3><figcaption>\4</figcaption></figure>',
            html_content
        )

        return html_content

    def _convert_inline_images_to_html_for_web(self, html_content: str) -> str:
        """Convert img tags to proper figure elements for web display.

        Images are in SAME directory as HTML (copied to final_deliverables).
        Wraps images in <figure> with proper styling and captions.
        """
        # Pattern 1: <p><img ...></p> - wrapped in paragraph
        def replace_p_img(match):
            full_match = match.group(0)
            alt_match = re.search(r'alt="([^"]*)"', full_match)
            src_match = re.search(r'src="([^"]*)"', full_match)

            if alt_match and src_match:
                alt = alt_match.group(1)
                src = src_match.group(1)
                return f'''<figure class="visual-asset">
                    <img src="{src}" alt="{alt}" loading="lazy">
                    <figcaption>{alt}</figcaption>
                </figure>'''
            return full_match

        html_content = re.sub(r'<p>\s*<img[^>]+>\s*</p>', replace_p_img, html_content)

        # Pattern 2: <p><img ...>\n<em>caption</em></p> - with italic caption
        def replace_p_img_caption(match):
            full_match = match.group(0)
            alt_match = re.search(r'alt="([^"]*)"', full_match)
            src_match = re.search(r'src="([^"]*)"', full_match)
            caption_match = re.search(r'<em>([^<]+)</em>', full_match)

            if alt_match and src_match:
                alt = alt_match.group(1)
                src = src_match.group(1)
                caption = caption_match.group(1) if caption_match else alt
                return f'''<figure class="visual-asset">
                    <img src="{src}" alt="{alt}" loading="lazy">
                    <figcaption>{caption}</figcaption>
                </figure>'''
            return full_match

        html_content = re.sub(r'<p>\s*<img[^>]+>\s*\n?\s*<em>[^<]+</em>\s*</p>', replace_p_img_caption, html_content)

        # Remove any orphaned italic captions
        html_content = re.sub(r'\n<p>\*Figure \d+:[^*]+\*</p>', '', html_content)
        html_content = re.sub(r'\n<em>Figure \d+:[^<]+</em>', '', html_content)

        return html_content

    def _create_manifest(
        self,
        input_data: AssemblyInput,
        pdf: Optional[PDFOutput],
        html: Optional[HTMLOutput],
        package: Optional[PackageOutput],
    ) -> dict:
        """Create assembly manifest."""
        return {
            "title": input_data.article_title,
            "subtitle": input_data.subtitle,
            "topic": input_data.topic,
            "word_count": input_data.word_count,
            "created": datetime.now().isoformat(),
            "deliverables": {
                "pdf": {
                    "generated": pdf is not None,
                    "filename": pdf.filename if pdf else None,
                    "pages": pdf.page_count if pdf else None,
                },
                "html": {
                    "generated": html is not None,
                    "filename": html.filename if html else None,
                    "responsive": html.is_responsive if html else False,
                    "has_audio": html.has_audio_player if html else False,
                    "has_video": html.has_video_player if html else False,
                },
                "package": {
                    "created": package is not None,
                    "filename": package.filename if package else None,
                    "files": package.total_files if package else 0,
                    "size_mb": package.total_size_mb if package else 0,
                },
            },
            "visual_assets": len(input_data.visual_assets),
            "multimedia": {
                "audio": input_data.multimedia.get("audio", {}).get("filename"),
                "video": input_data.multimedia.get("video", {}).get("filename"),
            },
        }


def create_assembly_agent(shared_state: SharedState) -> AssemblyAgent:
    """Factory function to create AssemblyAgent."""
    return AssemblyAgent(shared_state)
