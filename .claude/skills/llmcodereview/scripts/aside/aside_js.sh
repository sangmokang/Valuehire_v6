#!/bin/bash
# usage: aside_js.sh <jsfile>   (runs JS in Cursor tab, prints result)
source $(dirname "$0")/env.sh; W=$ASIDE_WIN; T=${CURSOR_TAB:?}
osascript - "$W" "$T" "$1" <<'AS'
on run argv
set w to (item 1 of argv) as integer
set t to (item 2 of argv) as integer
set js to read POSIX file (item 3 of argv) as «class utf8»
tell application "Aside"
return execute (tab id t of window id w) javascript js
end tell
end run
AS
