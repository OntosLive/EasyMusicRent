# Rider / Legendary / Professional Model Core — контрольная точка

Дата: 5 октября 2026.

## Задача

Исчерпывающе исследовать и внедрить в ONTOS.RENT реальные прокатные, технически-райдерные, профессиональные и легендарные модели по всему фонду. При необходимости расширить предметные категории.

Исходная точка перед этим проходом: 848 тем.

## Архитектурный результат

Модельный слой больше не определяется полнотой текущего каталога производителя. Действует отдельный канон `docs/rider-model-canon.md`.

Приоритет:

1. Rider Core.
2. Legendary Core.
3. Current Pro.
4. Specialist Model.

Введены пять типов профессиональной сущности:

- Exact Model;
- Series + Configuration;
- Legendary Lineage;
- System / Rig;
- Maker / School / Specimen.

Последний тип принципиально важен для акустических смычковых, исторических и части традиционных инструментов: там промышленный SKU не должен насильно подменять мастера, школу, размер, строй и конкретный экземпляр.

## Новое верхнее семейство

Добавлено тринадцатое L1-семейство:

**Усилители и бэклайн** — `/usiliteli-backline/`.

Подразделы:

- гитарные усилители;
- басовые усилители;
- гитарные кабинеты;
- басовые кабинеты;
- акустические усилители;
- Leslie / rotary-системы.

Семейство связано напрямую с корнем фонда. Документация проекта обновлена с 12 до 13 семейств.

## Пакеты этого прохода

### zz29 — усилители и backline

Категории и модели:

- Fender ’65 Twin Reverb;
- Fender ’65 Deluxe Reverb;
- Vox AC30C2;
- Marshall JCM800 2203;
- Marshall 1960A;
- Roland JC-120;
- EVH 5150III 100S;
- Orange Rockerverb 50 MKIII;
- Mesa Dual Rectifier;
- Ampeg SVT-CL;
- Ampeg SVT-810E;
- Aguilar Tone Hammer 700;
- Gallien-Krueger 800RB;
- Markbass Little Mark III;
- Fishman Loudbox Artist;
- Leslie 122.

Отдельно уже существует системная страница Hammond B3 + Leslie 122.

### zz30 — concert grand standards

- Steinway D-274;
- Steinway B-211;
- Yamaha CFX;
- Bösendorfer 280VC;
- Fazioli F278.

### zz31 — professional wind standards

- Yamaha YFL-677;
- Yamaha YAS-62 — углубление существующей страницы;
- Yamaha YTS-62 — углубление существующей страницы;
- Lorée Royal;
- Marigaux 901;
- Fox 601;
- Yamaha Xeno YTR-8335RS;
- Bach 42BO;
- Alexander 103;
- Besson Prestige 2052.

Реестр обнаружил, что YAS-62 и YTS-62 уже существовали в `99y-wind-model-comparisons.json`. Новые адреса не создавались: rental/professional-исследование встроено в существующие сущности через `mode=enrich`, при этом ранее утверждённые search/editorial titles сохранены.

### zz32 — legendary keyboards

Новая внутренняя ветвь `legendarnye-sintezatory` плюс:

- Rhodes Mark I Stage 73;
- Wurlitzer 200A;
- Hohner Clavinet E7;
- Yamaha DX7;
- Sequential Prophet-5;
- Roland JUPITER-8;
- Roland D-50;
- Korg M1.

В эту же сетку входят ранее созданные Minimoog Model D и Roland JUNO-106.

### zz33 — drum and harp rider standards

- Yamaha Absolute Hybrid Maple;
- Ludwig Classic Maple;
- Tama Starclassic Performer Birch/Bubinga;
- Pearl Masters Custom;
- Ludwig Supraphonic LM400;
- Lyon & Healy Style 30;
- Lyon & Healy Chicago CG Extended.

### zz34 — accordion / bayan professional core

- Hohner Gola;
- Pigini Super Bayan Sirius;
- Pigini Sirius Kyma.

Ранее добавлен Scandalli Super VI.

### zz35 — orchestral percussion / cymbal standards

- Adams Professional Gen II timpani;
- Yamaha YM-6100 marimba;
- Paiste 2002;
- Sabian HHX;
- Zildjian K Series.

