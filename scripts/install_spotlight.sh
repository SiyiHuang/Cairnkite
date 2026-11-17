#!/bin/bash
set -euo pipefail

version=$(/usr/bin/xcrun --sdk macosx --show-sdk-version)
[[ "${version%%.*}" -ge 27 ]] || { echo 'Use macOS SDK 27 or newer for SpotlightSearchTool.' >&2; exit 1; }
root="$PWD/.runtime/apple-spotlight"
mkdir -p "$root"
identity=$(printf '%s' "$PWD" | shasum -a 256 | cut -c1-16)
stage=$(mktemp -d "$root/.stage.XXXXXXXX")
trap 'rm -rf "$stage"' EXIT
app="$stage/LocalSpotlight.app/Contents"
mkdir -p "$app/MacOS" "$app/Resources"
touch "$app/Resources/native-ranked-query"
cat >"$app/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>dev.local-ai-toolkit.spotlight.r$identity</string>
<key>CFBundleExecutable</key><string>LocalSpotlight</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSUIElement</key><true/>
</dict></plist>
EOF
/usr/bin/xcrun --sdk macosx swiftc -parse-as-library -swift-version 6 -O -target arm64-apple-macos27.0 \
  native/spotlight/Spotlight.swift -o "$app/MacOS/LocalSpotlight"
/usr/bin/codesign --force --sign - "$stage/LocalSpotlight.app"
/usr/bin/codesign --verify --strict "$stage/LocalSpotlight.app"
release="LocalSpotlight-$(basename "$stage").app"
mv "$stage/LocalSpotlight.app" "$root/$release"
ln -s "$release" "$stage/Current.app"
mv -fh "$stage/Current.app" "$root/Current.app"
