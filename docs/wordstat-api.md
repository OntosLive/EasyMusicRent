# Wordstat API collector

Автоматический сбор поисковых запросов для ONTOS.RENT.

## Что уже сделано

- `data/seeds.csv` — семена, по которым опрашивается Wordstat.
- `tools/wordstat_collect.py` — сборщик Wordstat GetTop.
- `.github/workflows/wordstat-collect.yml` — ручной и еженедельный запуск через GitHub Actions.
- `data/wordstat_raw.csv` — полный сырой ответ после первого запуска.
- `data/query_candidates.csv` — дедуплицированные кандидаты для смысловой фильтрации.
- `data/queries.csv` остаётся каноническим отобранным backlog и автоматически не перезаписывается.

## География

Сейчас разрешены:

- Москва — регион Wordstat `213`
- Казань — регион Wordstat `43`, пока только цифровые пианино

## Как получить доступ к API

Для Wordstat в Yandex Search API нужен:

1. сервисный аккаунт;
2. роль `search-api.webSearch.user`;
3. API-ключ с областью действия `yc.search-api.execute`;
4. ID каталога Yandex Cloud.

В репозитории нужно добавить два GitHub Actions secret:

- `YANDEX_WORDSTAT_API_KEY`
- `YANDEX_FOLDER_ID`

После этого workflow **Collect Wordstat queries** можно запускать вручную через GitHub Actions.

## Как работает сбор

Для каждого включённого семени из `data/seeds.csv` выполняется запрос к:

`POST https://searchapi.api.cloud.yandex.net/v2/wordstat/topRequests`

На одно семя запрашивается до 2000 фраз.

Сохраняются два типа результатов:

- `result` — запросы, содержащие указанную фразу;
- `association` — похожие запросы.

Сборщик ничего автоматически не публикует и не переносит в `data/queries.csv`.
Это сделано специально: сначала сырьё, потом различение, потом публикация.

## Рабочий контур

**семена → Wordstat → raw → candidates → смысловая фильтрация → queries.csv → страницы**

Главный принцип:

> API собирает поле. Компилятор решает, что из него имеет смысл.
