#!/usr/bin/env bash
# h-stats.sh — вызывается из agent, должен установить переменные $khs и $stats.
#
# ВАЖНО, честно о неопределённости: epic-miner унаследован от той же родословной
# кода, что и оригинальный grin-miner (общий cuckoo-miner core, тот же slog-логгер).
# В grin-miner строка с производительностью выглядит так:
#   "... INFO Mining: Cuck(at)oo at 12.34 gps (graphs per second)"
# Это совпадение очень вероятно, но НЕ подтверждено напрямую для epic-miner —
# проверьте реальный лог-файл после первого запуска (tail -f <лог>.log) и,
# если строка отличается, подправьте grep/sed ниже под фактический формат.
#
# Также: Cuckoo-алгоритмы измеряются в gps (graphs per second), а не в хешах.
# Hive ожидает hs/khs/mhs — отдельной единицы "gps" в стандарте нет, поэтому
# число будет отображаться в дашборде Hive как если бы это были khs
# (на сам майнинг/пул это не влияет, влияет только на то, что вы увидите в UI).

LOG_FILE="${CUSTOM_LOG_BASENAME}.log"

GPS=$(tail -n 200 "$LOG_FILE" 2>/dev/null \
  | grep -oP 'Cuck\(at\)oo at \K[0-9]+\.?[0-9]*' \
  | tail -n 1)

GPS=${GPS:-0}
khs=$GPS

ACCEPTED=$(grep -oP 'Accepted.*?\K[0-9]+' "$LOG_FILE" 2>/dev/null | tail -n 1)
REJECTED=$(grep -oP 'Rejected.*?\K[0-9]+' "$LOG_FILE" 2>/dev/null | tail -n 1)
ACCEPTED=${ACCEPTED:-0}
REJECTED=${REJECTED:-0}

stats=$(jq -n \
  --argjson hs "[$khs]" \
  --arg ver "$CUSTOM_VERSION" \
  --argjson ar "[$ACCEPTED, $REJECTED]" \
  '{
    hs: $hs,
    hs_units: "khs",
    ver: $ver,
    ar: $ar,
    algo: "cuckatoo"
  }')
