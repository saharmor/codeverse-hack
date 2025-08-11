#!/bin/bash

# Build signed and notarized DMG for CodeVerse
# Usage: ./scripts/build-signed-dmg.sh

set -e

echo "🔨 Building CodeVerse DMG with signing and notarization..."

# Check if required environment variables are set
if [ -z "$APPLE_SIGNING_IDENTITY" ] || [ -z "$APPLE_ID" ] || [ -z "$APPLE_PASSWORD" ] || [ -z "$APPLE_TEAM_ID" ]; then
    echo "❌ Missing required environment variables:"
    echo "   APPLE_SIGNING_IDENTITY - e.g., 'Developer ID Application: Your Name (TEAM_ID)'"
    echo "   APPLE_ID - Your Apple ID email"
    echo "   APPLE_PASSWORD - App-specific password"
    echo "   APPLE_TEAM_ID - Your Apple Developer team ID"
    echo ""
    echo "💡 Create these in your shell:"
    echo "   export APPLE_SIGNING_IDENTITY=\"Developer ID Application: Your Name (TEAM_ID)\""
    echo "   export APPLE_ID=\"your-apple-id@example.com\""
    echo "   export APPLE_PASSWORD=\"your-app-specific-password\""
    echo "   export APPLE_TEAM_ID=\"YOUR_TEAM_ID\""
    exit 1
fi

# Build the DMG
echo "📦 Building Tauri app..."
npm run tauri build

DMG_PATH="src-tauri/target/release/bundle/dmg/CodeVerse_0.1.0_aarch64.dmg"

# Check if DMG was created
if [ ! -f "$DMG_PATH" ]; then
    echo "❌ DMG file not found at $DMG_PATH"
    exit 1
fi

echo "✅ DMG created successfully!"
echo "📍 Location: $DMG_PATH"
echo "💾 Size: $(du -h "$DMG_PATH" | cut -f1)"

# Optionally notarize if the DMG is signed
if codesign -dv "$DMG_PATH" 2>/dev/null; then
    echo "🔐 DMG appears to be signed, starting notarization..."

    echo "📤 Submitting to Apple for notarization..."
    xcrun notarytool submit "$DMG_PATH" \
        --apple-id "$APPLE_ID" \
        --team-id "$APPLE_TEAM_ID" \
        --password "$APPLE_PASSWORD" \
        --wait

    if [ $? -eq 0 ]; then
        echo "📎 Stapling notarization ticket..."
        xcrun stapler staple "$DMG_PATH"

        if [ $? -eq 0 ]; then
            echo "✅ DMG successfully notarized and stapled!"
        else
            echo "⚠️  Notarized but stapling failed"
        fi
    else
        echo "❌ Notarization failed"
        exit 1
    fi
else
    echo "⚠️  DMG is not signed - users will need to right-click -> Open"
    echo "🔗 See SIGNING_SETUP.md for instructions on setting up code signing"
fi

echo ""
echo "🎉 Build complete!"
echo "📦 DMG: $DMG_PATH"
echo "🚀 Ready for distribution!"
