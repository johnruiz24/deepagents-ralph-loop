#!/bin/bash

# Medium Article Fetcher - Headless (no visible Chrome)
# Uses agent-browser to access Medium and extract article content

set -e

MEDIUM_URL="https://medium.com/@luis.f.s.m.dias/building-and-deploying-production-ready-langchain-deep-agents-in-aws-99f0d22c8351"
OUTPUT_FILE="/Users/john.ruiz/Documents/projects/inkforge/ralph/medium_article_content.md"

echo "🔄 Starting headless browser automation..."

# Load credentials from .env
MEDIUM_EMAIL="johnvillalobos_24@hotmail.com"
MEDIUM_PASSWORD="peluche1802@#snoopy07@@"

# Step 1: Open Medium homepage
echo "📱 Opening Medium..."
agent-browser open "https://medium.com" --session medium_reader

# Step 2: Wait for page load
agent-browser wait --load networkidle --session medium_reader

# Step 3: Take snapshot to find login button
echo "📸 Looking for login options..."
agent-browser snapshot -i --session medium_reader > /tmp/medium_snapshot.txt

# Step 4: Click on sign in / login link
echo "🔐 Attempting to access login..."
agent-browser click @e1 --session medium_reader || agent-browser find text "Sign in" click --session medium_reader || true

# Wait for navigation
agent-browser wait --load networkidle --session medium_reader
agent-browser wait 2000 --session medium_reader

# Step 5: Look for Facebook login button
echo "📘 Finding Facebook login option..."
agent-browser snapshot -i --session medium_reader > /tmp/medium_login_snapshot.txt

# Click Facebook login if available
agent-browser find text "Facebook" click --session medium_reader || agent-browser find role button click --name "Facebook" --session medium_reader || true

# Wait for Facebook popup/redirect
agent-browser wait --load networkidle --session medium_reader
agent-browser wait 2000 --session medium_reader

# Step 6: Check if we're on Facebook login page
FB_URL=$(agent-browser get url --session medium_reader)
echo "Current URL: $FB_URL"

if [[ $FB_URL == *"facebook.com"* ]]; then
    echo "✅ Redirected to Facebook"

    # Step 7: Fill Facebook credentials
    agent-browser snapshot -i --session medium_reader > /tmp/facebook_login_snapshot.txt

    # Fill email
    agent-browser find placeholder "Email" fill "$MEDIUM_EMAIL" --session medium_reader || \
    agent-browser find label "Email" fill "$MEDIUM_EMAIL" --session medium_reader || true

    # Fill password
    agent-browser find placeholder "Password" fill "$MEDIUM_PASSWORD" --session medium_reader || \
    agent-browser find label "Password" fill "$MEDIUM_PASSWORD" --session medium_reader || true

    # Find and click login button
    agent-browser find role button click --name "Log In" --session medium_reader || \
    agent-browser find text "Log In" click --session medium_reader || true

    # Wait for authentication
    agent-browser wait --load networkidle --session medium_reader
    agent-browser wait 3000 --session medium_reader
fi

# Step 8: Navigate to the article
echo "🔗 Navigating to article..."
agent-browser open "$MEDIUM_URL" --session medium_reader

# Wait for article to load
agent-browser wait --load networkidle --session medium_reader
agent-browser wait 2000 --session medium_reader

# Step 9: Get article content
echo "📄 Extracting article content..."
ARTICLE_CONTENT=$(agent-browser get text body --session medium_reader)

# Step 10: Get full page screenshot for reference
agent-browser screenshot --full "/Users/john.ruiz/Documents/projects/inkforge/ralph/article_screenshot.png" --session medium_reader

# Step 11: Save content to file
cat > "$OUTPUT_FILE" << 'EOF'
# Medium Article Content

## Extracted from:
https://medium.com/@luis.f.s.m.dias/building-and-deploying-production-ready-langchain-deep-agents-in-aws-99f0d22c8351

## Content:
EOF

echo "$ARTICLE_CONTENT" >> "$OUTPUT_FILE"

# Step 12: Close browser session
agent-browser close --session medium_reader

echo "✅ Article saved to: $OUTPUT_FILE"
echo "📸 Screenshot saved to: /Users/john.ruiz/Documents/projects/inkforge/ralph/article_screenshot.png"
