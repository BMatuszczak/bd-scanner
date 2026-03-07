#!/bin/bash
# Sets up a weekly Monday 8am run using macOS launchd (no cron needed)
# Run once: bash schedule_macos.sh

PLIST=~/Library/LaunchAgents/com.latitudeit.bdscanner.plist
PYTHON=$(which python3)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.latitudeit.bdscanner</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$SCRIPT_DIR/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>10</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/scanner.log</string>
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/scanner.log</string>
</dict>
</plist>
EOF

launchctl load "$PLIST"
echo "Scheduled! BD Scanner will run every Monday at 8:00am."
echo "Log output: $SCRIPT_DIR/scanner.log"
