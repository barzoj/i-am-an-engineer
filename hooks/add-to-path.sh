#!/usr/bin/env bash
# SessionStart hook: put i-am-an-engineer's bin/ on PATH for later Bash calls.
root="${1:-${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-}}}"
[ -n "$root" ] && command -v cygpath >/dev/null 2>&1 && root="$(cygpath -u "$root")"
[ -n "$root" ] && [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -x "$root/bin/iae" ] || exit 0
grep -qs "i-am-an-engineer-path" "$CLAUDE_ENV_FILE" && exit 0
printf 'export PATH="%s/bin:$PATH" # i-am-an-engineer-path\n' "$root" >> "$CLAUDE_ENV_FILE"
exit 0
