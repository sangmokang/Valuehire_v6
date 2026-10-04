#!/bin/bash
# usage: insert_prompt.sh <prompt.txt>  -> puts text into composer (does not send)
S=$(dirname "$0"); B=$(base64 < "$1" | tr -d '\n')
cat > $S/_ins.js <<JS
(function(){var t=decodeURIComponent(escape(atob("$B")));var el=document.querySelector('div[contenteditable=true]');if(!el)return "NO_EDITOR";el.focus();var dt=new DataTransfer();dt.setData('text/plain',t);el.dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true}));return "len_in="+t.length+" len_editor="+el.innerText.length;})()
JS
bash $S/aside_js.sh $S/_ins.js
