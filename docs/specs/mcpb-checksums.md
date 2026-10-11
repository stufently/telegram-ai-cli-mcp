# Веха: SHA256-суммы для `.mcpb` в релизе — telegram-ai-cli-mcp

- Репозиторий `telegram-ai-cli-mcp` (`~/github/telegram-ai-cli-mcp`), дата 11.10.2026.
- BASE_SHA: `8516834347e68bd19ea5615fd9738f2e917655a6` («Release 0.1.1») — `origin/main` после `git fetch`, коммит, с которого снят
  клон. Поверх него в клоне ОДИН коммит постановщика со спекой и двумя пробниками; левая
  граница диффа ревью и `base_sha` отчёта — именно BASE_SHA.
- Исполнитель: `auto` (координатор выбирает Grok или Spark по квоте). Мутации по пробнику
  и скрипту гоняет ПРОТИВОПОЛОЖНЫЙ исполнитель отдельным прогоном.
- Критериев: 6. Контекст: `~/gitlab/9qw/tg-claude-userbot/TASKS.md`, пункт «Доверие как
  условие установки» (checksums для артефактов).

## Где работать

Одноразовый клон `/home/deploy/exec-clones/mcpb-sha-tg-20261011`, ветка `mcpb-checksums` (уже создана и выбрана, на ней коммит
со спекой). Живое дерево `~/github/telegram-ai-cli-mcp` и соседние клоны не трогать.

**`git push` запрещён — в любой remote, включая `origin`.** Работу заберёт постановщик через
`git fetch` из клона. Теги, релизы, `gh release …` с записью, `gh workflow run` — запрещены:
веха меняет только файлы. Коммиты локальные, `git add` по именам файлов, никогда `-A`.
Артефакты ревью — в `review/` в корне клона (untracked, не коммитить).

Что лежит в клоне от постановщика (закоммичено, менять запрещено):

| Файл | sha256 |
|---|---|
| `docs/specs/mcpb-checksums.md` | эта спека |
| `docs/specs/mcpb-checksums-probe.sh` | `9074206f51684ea9f10ceb55b38133df5d0f0bb7083e9b5c718f378639035596` |
| `docs/specs/mcpb-checksums-wiring.py` | `3fe4e1bfc7fea575553eb24865031501a4e351f51f3e7f3d8d3eb700597d146b` |

Зависимости ставить не нужно: критериям нужны `bash`, `sha256sum`, `python3` (stdlib) на
хосте и образ `rhysd/actionlint:1.7.12` (уже есть локально, внутри — `shellcheck` 0.11.0).
Docker — только с `-u 1002:1002`.

## Задача и почему

Бандлы `.mcpb` (Desktop Extension для Claude Desktop) выкладываются в GitHub Release без
контрольных сумм. Пользователь, скачавший `.mcpb`, не может проверить, что получил ровно то,
что собрал CI. Для MCP-сервера, которому отдают API-токены, это условие установки. Эталон
флота — zabbix-ai-cli-mcp: файл `checksums.txt` в релизе, формат `sha256sum`
(`<64 hex><два пробела><имя файла>`). Формат и имя файла одинаковые для всех семи репо.

Что сделать по сути: release-workflow после сборки считает sha256 для ВСЕХ `.mcpb` и
прикладывает `checksums.txt` к релизу; README говорит, как проверить.

**Что при этом может сломаться и обязано остаться целым:** существующие шаги workflow
(создание релиза, загрузка `.mcpb`, проверки тега) и сборка `scripts/build-mcpb.sh`.

## Что проверено вживую, а что предположение

Проверено 11.10.2026 командами `git pull`, `gh release view --json assets`,
`gh release download`, чтением workflow и `scripts/build-mcpb.sh`.

- Релиз v0.1.0: ассеты — `SHA256SUMS.txt`, `telegram-ai-cli-mcp-0.1.0.mcpb`, wheel, sdist.
  `SHA256SUMS.txt` (скачан) содержит ДВЕ строки — wheel и sdist; строки `.mcpb` нет.
