#!/usr/bin/env bash
# h-config.sh — вызывается перед каждым запуском майнера, генерирует epic-miner.toml.
# Переменные $CUSTOM_URL, $CUSTOM_TEMPLATE, $CUSTOM_PASS, $CUSTOM_USER_CONFIG, $CUSTOM_ALGO
# уже в скоупе (заданы в Flight Sheet и подставлены Hive перед запуском этого скрипта).

. /hive/miners/custom/epic-miner/h-manifest.conf

mkdir -p "$(dirname "$CUSTOM_CONFIG_FILENAME")"
mkdir -p "$(dirname "$CUSTOM_LOG_BASENAME")"

# Поле "algo" во флайтшите. Если не задано или не распознано — используем Cuckoo
# (CuckAToo31+), как и весь этот конфиг изначально задумывался.
case "${CUSTOM_ALGO,,}" in
  progpow) EPIC_ALGO="ProgPow" ;;
  randomx) EPIC_ALGO="RandomX" ;;
  cuckoo|cuckatoo|*) EPIC_ALGO="Cuckoo" ;;
esac

cat > "$CUSTOM_CONFIG_FILENAME" <<EOF
[logging]
log_to_stdout = true
stdout_log_level = "Info"
log_to_file = false
file_log_level = "Info"
log_file_path = "./epic-miner.log"
log_file_append = true

[mining]
algorithm = "${EPIC_ALGO}"
run_tui = false

stratum_server_addr = "${CUSTOM_URL}"
stratum_server_login = "${CUSTOM_TEMPLATE}"
stratum_server_password = "${CUSTOM_PASS:-x}"
stratum_server_tls_enabled = false

miner_plugin_dir = "./plugins"

EOF

# CUSTOM_USER_CONFIG — поле "Extra config arguments" во флайтшите.
# Сюда вставляется RAW TOML-блок [[mining.gpu_config]] (для ProgPoW) или
# [[mining.miner_plugin_config]] (для Cuckatoo) — то есть ровно то, что
# мы собирали в предыдущих конфигах для GPU/CPU. Если поле пустое —
# подставляется безопасный дефолт: cuckatoo_mean_cpu_avx2_31, 4 потока,
# чтобы майнер хотя бы стартовал, а не падал на пустом конфиге.
if [[ -n "$CUSTOM_USER_CONFIG" ]]; then
  echo "$CUSTOM_USER_CONFIG" >> "$CUSTOM_CONFIG_FILENAME"
else
  cat >> "$CUSTOM_CONFIG_FILENAME" <<'EOF'
[[mining.miner_plugin_config]]
plugin_name = "cuckatoo_mean_cpu_avx2_31"
[mining.miner_plugin_config.parameters]
nthreads = 4
EOF
fi
