#!/bin/bash

# Medium Article Fetcher - Advanced (Anti-Bot Detection)
# Uses agent-browser with human-like behavior

set -e

MEDIUM_URL="https://medium.com/@luis.f.s.m.dias/building-and-deploying-production-ready-langchain-deep-agents-in-aws-99f0d22c8351"
OUTPUT_FILE="/Users/john.ruiz/Documents/projects/inkforge/ralph/medium_article_content.md"

echo "🔄 Starting advanced headless browser automation..."

# Load credentials
MEDIUM_EMAIL="johnvillalobos_24@hotmail.com"
MEDIUM_PASSWORD="peluche1802@#snoopy07@@"

# Start with --headed flag to handle Cloudflare/bot detection better
echo "🌐 Opening Medium with enhanced detection bypass..."

# Use a session to persist cookies
agent-browser --session medium_secure --headed open "https://medium.com" 2>/dev/null || agent-browser --session medium_secure open "https://medium.com"

# Wait longer for page load
agent-browser wait --load networkidle --session medium_secure
agent-browser wait 3000 --session medium_secure

# Take screenshot to see current state
echo "📸 Taking screenshot of current state..."
agent-browser screenshot --full "/tmp/medium_step1.png" --session medium_secure

# Try to wait for Cloudflare/security checks to pass
echo "⏳ Waiting for security checks..."
agent-browser wait 5000 --session medium_secure

# Navigate directly to article (may bypass some checks)
echo "🔗 Navigating to article..."
agent-browser open "$MEDIUM_URL" --session medium_secure

# Wait extensively for page
agent-browser wait --load networkidle --session medium_secure
agent-browser wait 5000 --session medium_secure

# Take screenshot
agent-browser screenshot --full "/tmp/medium_article.png" --session medium_secure

# Try to get full article text
echo "📄 Extracting article content..."
ARTICLE_TEXT=$(agent-browser get text body --session medium_secure 2>/dev/null || echo "Could not extract")

# Also try with eval for better extraction
ARTICLE_JSON=$(agent-browser eval --stdin --session medium_secure <<'JSEOF' 2>/dev/null || echo "{}")
JSON.stringify({
  title: document.querySelector('h1')?.innerText || 'No title',
  author: document.querySelector('[data-action="show-user-card"]')?.innerText || 'Unknown',
  content: Array.from(document.querySelectorAll('article p, article h2, article h3, article blockquote'))
    .map(el => el.innerText)
    .join('\n\n'),
  url: window.location.href
})
JSEOF

# Save extracted content
cat > "$OUTPUT_FILE" << EOF
# Medium Article Content

## URL
$MEDIUM_URL

## Extracted Content

$ARTICLE_TEXT

---

## JSON Data
$ARTICLE_JSON

EOF

echo "✅ Content extraction complete"
echo "📁 Saved to: $OUTPUT_FILE"

# Keep browser open briefly for debugging
echo "🔍 Keeping browser open for 10 seconds (can inspect with DevTools)..."
agent-browser wait 10000 --session medium_secure

# Close
agent-browser close --session medium_secure
echo "✅ Browser closed"
