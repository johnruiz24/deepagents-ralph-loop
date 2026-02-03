# HBR Article Standards Skill

This skill provides the templates, guidelines, and logic required to generate articles that meet the rigorous standards of Harvard Business Review.

## Features

- **Structural Templates:** HTML and CSS for HBR-style layouts.
- **Guideline Documents:** Detailed guides on writing style, visual standards, and structural elements.
- **Automated Content Generation:** Functions to create "Idea in Brief" sidebars and pull quotes.

## How to Use

1.  **Integrate with Assembly Agent:** The `AssemblyAgent` should use the templates from this skill to generate the final PDF and HTML.
2.  **Integrate with HBR Editor Agent:** The `HBREditorAgent` should use the guidelines to refine the article's tone and structure.
3.  **Call Generation Functions:** Use the provided functions to automatically generate sidebars and pull quotes from the main article content.

## Key Components

- **`/templates/`:** Contains `hbr_layout_template.html` and `hbr_pdf_template.css`.
- **`/guidelines/`:** Contains detailed Markdown files on HBR standards.
- **`/examples/`:** Contains sample outputs for reference.