Ранее добавлены Zildjian A Series, Ludwig Black Beauty и Musser M55.

### zz36 — electronic / plucked legendary models

- Roland TR-808;
- Roland TR-909;
- Gibson F-5 Master Model;
- Deering Sierra;
- Moog Etherwave.

### zz37 — Current Pro workstations

- Yamaha MONTAGE M8x;
- Roland FANTOM 8 EX;
- Korg NAUTILUS 88 AT.

Они добавлены после отдельной проверки текущих rental inventories, чтобы Legendary Core не вытеснял современный профессиональный backline.

## Более ранний Rider Core этого же направления

До zz29 в модели уже были внедрены, среди прочего:

- Nord Stage 3 88;
- Yamaha CP88;
- Roland RD-2000 EX;
- Korg Kronos 2 88;
- Yamaha Motif XF8;
- Fender American Professional II Stratocaster / Telecaster / Precision Bass / Jazz Bass;
- Gibson Les Paul Standard 60s / ES-335 / J-45;
- Martin D-28;
- Music Man StingRay Special;
- DW Collector’s Series;
- Yamaha Recording Custom;
- Gretsch USA Custom;
- Buffet R13;
- Selmer Mark VI tenor;
- Bach Stradivarius 180S37;
- Conn 8D;
- Lyon & Healy Style 23;
- Scandalli Super VI;
- Minimoog Model D;
- Roland JUNO-106;
- Ludwig Black Beauty;
- Musser M55;
- Zildjian A Series.

## Что значит «исчерпывающе»

Исчерпывание не равно копированию всех SKU всех производителей.

Слой считается содержательно закрытым сверху вниз, когда система умеет различать:

- устойчивые названия из технических райдеров;
- реально повторяющиеся позиции rental/backline;
- исторические модели, продолжающие жить железом;
- актуальные профессиональные replacement / current standards;
- серии, которым обязательно требуется конфигурация;
- rigs, существующие только как связка нескольких узлов;
- категории, где промышленная модель не является главным профессиональным идентификатором.

## Источники и доказательность

Для новых страниц использовались два типа оснований:

1. первичные страницы производителей — для конструкции, версии, истории и технических различий;
2. реальные rental/backline inventories — для утверждения, что модель живёт как отдельная прокатная или райдерная единица.

Публичная страница модели не означает наличия конкретного экземпляра ONTOS.RENT. Для rare / vintage / specialist моделей доступность подтверждается отдельно.

## Защитные проверки, сработавшие в этом проходе

Автоматические проверки остановили публикацию в двух важных местах:

1. обнаружили повторные декларации YAS-62 и YTS-62;
2. обнаружили недостижимость нового 13-го семейства из корня;
3. редакционный title Marigaux 901 содержал коммерческое слово и был исправлен;
4. существующие утверждённые заголовки YAS/YTS не позволено было тихо заменить новым слоем.

После исправлений тесты проходят без отключения или ослабления этих защит.

## Проверенное состояние

На содержательном коммите `f65fe53f6b91f1ecfe78f29123bc00b7ac1364f7`:

- 916 действующих тем;
- 1832 страницы предметных пар;
- 8 страниц условий;
- 1840 обычных документов проверено;
- 48 перенаправлений;
- 916 адресов sitemap;
- 1 вариант контактного блока;
- 0 недостижимых страниц;
- 0 ошибок;
- 51 / 51 тестов успешно.

Canon audit: https://github.com/OntosLive/EasyMusicRent/actions/runs/37250549203 — success.

Build / validation / deploy для этого же коммита проверяется отдельным workflow и должен фиксироваться отдельно от тестового аудита.

## Следующее развитие

Следующие проходы не должны снова начинать с «какие модели ещё придумать».

Рабочий порядок:

1. измерять покрытие внутри каждого семейства;
2. находить реальные rider / rental gaps;
3. дополнять Current Pro там, где новые флагманы уже вошли в профессиональный прокат;
4. для bowed / historical / traditional развивать Maker / School / Specimen, а не искусственные SKU;
5. отдельно развивать rig-граф: инструмент → усилитель → cabinet → accessories → stage preparation;
6. различать exact request и согласованный substitute;
7. продолжать проверять полный реестр перед каждой новой сущностью.
