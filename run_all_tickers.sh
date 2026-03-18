#!/bin/bash
BASE_URL="http://localhost:8000"
API_KEY="spock-prod-api-key-2026"
RESULTS_FILE="/root/www/projects/back/python/spock/results.log"
MAX_REPORTS=4
MAX_PASSES=16
PARALLEL=5

echo "ticker,type,pass,discovered,analyzed,cached,failed,remaining,score,classification,http_code" > "$RESULTS_FILE"

process_ticker() {
    local type=$1
    local ticker=$2

    for pass in $(seq 1 $MAX_PASSES); do
        local response http_code body
        response=$(curl -s -w "\n%{http_code}" -X POST \
            "${BASE_URL}/${type}/funds/${ticker}/discover?maxReports=${MAX_REPORTS}" \
            -H "x-api-key: ${API_KEY}" \
            -H "Content-Type: application/json" \
            --max-time 120 2>/dev/null)

        http_code=$(echo "$response" | tail -1)
        body=$(echo "$response" | sed '$d')

        if [ "$http_code" = "200" ]; then
            local vals
            vals=$(echo "$body" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d['discovered'],d['analyzed'],d['cached'],d['failed'],d['remaining'],d['score'],d.get('classification'))
" 2>/dev/null)
            read -r discovered analyzed cached failed remaining score classification <<< "$vals"
            echo "${ticker},${type},${pass},${discovered},${analyzed},${cached},${failed},${remaining},${score},${classification},${http_code}" >> "$RESULTS_FILE"
            echo "[$(date +%H:%M:%S)] ${type}/${ticker} p${pass}: d=${discovered} a=${analyzed} c=${cached} f=${failed} r=${remaining} s=${score} cl=${classification}" >&2

            if [ "$remaining" = "0" ]; then
                return 0
            fi
        else
            echo "${ticker},${type},${pass},,,,,,,${http_code}" >> "$RESULTS_FILE"
            echo "[$(date +%H:%M:%S)] ${type}/${ticker} p${pass}: HTTP ${http_code}" >&2
            sleep 3
        fi
    done
}

export -f process_ticker
export BASE_URL API_KEY RESULTS_FILE MAX_REPORTS MAX_PASSES

echo "=== Starting parallel discover (maxReports=${MAX_REPORTS}, ${PARALLEL} concurrent, up to ${MAX_PASSES} passes) at $(date) ===" >&2

# Build job list: type ticker
{
    for t in BTLG11 GGRC11 BRCO11 HGLG11 XPLG11 VILG11 INLG11 TRBL11 HSLG11 NEWL11 LVBI11 XPML11 VISC11 HGBS11 PMLL11 HSML11 CPSH11 BBIG11 PVBI11 TEPP11 KORE11 FATN11 HGRE11 JSRE11 GTWR11 HGRU11 RBVA11 KNRI11 TRXF11 TVRI11 GARE11 ALZR11 RZAT11 NSLU11 HTMX11 TGAR11 RZTR11 SNFZ11 BCIA11 KFOF11 HFOF11 MCRE11 BTHF11 CCME11 ITRI11 RBFM11 PSEC11 WHGR11 MANA11 GAME11 KNHF11 IRIM11 TRXY11; do
        echo "equity $t"
    done
    for t in RECR11 CLIN11 PCIP11 VGIR11 ICRI11 KCRE11 XPCI11 KNHY11 AFHI11 HGCR11 KNCR11 MXRF11 BTCI11 MCCI11 VGIP11 KNIP11 KNSC11 PORD11 KNUQ11 CYCR11 JSCR11 SAPI11 IFRI11 CDII11 BODB11 KDIF11 CPTI11 DIVS11 JURO11 IFRA11 KNCA11 RZAG11 RZAK11 FGAA11 EGAF11 IAAG11 CRAA11 RURA11 SNAG11; do
        echo "mortgage $t"
    done
} | xargs -P $PARALLEL -L 1 bash -c 'process_ticker "$@"' _

echo "" >&2
echo "=== Completed at $(date) ===" >&2
echo "--- Summary ---" >&2
echo "Total calls: $(tail -n +2 "$RESULTS_FILE" | wc -l)" >&2
echo "Successful (200): $(grep -c ',200$' "$RESULTS_FILE")" >&2
echo "Tickers with remaining > 0 on last pass:" >&2
tail -n +2 "$RESULTS_FILE" | awk -F, '{key=$1","$2; data[key]=$0} END {for (k in data) {split(data[k],a,","); if (a[8]+0>0) print a[1]" ("a[2]") remaining="a[8]}}' >&2
echo "Results saved to $RESULTS_FILE" >&2
