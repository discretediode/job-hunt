#!/bin/bash
# ponytail: one curl per id, strip tags. No parser class needed.
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
for id in "$@"; do
  echo "===== $id ====="
  curl -sS -A "$UA" "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/$id" \
  | python3 -c "
import sys,re,html
h=sys.stdin.read()
m=re.search(r'show-more-less-html__markup(.*?)</div>',h,re.S)
t=html.unescape(re.sub(r'<[^>]+>',' ',m.group(1))) if m else 'NO DESCRIPTION'
print(re.sub(r'\s+',' ',t)[:1700])
"
  sleep 1
done
