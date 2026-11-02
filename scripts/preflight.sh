#!/usr/bin/env bash
# TIP preflight — validates dtctl readiness. (MCP is validated separately by the agent.)
# Usage: bash preflight.sh <dtctl-context>
set -uo pipefail
CTX="${1:-}"
CTXFLAG=""; [ -n "$CTX" ] && CTXFLAG="--context $CTX"
ok=0; fail=0
pass(){ echo "  ✅ $1"; ok=$((ok+1)); }
bad(){  echo "  ❌ $1"; fail=$((fail+1)); }

echo "== TIP preflight: dtctl =="

# 1. dtctl present
if ! command -v dtctl >/dev/null 2>&1; then bad "dtctl not found in PATH"; echo "ABORT"; exit 2; fi
pass "dtctl found: $(command -v dtctl)"

# 2. context
CUR=$(dtctl config current-context 2>/dev/null | tr -d '"')
if [ -n "$CTX" ]; then echo "  • requested context: $CTX (current: ${CUR:-none})"; else echo "  • current context: ${CUR:-none}"; fi

# 3. auth / token
WHO=$(dtctl auth whoami --plain $CTXFLAG 2>&1)
if echo "$WHO" | grep -qiE "invalid_grant|refresh token|validation_error|UNSUCCESSFUL"; then
  bad "OAuth token expired / invalid"
  echo "     → ask the user to run:  !dtctl auth login ${CTX:+--context $CTX}"
else
  USER=$(echo "$WHO" | grep -iE "User Name|Email" | head -1 | sed 's/^[^:]*: *//')
  ENV=$(echo "$WHO" | grep -iE "Environment" | head -1 | sed 's/^[^:]*: *//')
  pass "authenticated as ${USER:-unknown}  env=${ENV:-?}"
fi

# 4. read access (trivial DQL)
RD=$(dtctl query $CTXFLAG -f <(echo 'fetch dt.entity.host | summarize c=count()') -o json 2>/dev/null)
if echo "$RD" | grep -q '"c"'; then
  N=$(echo "$RD" | python3 -c "import sys,json;print(json.load(sys.stdin)['records'][0]['c'])" 2>/dev/null)
  pass "read access OK (hosts=$N)"
else
  bad "read access FAILED (cannot run DQL)"
fi

# 5. app IDs (needed for deep-links)
APPS=$(dtctl get apps $CTXFLAG -o json 2>/dev/null | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin); d=d if isinstance(d,list) else d.get('result',[])
  print(len([a for a in d if isinstance(a,dict)]))
except: print(0)" 2>/dev/null)
if [ "${APPS:-0}" -gt 0 ] 2>/dev/null; then pass "app registry readable ($APPS apps) — use for deep-links"; else bad "could not list apps (deep-links may be guesses)"; fi

# 6. write access (optional; needed to upload supporting dashboards/segments)
echo "  • write access: not auto-tested (would create objects). Confirm the context SafetyLevel"
echo "    is readwrite-* if you plan to upload dashboards. Check: dtctl config get-contexts"

echo "== dtctl preflight: $ok passed, $fail failed =="
echo "NEXT: agent must validate the Dynatrace MCP server by calling a lightweight MCP read tool"
echo "      (e.g. get_dql_knowledgebase / list_strato_components). Record both results."
[ "$fail" -gt 0 ] && exit 1 || exit 0
