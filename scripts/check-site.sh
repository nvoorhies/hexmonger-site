#!/usr/bin/env bash
# Checks the site before it deploys: every page has a title, and every
# root-relative or relative link/src in the HTML and CSS lands on a file.
set -euo pipefail
cd "$(dirname "$0")/.."
fail=0
pages=$(find . -name '*.html' -not -path './.git/*' -not -path './_site/*')
for p in $pages; do
  grep -q '<title>[^<]\+</title>' "$p" || { echo "no <title>: $p"; fail=1; }
  dir=$(dirname "$p")
  # strip HTML comments so commented-out links (e.g. future YouTube) are ignored
  refs=$(perl -0pe 's/<!--.*?-->//gs' "$p" | grep -oE '(href|src)="[^"#]+"' | sed -E 's/^(href|src)="//; s/"$//' || true;
         perl -0pe 's/<!--.*?-->//gs' "$p" | grep -oE 'srcset="[^"]+"' | sed -E 's/^srcset="//; s/"$//' | tr "," "\n" | awk "{print \$1}" || true)
  for r in $refs; do
    case "$r" in http*|mailto:*|//*) continue;; esac
    if [[ "$r" == /* ]]; then f=".${r}"; else f="$dir/$r"; fi
    [[ "$f" == */ ]] && f="${f}index.html"
    [ -e "$f" ] || { echo "broken link in $p: $r"; fail=1; }
  done
done
for css in assets/*.css; do
  for u in $(grep -oE 'url\("[^"]+"\)' "$css" | sed -E 's/url\("//; s/"\)//' | grep -v '^data:' || true); do
    [ -e "assets/$u" ] || { echo "broken url() in $css: $u"; fail=1; }
  done
done
[ "$(cat CNAME)" = "hexmonger.com" ] || { echo "CNAME is not hexmonger.com"; fail=1; }
[ $fail -eq 0 ] && echo "site OK"
exit $fail
