#!/usr/bin/env bash
# h-run.sh — запускает майнер. Working dir = /hive/miners/custom/epic-miner

. /hive/miners/custom/epic-miner/h-manifest.conf

cd /hive/miners/custom/epic-miner || exit 1

# Если в пакет были положены CUDA-плагины — может потребоваться путь к CUDA-либам.
# Раскомментируйте, если бинарник собран с CUDA и ругается на отсутствие .so:
# export LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"

# epic-miner ищет epic-miner.toml в текущей директории (генерируется h-config.sh).
exec ./epic-miner >> "${CUSTOM_LOG_BASENAME}.log" 2>&1
