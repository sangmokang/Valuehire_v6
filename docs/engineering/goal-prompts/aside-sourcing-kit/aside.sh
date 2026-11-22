#!/bin/bash
W=665806854
case "$1" in
 nav) osascript -e 'on run argv' -e 'tell application "Aside" to set URL of tab id ((item 1 of argv) as integer) of window id ((item 3 of argv) as integer) to (item 2 of argv)' -e 'end run' "$2" "$3" "$W" ;;
 js) osascript -e 'on run argv' -e 'tell application "Aside" to execute tab id ((item 1 of argv) as integer) of window id ((item 3 of argv) as integer) javascript (item 2 of argv)' -e 'end run' "$2" "$(cat "$3")" "$W" ;;
 tabs) osascript -e "tell application \"Aside\"
set o to \"\"
repeat with t in tabs of window id $W
set o to o & (id of t) & \" | \" & (URL of t) & linefeed
end repeat
return o
end tell" ;;
esac
