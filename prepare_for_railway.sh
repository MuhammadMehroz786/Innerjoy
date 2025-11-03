#!/bin/bash

echo "=========================================="
echo "Railway Deployment Preparation Script"
echo "=========================================="
echo ""

# Check if credentials.json exists
if [ ! -f "credentials.json" ]; then
    echo "❌ Error: credentials.json not found!"
    echo "   Make sure you have the Google Service Account credentials file."
    exit 1
fi

echo "✓ Found credentials.json"
echo ""

# Convert to base64
echo "Converting credentials to base64..."
echo "=========================================="
echo ""
echo "GOOGLE_SERVICE_ACCOUNT_JSON="
cat credentials.json | base64
echo ""
echo "=========================================="
echo ""
echo "✓ Copy the above base64 string (starting after GOOGLE_SERVICE_ACCOUNT_JSON=)"
echo "  and paste it as an environment variable in Railway"
echo ""

# Check for .env file
if [ -f ".env" ]; then
    echo "✓ Found .env file"
    echo ""
    echo "Current environment variables:"
    echo "=========================================="
    cat .env | grep -v "^#" | grep "="
    echo "=========================================="
    echo ""
    echo "⚠️  Make sure to set ALL these variables in Railway!"
else
    echo "⚠️  No .env file found. Make sure to set these variables in Railway:"
    echo "   - RESPOND_API_KEY"
    echo "   - RESPOND_SPACE_ID"
    echo "   - ZOOM_PREVIEW_LINK"
    echo "   - GOOGLE_SHEETS_ID"
    echo "   - GOOGLE_SERVICE_ACCOUNT_JSON (from above)"
fi

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo "1. Copy the GOOGLE_SERVICE_ACCOUNT_JSON base64 string above"
echo "2. Push code to GitHub:"
echo "   git add ."
echo "   git commit -m 'Prepare for Railway deployment'"
echo "   git push"
echo "3. Create new project on Railway (https://railway.app)"
echo "4. Deploy from GitHub"
echo "5. Add all environment variables"
echo "6. Generate domain"
echo "7. Update Respond.io webhook URL"
echo ""
echo "✓ Ready for deployment!"
