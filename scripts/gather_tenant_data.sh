#!/usr/bin/env bash
# TIP — gather live tenant stats, app IDs and candidate entity IDs for the deck.
# Usage: bash gather_tenant_data.sh <dtctl-context>
set -uo pipefail
CTX="${1:-}"; CF=""; [ -n "$CTX" ] && CF="--context $CTX"
q(){ dtctl query $CF -f <(echo "$1") -o json 2>/dev/null; }
num(){ q "$1" | python3 -c "import sys,json
try: print(json.load(sys.stdin)['records'][0].get('c','n/a'))
except: print('n/a')"; }

echo "#################### HEADLINE STATS ####################"
printf "%-26s %s\n" "Hosts"              "$(num 'fetch dt.entity.host | summarize c=count()')"
printf "%-26s %s\n" "Services"           "$(num 'fetch dt.entity.service | summarize c=count()')"
printf "%-26s %s\n" "Process groups"     "$(num 'fetch dt.entity.process_group | summarize c=count()')"
printf "%-26s %s\n" "Process instances"  "$(num 'fetch dt.entity.process_group_instance | summarize c=count()')"
printf "%-26s %s\n" "K8s clusters"       "$(num 'fetch dt.entity.kubernetes_cluster | summarize c=count()')"
printf "%-26s %s\n" "K8s namespaces"     "$(num 'fetch dt.entity.cloud_application_namespace | summarize c=count()')"
printf "%-26s %s\n" "K8s workloads"      "$(num 'fetch dt.entity.cloud_application | summarize c=count()')"
printf "%-26s %s\n" "Spans (2h)"         "$(num 'fetch spans, from:now()-2h | summarize c=count()')"
printf "%-26s %s\n" "Logs (2h)"          "$(num 'fetch logs, from:now()-2h | summarize c=count()')"
printf "%-26s %s\n" "Distinct problems 7d" "$(num 'fetch events, from:now()-7d | filter event.kind=="DAVIS_PROBLEM" | summarize c=countDistinctExact(display_id)')"

echo; echo "#################### DB SYSTEMS (24h traces) ####################"
q 'fetch spans, from:now()-24h | filter isNotNull(db.system) | summarize c=count(), by:{db.system} | sort c desc | limit 8' \
 | python3 -c "import sys,json
try:
 [print(' ',r.get('db.system'),r.get('c')) for r in json.load(sys.stdin)['records']]
except Exception as e: print('  (none)')"

echo; echo "#################### TOP SERVICES (deep-link candidates) ####################"
q 'timeseries r=sum(dt.service.request.count), by:{dt.entity.service}, from:now()-24h | fieldsAdd t=arraySum(r), name=entityName(dt.entity.service) | sort t desc | limit 6 | fields dt.entity.service, name' \
 | python3 -c "import sys,json
try:
 [print(' ',r.get('dt.entity.service'),'|',r.get('name')) for r in json.load(sys.stdin)['records']]
except: print('  (none)')"

echo; echo "#################### HOST GROUPS / K8s CLUSTERS ####################"
q 'fetch dt.entity.host_group | fields id, entity.name' | python3 -c "import sys,json
try:
 [print('  hostgroup',r.get('id'),'|',r.get('entity.name')) for r in json.load(sys.stdin)['records']]
except: pass"
q 'fetch dt.entity.kubernetes_cluster | fields id, entity.name' | python3 -c "import sys,json
try:
 [print('  cluster',r.get('id'),'|',r.get('entity.name')) for r in json.load(sys.stdin)['records']]
except: pass"

echo; echo "#################### APP IDs (deep-link base = https://<tenant>/ui/apps/<id>) ####################"
dtctl get apps $CF -o json 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin); d=d if isinstance(d,list) else d.get('result',[])
want=('infraops','discovery','smartscape','services','distributedtracing','database','clouds','automations','davis.problems','logs','kubernetes','debugger','dashboards','vulnerabilities','synthetic','ai','observ','network')
for a in d:
  if isinstance(a,dict) and any(w in (a.get('id') or '') for w in want):
    print('  ',a.get('id'),'|',a.get('name'))
" 2>/dev/null | sort -u
echo; echo "Paste these numbers/IDs into your config.json (step 3)."