- В момент постановки идёт релиз 0.1.1 (прогон Release на теге v0.1.1 не завершён). Клон
  снят строго с `origin/main` после `git fetch` (= коммит «Release 0.1.1»); тег, релиз и
  PyPI этой вехой не трогаются.
- `release.yml`: job `build` пишет `checksums/SHA256SUMS.txt` и кладёт его артефактом
  `checksums`; job `build-mcpb` кладёт `dist-mcpb/*.mcpb` артефактом `mcpb`; job
  `github-release` (`needs: publish-pypi, build-mcpb`) БЕЗ checkout скачивает `dist` и
  `checksums` в `dist/`, `mcpb` в `mcpb-asset/` и создаёт черновик релиза
  `softprops/action-gh-release` с `files: dist/* mcpb-asset/*`.
- Кроме `release.yml`, `SHA256SUMS` нигде в репо не упоминается (grep без `.git`).
- README: абзац про `.mcpb` — ~строка 309.
- `actionlint` 1.7.12 (последний релиз rhysd/actionlint на 11.10.2026) на HEAD клона: rc=0 —
  исходное состояние зелёное.
- Пробник `mcpb-checksums-probe.sh` (v2, 11.10.2026: усилен после мутационного прогона на zabbix — порядок и полнота чужих строк, последняя строка без LF, порядок `LC_ALL=C`, провал внутреннего `sha256sum -c`, `\`-строки) прогнан постановщиком: на эталонной реализации
  `PROBE PASSED`, rc=0; на семи уклончивых реализациях (no-op; полные пути вместо имён;
  перезапись без сохранения чужих строк; дописывание без удаления старых строк `.mcpb`;
  суммы всех файлов каталога; rc=0 на пустом каталоге; sha1 вместо sha256) — rc=1 каждый.
  На чистом клоне (скрипта ещё нет) — rc=1, `FAIL: no …/scripts/mcpb-checksums.sh`.
- **Предположение:** `gh release download/upload` в Actions работают с `GITHUB_TOKEN` при
  `contents: write` так же, как уже работающая загрузка `.mcpb` в этом же job. Живым тегом
  это не проверяется — проверит первый настоящий релиз после мержа (за координатором).

## Что сделать

### 1. `scripts/mcpb-checksums.sh` (новый файл)

Интерфейс ровно такой (его проверяет пробник AC-001):

```
bash scripts/mcpb-checksums.sh DIR SUMS
```

- `DIR` — каталог с бандлами; учитываются только файлы `DIR/*.mcpb` (без рекурсии;
  `notes.txt`, `x.mcpb.bak` и сам `checksums.txt` — не бандлы).
- `SUMS` — путь к файлу сумм; может лежать внутри `DIR` или вне его; может уже
  существовать; путь может быть относительным к текущему каталогу.
- Нет ни одного `DIR/*.mcpb` → сообщение в stderr, код возврата ≠ 0, `SUMS` не создаётся
  и не меняется.
- Иначе итоговый `SUMS` = все строки прежнего `SUMS`, имя файла в которых НЕ оканчивается на
  `.mcpb`, в исходном порядке и байт в байт, затем по одной строке на каждый бандл,
  отсортированные по имени (`LC_ALL=C`), в текстовом формате `sha256sum`:
  `<64 строчных hex><два пробела><имя файла без каталога>`. Повторный запуск даёт
  побайтно тот же файл (старые строки `.mcpb` заменяются, а не дублируются).
- Строкой `.mcpb` считается и строка GNU-формата с ведущей обратной косой
  (`\<64 hex>  <имя>`, так `sha256sum` пишет имя с `\` или переводом строки): она тоже
  заменяется, а не дублируется. Строки goreleaser сохраняются в исходном порядке байт
  в байт, включая последнюю строку без завершающего перевода строки.
- Внутренняя проверка `sha256sum -c` провалилась → rc≠0, и прежний `SUMS` остаётся
  нетронутым (сначала проверка временного файла, потом `mv`).
- После записи скрипт сам проверяет строки `.mcpb` через `sha256sum -c` из `DIR` и при
  расхождении выходит с ≠ 0.
- Запись атомарная (временный файл рядом + `mv`), stdin не читать, `set -euo pipefail`,
  чисто под `shellcheck`.

### 2. Workflow `.github/workflows/release.yml`

У telegram в релизе УЖЕ есть файл сумм, но он называется `SHA256SUMS.txt` и покрывает
только wheel и sdist: его пишет job `build` из `dist/`, а `.mcpb` собирает отдельный job
`build-mcpb` в `mcpb-asset/` (проверено на v0.1.0, см. ниже). Формат проекта сводится к
zabbix: один файл `checksums.txt` в формате `sha256sum`.

В `.github/workflows/release.yml`:

1. Job `build`, шаг `Generate checksums`: переименовать выходной файл
   `checksums/SHA256SUMS.txt` → `checksums/checksums.txt` (команда та же:
   `(cd dist && sha256sum -- *) > checksums/checksums.txt` и `cat` его же). Комментарий
   над шагом про отдельный каталог оставить.
2. Job `github-release`: у него сейчас НЕТ checkout, а скрипт лежит в репо. Первым шагом
   job добавить `actions/checkout` тем же пином, что в остальных job
   (`actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`) с
   `persist-credentials: false`. Именно ПЕРВЫМ: checkout чистит рабочий каталог и снёс бы
   уже скачанные `dist/` и `mcpb-asset/`.
3. Там же, после трёх шагов `download-artifact` и ДО `softprops/action-gh-release`,
   добавить шаг:

   ```yaml
      - name: Add the mcpb bundle to the checksums
        run: bash scripts/mcpb-checksums.sh mcpb-asset dist/checksums.txt
   ```

   `dist/*` уже входит в `files:` релиза, поэтому `checksums.txt` с суммами wheel, sdist
   и `.mcpb` попадёт в черновик релиза без правки `files:`.

В `.github/workflows/` после работы не должно остаться ни одного упоминания
`SHA256SUMS`. Job `publish-pypi`, `environment: pypi`, имя файла `release.yml`, пины
остальных actions и шаги проверки версии/архивов не трогать: от них зависит Trusted
Publishing на PyPI.

### 3. README.md

рядом с абзацем про установку `.mcpb` (~строка 309) добавить короткий абзац (по-английски, как весь README) о том, что в
релизе лежит `checksums.txt` с SHA256 каждого `.mcpb`, и строку проверки ровно с такой
подстрокой (её ищет AC-004; `.mcpb` должен стоять в той же строке, например в
комментарии):

```bash
sha256sum -c --ignore-missing checksums.txt   # run next to the downloaded .mcpb
```

На macOS допустимо добавить вариант `shasum -a 256 -c`, но строку выше — оставить.

### 4. CHANGELOG.md

Одна запись в верхнюю незакрытую секцию (`Unreleased`/`[Unreleased]`; в репо без такой
секции — новая секция в принятом в файле формате, датой 11.10.2026): релиз теперь прикладывает
`checksums.txt` с SHA256 для `.mcpb`.

## Не трогать

- `scripts/build-mcpb.sh`, `mcpb/`, манифесты, исходный код, тесты, `Dockerfile*`,
  `.goreleaser.yaml`, все остальные workflow, кроме `.github/workflows/release.yml`.
- В `.github/workflows/release.yml` — только то, что перечислено выше; пины actions, триггеры, `permissions`,
  `environment` не менять.
- Файлы постановщика в `docs/specs/` (спека и два пробника) — их sha256 вшиты в критерии.
- Полный список разрешённых к изменению файлов — в AC-005; всё прочее — нарушение вехи.

## Критерии приёмки

Команды запускаются из корня клона.

- **AC-001.** Скрипт сумм на имитации каталога релиза с фиктивными бандлами: суммы верны,
  проверка sha256sum -c проходит, чужие строки сохранены, повтор идемпотентен, пустой каталог —
  ошибка. Пробник постановщика, его sha256 вшит:
  `bash -c 'echo "9074206f51684ea9f10ceb55b38133df5d0f0bb7083e9b5c718f378639035596  docs/specs/mcpb-checksums-probe.sh" | sha256sum -c - && bash docs/specs/mcpb-checksums-probe.sh scripts/mcpb-checksums.sh'`
- **AC-002.** Workflow вызывает скрипт после сборки и прикладывает файл к релизу (порядок
  шагов проверяется, строки-комментарии не считаются):
  `bash -c '! grep -rq SHA256SUMS .github/workflows && echo "3fe4e1bfc7fea575553eb24865031501a4e351f51f3e7f3d8d3eb700597d146b  docs/specs/mcpb-checksums-wiring.py" | sha256sum -c - && python3 docs/specs/mcpb-checksums-wiring.py .github/workflows/release.yml "checksums/checksums.txt" "github-release:" "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1" "name: dist" "name: mcpb" "bash scripts/mcpb-checksums.sh mcpb-asset dist/checksums.txt" "softprops/action-gh-release@"'`
- **AC-003.** `actionlint` 1.7.12 в Docker зелёный по всем workflow, `shellcheck` зелёный по
  новому скрипту:
  `bash -c 'docker run --rm -u 1002:1002 -v "$PWD":/repo -w /repo rhysd/actionlint:1.7.12 && docker run --rm -u 1002:1002 -v "$PWD":/repo -w /repo --entrypoint shellcheck rhysd/actionlint:1.7.12 scripts/mcpb-checksums.sh'`
- **AC-004.** README учит проверять бандлы командой sha256sum -c:
  `bash -c 'grep -F "sha256sum -c --ignore-missing checksums.txt" README.md | grep -qF .mcpb'`
- **AC-005.** Других изменений нет: от BASE_SHA изменены только разрешённые файлы, и
  обязательные среди них есть:
  `bash -c 'c="$(git diff --name-only 8516834347e68bd19ea5615fd9738f2e917655a6..HEAD)" && test -z "$(printf "%s\n" "$c" | grep -vxF -e .github/workflows/release.yml -e README.md -e CHANGELOG.md -e scripts/mcpb-checksums.sh -e docs/specs/mcpb-checksums.md -e docs/specs/mcpb-checksums-probe.sh -e docs/specs/mcpb-checksums-wiring.py)" && printf "%s\n" "$c" | grep -qxF .github/workflows/release.yml && printf "%s\n" "$c" | grep -qxF README.md && printf "%s\n" "$c" | grep -qxF CHANGELOG.md && printf "%s\n" "$c" | grep -qxF scripts/mcpb-checksums.sh'`
- **AC-006.** Дерево чистое, работа закоммичена:
  `bash -c 'test -z "$(git status --porcelain -- . ":(exclude)report.json" ":(exclude)report-blocked.md" ":(exclude)review/")"'`

Ожидание на чистом клоне (проверено постановщиком): AC-001, AC-002, AC-004, AC-005 — красные
(нет скрипта / нет шага / нет строки / нет изменений), AC-003 — красный только на
`shellcheck` (файла нет), AC-006 — зелёный.

## Контракт отчёта

`report.json` в КОРНЕ клона, untracked, схема v2 (её проверяет `accept_run.py` до запуска
критериев):

```json
{"schema_version": 2,
 "policy_id": "cross-review-v1",
 "handoff_status": "ready",
 "executor": {"backend": "grok|spark|codex", "model": "<точная модель>"},
 "spec_sha256": "<sha256 файла docs/specs/mcpb-checksums.md>",
 "base_sha": "8516834347e68bd19ea5615fd9738f2e917655a6",
 "reviewed_sha": "<коммит, отданный на ревью>",
 "final_sha": "<HEAD клона после единственного захода фиксов>",
 "review": {"initial_receipts": [], "verification_receipts": [], "resolutions": []},
 "criteria": [{"id": "AC-001", "status": "pass|fail|blocked",
               "command": "<команда ИЗ ЭТОЙ СПЕКИ, посимвольно>", "rc": 0, "note": "…"}]}
```

Записей в `criteria` ровно 6, AC-001…AC-006. Поле — `reviewed_sha`, не `review_sha`; три
sha — 40 строчных hex; `final_sha` = HEAD клона; `base_sha → reviewed_sha → final_sha` —
предки друг друга. `command` совпадает с командой критерия ДОСЛОВНО. Квитанции ревью
перечисляются в `review.initial_receipts` / `review.verification_receipts`. Перед сдачей:
`python3 /home/deploy/.claude/skills/executor-milestone/scripts/accept_run.py /home/deploy/exec-clones/mcpb-sha-tg-20261011 --spec /home/deploy/exec-clones/mcpb-sha-tg-20261011/docs/specs/mcpb-checksums.md --dry-run`
обязан дать код 2 (`validation_only`).

`blocked` — штатный исход, когда среда не даёт выполнить критерий: `"rc": null`, в `command`
команда-улика, в `note` дословная ошибка. Обходить несовместимость (`--no-deps`, `|| true`,
`set +e` в команде критерия, `sudo`, `git push`) ЗАПРЕЩЕНО.

## Контракт на невыполнимое

Противоречие в спеке, невыполнимый критерий, факт, опровергающий раздел «Что проверено» (в
том числе: workflow устроен не так, как описано; `actionlint` красный на нетронутом дереве;
пробник требует поведения, противоречащего интерфейсу из раздела 1) — **остановись и
доложи**: `report-blocked.md` в корне клона с дословной командой, выводом и опровергнутым
утверждением. Править пробники и спеку, ослаблять критерии — запрещено.

## Автономное перекрёстное ревью

Действует `cross-review-v1` целиком: `/home/deploy/.claude/skills/executor-milestone/docs/cross-review-v1.md`. Пара ревьюеров по
backend исполнителя: Codex или Spark → `agy` + `grok`; Grok → `codex` + `agy`. Сам себя не ревьюит никто.

1. Реализация → своя проверка всех AC → коммит: это REVIEW_SHA.
2. Оба ревью параллельно на `BASE_SHA..REVIEW_SHA`, каждое только читает:
   `bash /home/deploy/.claude/skills/executor-milestone/scripts/review_run.sh initial <ревьюер> --clone /home/deploy/exec-clones/mcpb-sha-tg-20261011 --base 8516834347e68bd19ea5615fd9738f2e917655a6 --range 8516834347e68bd19ea5615fd9738f2e917655a6..<REVIEW_SHA> --context "mcpb checksums milestone, read-only"`
   run_id = `mcpb-sha-tg-20261011-8516834347e6`; квитанции пишет только `review_run.sh`.
3. Дождаться ОБОИХ, свести находки, по каждой `fixed` / `disproved` / `needs_owner`.
   Один заход исправлений → FINAL_SHA. Затем те же два ревьюера ОДИН раз на
   `REVIEW_SHA..FINAL_SHA` (фаза `verification`, тот же `--base 8516834347e68bd19ea5615fd9738f2e917655a6`); если код после
   ревью не менялся и споров нет — завершающая проверка пропускается. Второй заход
   исправлений запрещён.
4. Обрезанный вход, оборванный ответ или нет маркера `ВЕРДИКТ:` — `incomplete`, а не «находок
   нет». Один технический повтор незавершённого вызова допустим; исчерпанная квота —
   `blocked`. Эксперименты с процессами, сигналами и tmux — только в Docker с фейками.

## Стыки с соседними вехами

Шесть таких же вех идут параллельно в остальных MCP-репо флота с тем же интерфейсом
скрипта и тем же пробником; интерфейс не расширять, чтобы скрипт оставался одинаковым во
всех семи репо. Подпись артефактов (cosign/minisign) и таблица протестированных клиентов —
отдельные будущие вехи, сюда не входят.
