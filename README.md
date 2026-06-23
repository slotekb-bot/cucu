# epic-miner — custom-майнер для HiveOS

## Что уже готово в этой папке
- `h-manifest.conf` — метаданные для Hive
- `h-config.sh` — генерирует `epic-miner.toml` перед каждым запуском из полей флайтшита
- `h-run.sh` — запускает бинарник
- `h-stats.sh` — отдаёт хешрейт/статистику в Hive (формат gps, см. комментарии в файле — это лучшее предположение по аналогии с grin-miner, проверьте на реальном логе)

## Что нужно добавить самостоятельно перед упаковкой

1. **Бинарник `epic-miner`.** Соберите его одним из скриптов, что мы готовили ранее
   (`setup-epic-miner-rtx3080.sh` для CUDA/Cuckatoo на GPU, или
   `setup-epic-miner-cpu-avx2.sh` для CPU AVX2). Важно: собирать нужно либо прямо
   на самом риге (по SSH, пока он не запущен в майнинг-режиме), либо на машине
   с такой же версией Ubuntu/glibc, как у HiveOS — иначе бинарник может не запуститься
   из-за несовпадения версий системных библиотек.
   Скопируйте `target/release/epic-miner` в эту папку.

2. **Плагины.** Из `target/release/` (или `target/release/plugins/`, в зависимости от
   версии сборки) скопируйте все файлы `*.cuckooplugin` в подпапку `plugins/` рядом
   с бинарником — `h-config.sh` ожидает `miner_plugin_dir = "./plugins"`.

Итоговая структура папки перед упаковкой должна быть:

```
epic-miner/
├── h-manifest.conf
├── h-config.sh
├── h-run.sh
├── h-stats.sh
├── epic-miner          <- бинарник, добавляете сами
└── plugins/             <- *.cuckooplugin файлы, добавляете сами
```

## Упаковка

```bash
chmod +x h-run.sh h-config.sh h-stats.sh epic-miner
cd ..
tar -zcvf epic-miner-1.4.0.tar.gz epic-miner/
```

Выложите получившийся `.tar.gz` куда-нибудь с прямой ссылкой (свой сервер,
GitHub Releases вашего форка и т.п.) — HiveOS скачивает пакет по URL, который
вы укажете при добавлении custom-майнера.

## Установка во Flight Sheet HiveOS

1. Flight Sheet → Miner: **Custom**.
2. **Miner name**: `epic-miner`.
3. **Installation URL**: ссылка на ваш `epic-miner-1.4.0.tar.gz`.
4. **Hash algorithm**: можно указать `cuckatoo` (произвольное имя для дашборда).
5. **Pool URL**: адрес пула Epic Cash (попадёт в `$CUSTOM_URL`).
6. **Wallet and worker template**: например `%WAL%.%WORKER_NAME%` (попадёт в `$CUSTOM_TEMPLATE`,
   станет `stratum_server_login`).
7. **Pass**: пароль воркера (`$CUSTOM_PASS`).
8. **Extra config arguments**: вставьте сюда RAW TOML-блок плагина — то есть ровно
   то, что мы собирали раньше. Например, для CPU AVX2 56 потоков:

   ```
   [[mining.miner_plugin_config]]
   plugin_name = "cuckatoo_mean_cpu_avx2_31"
   [mining.miner_plugin_config.parameters]
   nthreads = 56
   ```

   Или для GPU CUDA на RTX 3080:

   ```
   [[mining.miner_plugin_config]]
   plugin_name = "cuckatoo_mean_cuda_rtx_31"
   [mining.miner_plugin_config.parameters]
   device = 0
   expand = 3
   cpuload = 1
   ntrims = 176
   genablocks = 4096
   genatpb = 128
   genbtpb = 128
   trimtpb = 512
   tailtpb = 1024
   recoverblocks = 1024
   recovertpb = 1024
   ```

   Если поле оставить пустым, `h-config.sh` подставит безопасный дефолт
   (`cuckatoo_mean_cpu_avx2_31`, 4 потока) — чтобы майнер хотя бы стартовал,
   а не падал на пустом конфиге.

## Проверка после первого запуска

- Откройте лог: `tail -f /var/log/miner/epic-miner/epic-miner.log` на риге.
- Убедитесь, что строка с производительностью реально содержит `Cuck(at)oo at X gps` —
  если формат другой, поправьте `grep -oP` в `h-stats.sh` под фактический текст,
  иначе Hive будет показывать хешрейт 0 даже при исправно работающем майнере.
- Проверьте, что пул реально принимает Cuckatoo для Epic Cash (не все пулы это
  поддерживают — см. https://miningpoolstats.stream/epiccash-cuckoo).
