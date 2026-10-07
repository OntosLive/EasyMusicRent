# Расширение ONTOS.RENT: полный музыкальный комплект

7 октября 2026 года. Основа `893002c6eec3abc4515d6dafc40e2cd2214cc551`; её [выпуск 37575200503](https://github.com/OntosLive/EasyMusicRent/actions/runs/37575200503) подтверждён до начала изменений.

## Состояние и основание

Опубликованы **79 новых тем, включая 28 точных моделей**, и **25 уточнений существующих тем**: 20 изменений тела и 5 изменений только заголовка/метаданных. Ещё 14 прежних тем изменились только навигационно. Все 1901 старые темы, их родители, 21 alias и 3888 HTML-адресов сохранены. Общий корпус теперь содержит 1980 тем.

Полная локальная проверка пройдена: 209 тестов за 112,659 с, 3968 обычных документов, 78 перенаправлений, 1980 входов sitemap, один вариант контакта, 0 ошибок и 0 недостижимых страниц.

**Содержательный коммит `3e4c6ed2bf022e4838e7d752979d240bb296583c` успешно опубликован:** точный [выпуск 37585580963](https://github.com/OntosLive/EasyMusicRent/actions/runs/37585580963) завершён 7 октября в 07:11:45 UTC, дерево `714b93610efd2639c4cd058a493efc4b8d9865a6`. Отдельный прогон CI подтвердил 209 тестов за 99,095 с, 3968 обычных документов, 78 перенаправлений и 1980 входов sitemap. Результат CI не заменяет и не переименовывает прежний локальный журнал. [Подтверждение выпуска](2026-10-07-rental-expansion-release-confirmation.json) сохраняет данные точного коммита и workflow.

HTTP-проверка пакета завершена 7 октября в 07:13:56–07:20:27 UTC: все 238 файлов получили HTTP 200 и побайтно совпали с проверенной сборкой, ошибок — 0. Сверены 235 новых или изменённых HTML, robots.txt, sitemap.xml и CSS. [Отдельный отчёт публичной сверки](2026-10-07-rental-expansion-live-verification.json) фиксирует результаты, полные хеши и границы: HTTP-проверка всех страниц корпуса не заявляется.

В Chrome проверен путь от общего каталога через усиление и сценический звук к учебному вокальному комплекту. Новые подписи, раскрытие навигации и переходы N.0 → N.1 работают. В просмотренных страницах ширина документа не превышает ширину окна; мобильный просмотр этим проходом не заявляется. Сохранены [журнал браузерной проверки](2026-10-07-rental-expansion-browser-review.json) и [снимок опубликованной страницы](2026-10-07-rental-expansion-stage.jpg).

## Логика развития

Проект прошёл от ранней типографической «газеты аренды» к публичному интерфейсу инструментального фонда: короткий запрос ведёт к самостоятельному предметному тексту и контакту. Затем появились 13 семейств, точные модели и человеческие сцены — обучение, репетиция, запись, концерт. Следующие проходы связали эти темы, объединили смысловые дубли и исправили ранние формулировки. Восстановление 7 октября закрыло прежние подготовленные очереди и вернуло один канал main/codex/active.

Этот пакет развивает следующую конкретную потребность владельца: человек получает доступ ко всему музыкальному комплекту — от инструмента и микрофона до усиления, мониторинга, рабочего места и согласованного райдера. Новые темы размещены внутри прежних семейств. Сценический звук относится к усилителям/бэклайну, DJ — к электронным инструментам. На главной уточнены только две подписи; все 13 направлений и их порядок сохранены. [Полная эволюция и канон](../project-concept.md), [единственная текущая точка](../CURRENT-WORK-STATE.md).

## Что раскрыто

| Участок | Новых тем | Точных моделей | Результат |
| --- | ---: | ---: | --- |
| Вокал и сценический звук |27|12|Учебный вокальный комплект, фонограмма, дуэт, радиоканалы, микшеры, мониторинг и концертные консоли.|
| Мебель и учебные комплекты |16|0|Стулья, пюпитры, подсветка, стойки, принадлежности ударных, гитара/бас с комбиком.|
| Рояли и пианино |12|4|Кабинетный/малый, белый/чёрный/красный, цифровой рояль, акустическое пианино, банкетка и сценические применения.|
| DJ |17|9|Контроллер, самостоятельная система, раздельный райдер, винил, смена артистов, обучение и живые инструменты.|
| Инструментальные микрофоны |6|3|Микрофонная стойка, акустический ансамбль, SM57, SM81, BETA52A; связь с существующими DI.|
| Полнота звуковой системы |1|0|Сабвуферы; дополнены покрытие слушательских зон, состав и подготовка PA.|

Малый и кабинетный рояль объединены в один вход. Цифровой рояльный корпус отделён от акустического инструмента. Старые корпусные, переносные и сценические цифровые пианино дополнены по составу и способу использования. Новая электрогитара с комбиком описывает весь учебный комплект; прежняя домашняя сцена сохраняет свою задачу практики.

Точная модель не становится автоматической заменой другой модели райдера. У CL5 число каналов обработки отделено от локальных входов; у радиосистем различаются серия, передатчик, приёмник и капсюль; у DJ-контроллера — внешнее устройство и программная среда. Заводской комплект не объявляется составом прокатной выдачи. Во время проверки PLX-1000 отдельно исправлена двусмысленность о головке с иглой. [Предметные основания](../research/2026-10-07-rental-expansion-summary.json) ведут ко всем шести журналам.

## Исследование российских каталогов

Выборка включает **26 российских прокатных сайтов и 43 различных URL**. Подтверждения охватывают Москву, Санкт-Петербург, Казань, Екатеринбург и Новосибирск. В ней есть специализированные фортепианные прокаты, звуковые компании, каталоги бэклайна, мебели и DJ. Полный список доменов и соответствие журналам сохранены в [реестре исследования](../research/2026-10-07-rental-expansion-sites.json).

Каталоги подтверждают существование запроса и прокатной позиции. Технические свойства проверены по Shure, Yamaha, Kawai, Allen & Heath, QSC, Sennheiser, Pioneer DJ/AlphaTheta, Midas и документации других изготовителей. Тексты написаны заново в каноне фонда. Чужие цены, наличие, сроки и условия услуг не перенесены.

Самостоятельные предметы выбирались по реальному различию задачи. Линейки SKU не переписаны целиком. Для точных модификаций без достаточного подтверждения в журналах оставлена причина исключения. Свет, дым, конфетти, экраны и полная организация событий не включены в инструментальный фонд только по соседству в чужом каталоге.

## Аренда и прокат

В прежних search_title слово «прокат» отсутствовало, хотя надпись «ПРОСТОЙ МУЗЫКАЛЬНЫЙ ПРОКАТ» уже отображалась на каждом коротком входе. Теперь 54 поисковых заголовка содержат «прокат» или «напрокат», в том числе основные гитарные, клавишные, духовые, ударные, электронные и сценические направления. Существующие URL сохранены; страницы-дубли ради синонима не создавались.

| Поле | Страниц с аренд* до → после | Страниц с (на)прокат* до → после |
| --- | ---: | ---: |
|search_title|1895→1920|0→54|
|description|106→106|19→23|
|intro|115→116|30→48|
|blocks|1023→1028|56→105|
|kicker|144→144|1→1|

Считаются поля исходного содержания; постоянный N.0 kicker не входит в эту строку. Числа разных полей не складываются в уникальные темы. Это проверка языка, не измерение частотности Wordstat. [Google о понятных названиях и разных словах запроса](https://developers.google.com/search/docs/fundamentals/seo-starter-guide).

## Проверка структуры и готового сайта

Явные маршруты: 5285→5598. Маршруты вне прямого родителя и прямых детей: 3757→4031. Все 1754 конечные темы имеют такой выход. Два новых раздела с дочерними темами — радиомикрофоны и микшерные пульты — ведут только к своим прямым детям; это зафиксированное устройство разделов, а не конечные тупики. Повторов, самоссылок и неверных целей нет.

Получены 4046 HTML-путей и 4050 выходных файлов. Добавлены 158 HTML, изменены 77 прежних HTML и sitemap.xml; 3814 прежних выходных файлов побайтно совпали с проверенной основой. Компилятор и CSS не изменялись. Полный список различий находится в [сверке артефакта](2026-10-07-rental-expansion-artifact.json).

Проверки: [структура](2026-10-07-rental-expansion-structure.json), [граф](2026-10-07-rental-expansion-links.json), [изменённые поля до/после](2026-10-07-rental-expansion-field-changes.json), [навигация](2026-10-07-rental-expansion-navigation.json), [полный валидатор](2026-10-07-rental-expansion-validation.json), [журнал 209 тестов](2026-10-07-rental-expansion-tests.log). Полное чтение всего старого корпуса этим пакетом не заявляется: подробно проверены изменяемые и близкие по задаче контексты.

## Индексация

Поисковые N.0 имеют собственный canonical, открыты для обхода и включены в sitemap. Подробные N.1 имеют собственный canonical и намеренно сохраняют noindex,follow; их нет в sitemap. Эта архитектура не менялась.

Наличие sitemap и разрешённого обхода помогает обнаружить адреса, но не гарантирует включение каждого адреса в индекс. Подтвердить реальную индексацию можно по данным поисковиков. [Google: Sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview), [Google: noindex](https://developers.google.com/search/docs/crawling-indexing/block-indexing), [Яндекс: Sitemap](https://yandex.ru/support/webmaster/ru/indexing-options/sitemap).

## Все новые темы

| Поисковый вход | Родитель | Основание |
| --- | --- | --- |
|[Прокат сценического звука в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/scenicheskiy-zvuk/)|`usiliteli-backline`|Предмет или музыкальная задача|
|[Прокат вокальных микрофонов в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/vokalnye-mikrofony/)|`scenicheskiy-zvuk`|Предмет или музыкальная задача|
|[Аренда радиомикрофонов для вокала в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/radiomikrofony-dlya-vokala/)|`scenicheskiy-zvuk`|Предмет или музыкальная задача|
|[Прокат микшерных пультов для живого звука в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/mikshery-dlya-zhivogo-zvuka/)|`scenicheskiy-zvuk`|Предмет или музыкальная задача|
|[Аренда активной акустики для живого выступления в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/aktivnye-akusticheskie-sistemy/)|`scenicheskiy-zvuk`|Предмет или музыкальная задача|
|[Прокат сценических мониторов в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/scenicheskie-monitory/)|`scenicheskiy-zvuk`|Предмет или музыкальная задача|
|[Аренда персонального ушного мониторинга в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/personalnyy-ushnoy-monitoring/)|`scenicheskiy-zvuk`|Предмет или музыкальная задача|
|[Прокат вокального микрофона Shure SM58 в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/shure-sm58-v-arendu/)|`vokalnye-mikrofony`|Точная модель|
|[Аренда вокального микрофона Shure BETA 58A в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/shure-beta58a-v-arendu/)|`vokalnye-mikrofony`|Точная модель|
|[Прокат микрофона Sennheiser e 835-S в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/sennheiser-e835s-v-arendu/)|`vokalnye-mikrofony`|Точная модель|
|[Прокат радиосистемы Shure BLX24/SM58 в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/shure-blx24-sm58-v-arendu/)|`radiomikrofony-dlya-vokala`|Точная модель|
|[Прокат микшерного пульта Yamaha MG10XU в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/yamaha-mg10xu-v-arendu/)|`mikshery-dlya-zhivogo-zvuka`|Точная модель|
|[Аренда микшерного пульта Allen & Heath ZED-10FX в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/allen-heath-zed10fx-v-arendu/)|`mikshery-dlya-zhivogo-zvuka`|Точная модель|
|[Прокат цифрового микшера Behringer XR18 в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/behringer-xr18-v-arendu/)|`mikshery-dlya-zhivogo-zvuka`|Точная модель|
|[Аренда активной колонки QSC K12.2 в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/qsc-k122-v-arendu/)|`aktivnye-akusticheskie-sistemy`|Точная модель|
|[Прокат ушного мониторинга Sennheiser ew IEM G4 в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/sennheiser-ew-iem-g4-v-arendu/)|`personalnyy-ushnoy-monitoring`|Точная модель|
|[Прокат комплекта для обучения вокалу с микрофоном](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/komplekt-dlya-obucheniya-vokalu-s-mikrofonom/)|`scenicheskiy-zvuk`|Предмет или музыкальная задача|
|[Аренда звука для вокалиста с фонограммой](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/zvuk-dlya-vokalista-s-fonogrammoy/)|`scenicheskiy-zvuk`|Предмет или музыкальная задача|
|[Прокат микрофонов для двух вокалистов](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/mikrofony-dlya-vokalnogo-dueta/)|`vokalnye-mikrofony`|Предмет или музыкальная задача|
|[Аренда головного микрофона для поющего музыканта](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/golovnoy-mikrofon-dlya-poyuschego-instrumentalista/)|`radiomikrofony-dlya-vokala`|Предмет или музыкальная задача|
|[Прокат радиосистем для нескольких вокалистов](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/radiosistemy-dlya-neskolkih-vokalistov/)|`radiomikrofony-dlya-vokala`|Предмет или музыкальная задача|
|[Аренда микшера для записи репетиции](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/mikshery-dlya-zapisi-repetitsii/)|`mikshery-dlya-zhivogo-zvuka`|Предмет или музыкальная задача|
|[Прокат звука для учебного вокального концерта](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/zvuk-dlya-uchebnogo-vokalnogo-kontserta/)|`scenicheskiy-zvuk`|Предмет или музыкальная задача|
|[Аренда ушного мониторинга для первой репетиции](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/pervaya-repetitsiya-s-ushnym-monitoringom/)|`personalnyy-ushnoy-monitoring`|Предмет или музыкальная задача|
|[Аренда радиосистемы Shure QLXD24/B58 в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/shure-qlxd24-beta58a-v-arendu/)|`radiomikrofony-dlya-vokala`|Точная модель|
|[Прокат концертного пульта Yamaha CL5 в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/yamaha-cl5-v-arendu/)|`mikshery-dlya-zhivogo-zvuka`|Точная модель|
|[Аренда концертного микшерного пульта Midas M32 в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/midas-m32-v-arendu/)|`mikshery-dlya-zhivogo-zvuka`|Точная модель|
|[Прокат сценической мебели и стоек для музыкантов в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/scenicheskaya-mebel-i-stoyki/)|`usiliteli-backline`|Предмет или музыкальная задача|
|[Стул для музыканта напрокат](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/stul-dlya-muzykanta/)|`scenicheskaya-mebel-i-stoyki`|Предмет или музыкальная задача|
|[Аренда стула для барабанщика](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/stul-dlya-barabanshchika/)|`scenicheskaya-mebel-i-stoyki`|Предмет или музыкальная задача|
|[Прокат пюпитров для нот в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/pyupitr/)|`scenicheskaya-mebel-i-stoyki`|Предмет или музыкальная задача|
|[Аренда подсветки для пюпитра](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/podsvetka-dlya-pyupitra/)|`scenicheskaya-mebel-i-stoyki`|Предмет или музыкальная задача|
|[Стойка для гитары напрокат](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/stoyka-dlya-gitary/)|`scenicheskaya-mebel-i-stoyki`|Предмет или музыкальная задача|
|[Прокат стойки для клавишных инструментов](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/klavishnaya-stoyka/)|`scenicheskaya-mebel-i-stoyki`|Предмет или музыкальная задача|
|[Аренда стойки для ноутбука на сцену](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/stoyka-dlya-noutbuka-na-scene/)|`scenicheskaya-mebel-i-stoyki`|Предмет или музыкальная задача|
|[Прокат столика для перкуссии](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/stolik-dlya-perkussii/)|`scenicheskaya-mebel-i-stoyki`|Предмет или музыкальная задача|
|[Коврик для барабанной установки напрокат](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/kovrik-dlya-barabannoy-ustanovki/)|`scenicheskaya-mebel-i-stoyki`|Предмет или музыкальная задача|
|[Аренда подставки для комбоусилителя](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/stoyka-dlya-kombika/)|`scenicheskaya-mebel-i-stoyki`|Предмет или музыкальная задача|
|[Прокат педали для бас-барабана](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/pedal-dlya-bas-barabana/)|`barabannaya-ustanovka`|Предмет или музыкальная задача|
|[Аренда комплекта стоек для барабанной установки](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/komplekt-stoek-dlya-barabannoy-ustanovki/)|`barabannaya-ustanovka`|Предмет или музыкальная задача|
|[Электрогитара с комбиком для обучения напрокат](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/elektrogitara-s-kombikom-dlya-obucheniya/)|`elektrogitara`|Предмет или музыкальная задача|
|[Бас-гитара с комбиком для занятий в аренду](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/bas-gitara-s-kombikom-dlya-obucheniya/)|`bas-gitara`|Предмет или музыкальная задача|
|[Прокат стульев и пюпитров для ансамбля](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/mebel-i-pyupitry-dlya-ansamblya/)|`scenicheskaya-mebel-i-stoyki`|Предмет или музыкальная задача|
|[Кабинетный и малый рояль напрокат в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/kabinetnyy-royal/)|`royal`|Предмет или музыкальная задача|
|[Прокат белого рояля для мероприятия](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/belyy-royal/)|`royal`|Предмет или музыкальная задача|
|[Чёрный рояль напрокат в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/chernyy-royal/)|`royal`|Предмет или музыкальная задача|
|[Прокат красного рояля для сцены и съёмки](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/krasnyy-royal/)|`royal`|Предмет или музыкальная задача|
|[Прокат цифрового рояля в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/cifrovoy-royal/)|`cifrovoe-pianino`|Предмет или музыкальная задача|
|[Цифровой рояль Yamaha CLP-765GP в аренду](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/yamaha-clp765gp-v-arendu/)|`cifrovoy-royal`|Точная модель|
|[Цифровой рояль Kawai DG30 напрокат](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/kawai-dg30-v-arendu/)|`cifrovoy-royal`|Точная модель|
|[Акустический рояль Kawai GL-10 в аренду](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/kawai-gl10-v-arendu/)|`royal`|Точная модель|
|[Акустическое пианино Yamaha YUS1 напрокат](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/yamaha-yus1-v-arendu/)|`akusticheskoe-pianino`|Точная модель|
|[Прокат регулируемой банкетки для пианиста](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/banketka-dlya-pianista/)|`fortepiano`|Предмет или музыкальная задача|
|[Акустическое пианино для съёмки напрокат](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/pianino-dlya-semki/)|`akusticheskoe-pianino`|Предмет или музыкальная задача|
|[Рояль для фойе и встречи гостей в аренду](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/royal-dlya-foye/)|`royal`|Предмет или музыкальная задача|
|[Прокат DJ-оборудования в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/dj-oborudovanie/)|`elektronnye`|Предмет или музыкальная задача|
|[DJ-комплект для обучения в аренду](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/dj-komplekt-dlya-obucheniya/)|`dj-oborudovanie`|Предмет или музыкальная задача|
|[Прокат DJ-оборудования для репетиции перед выступлением](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/dj-oborudovanie-dlya-repetitsii-pered-vystupleniem/)|`dj-oborudovanie`|Предмет или музыкальная задача|
|[Аренда DJ-комплекта по райдеру артиста](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/dj-komplekt-po-rayderu/)|`dj-oborudovanie`|Предмет или музыкальная задача|
|[DJ-комплект для смены артистов в аренду](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/dj-komplekt-dlya-smeny-artistov/)|`dj-oborudovanie`|Предмет или музыкальная задача|
|[Аренда оборудования для DJ с живыми инструментами](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/dj-i-zhivye-instrumenty/)|`dj-oborudovanie`|Предмет или музыкальная задача|
|[Прокат виниловых проигрывателей для DJ в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/vinilovye-dj-proigryvateli/)|`dj-oborudovanie`|Предмет или музыкальная задача|
|[Аренда стола для DJ-оборудования в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/stol-dlya-dj-oborudovaniya/)|`dj-oborudovanie`|Предмет или музыкальная задача|
|[Аренда Pioneer DJ CDJ-3000 в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/pioneer-cdj-3000-v-arendu/)|`dj-oborudovanie`|Точная модель|
|[Прокат AlphaTheta CDJ-3000X в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/alphatheta-cdj-3000x-v-arendu/)|`dj-oborudovanie`|Точная модель|
|[Аренда DJ-микшера Pioneer DJ DJM-A9 в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/pioneer-djm-a9-v-arendu/)|`dj-oborudovanie`|Точная модель|
|[Прокат Pioneer DJ DJM-900NXS2 в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/pioneer-djm-900nxs2-v-arendu/)|`dj-oborudovanie`|Точная модель|
|[Аренда Allen & Heath Xone:96 в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/allen-heath-xone-96-v-arendu/)|`dj-oborudovanie`|Точная модель|
|[Прокат Pioneer DJ XDJ-RX3 в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/pioneer-xdj-rx3-v-arendu/)|`dj-oborudovanie`|Точная модель|
|[Аренда AlphaTheta XDJ-AZ в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/alphatheta-xdj-az-v-arendu/)|`dj-oborudovanie`|Точная модель|
|[Прокат DJ-контроллера Pioneer DJ DDJ-FLX4 в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/pioneer-ddj-flx4-v-arendu/)|`dj-oborudovanie`|Точная модель|
|[Аренда винилового проигрывателя Pioneer DJ PLX-1000](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/pioneer-plx-1000-v-arendu/)|`vinilovye-dj-proigryvateli`|Точная модель|
|[Прокат микрофонной стойки в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/mikrofonnaya-stoyka/)|`scenicheskaya-mebel-i-stoyki`|Предмет или музыкальная задача|
|[Прокат инструментальных микрофонов в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/instrumentalnye-mikrofony/)|`scenicheskiy-zvuk`|Предмет или музыкальная задача|
|[Аренда микрофонов для акустического ансамбля в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/mikrofony-dlya-akusticheskogo-ansamblya/)|`instrumentalnye-mikrofony`|Предмет или музыкальная задача|
|[Аренда Shure SM57 в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/shure-sm57-v-arendu/)|`instrumentalnye-mikrofony`|Точная модель|
|[Прокат Shure SM81 в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/shure-sm81-v-arendu/)|`instrumentalnye-mikrofony`|Точная модель|
|[Аренда Shure BETA 52A для большого барабана в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/shure-beta52a-v-arendu/)|`instrumentalnye-mikrofony`|Точная модель|
|[Прокат сценических сабвуферов в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/scenicheskie-sabvufery/)|`scenicheskiy-zvuk`|Предмет или музыкальная задача|

## Прежние темы с изменённым содержанием или метаданными

| Тема | Изменённые поля |
| --- | --- |
|[Аренда акустического пианино в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/akusticheskoe-pianino/)|`intro`|
|[Аренда концертного рояля в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/arenda-koncertnogo-royalya-moskva/)|`blocks`|
|[Бэклайн для акустического концерта в аренду](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/backline-dlya-akusticheskogo-kontserta/)|`description`, `blocks`, `sources`|
|[Бэклайн для быстрой смены групп в аренду](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/backline-dlya-bystroy-smeny-grupp/)|`blocks`|
|[Бэклайн для фестиваля в аренду](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/backline-dlya-festivalya/)|`blocks`|
|[Бэклайн для вокалиста с гитарой в аренду](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/backline-dlya-vokalista-s-gitaroy/)|`description`, `blocks`, `sources`|
|[Бэклайн по райдеру для группы в аренду](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/backline-po-rayderu-dlya-gruppy/)|`description`, `blocks`, `sources`|
|[Прокат цифрового пианино в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/cifrovoe-pianino/)|`search_title`, `intro`|
|[Прокат духовых музыкальных инструментов в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/duhovye/)|`search_title`, `description`, `blocks`|
|[Прокат электронных музыкальных инструментов в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/elektronnye/)|`search_title`, `description`, `kicker`, `intro`|
|[Электронные барабаны для домашних занятий в аренду](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/elektronnye-barabany-dlya-domashnih-zanyatiy/)|`blocks`|
|[Прокат гитарных усилителей в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/gitarnye-usiliteli/)|`search_title`|
|[Прокат гитар в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/gitary/)|`search_title`, `description`|
|[Инструментальный комплект в аренду, если не хватает мониторинга](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/instrument-esli-ne-hvataet-monitoringa/)|`blocks`, `sources`|
|[Прокат клавишных инструментов в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/klavishnye/)|`search_title`, `description`|
|[Корпусное цифровое пианино в аренду](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/korpusnoe-cifrovoe-pianino/)|`intro`, `blocks`, `sources`|
|[Переносное цифровое пианино в аренду](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/perenosnoe-cifrovoe-pianino/)|`intro`, `blocks`, `sources`|
|[Аренда рояля в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/royal/)|`intro`|
|[Рояль для съёмки в аренду](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/royal-dlya-semki/)|`blocks`, `sources`|
|[Прокат сценических клавишных в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/scenicheskie-klavishnye/)|`search_title`|
|[Сценическое цифровое пианино в аренду](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/stsenicheskoe-cifrovoe-pianino/)|`blocks`|
|[Прокат ударных музыкальных инструментов и перкуссии в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/udarnye/)|`search_title`, `description`|
|[Прокат усилителей, сценического звука и бэклайна в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/usiliteli-backline/)|`search_title`, `editorial_title`, `description`, `kicker`, `intro`, `blocks`, `quote`|
|[Yamaha Clavinova CLP в аренду в Москве](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/yamaha-clavinova-clp-v-arendu/)|`intro`, `sources`|
|[Акустическое пианино Yamaha U1 в аренду](https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai/yamaha-u1-v-arendu/)|`blocks`|

## Предложение об источниках

Публичное отображение сейчас сохранено: свёрнутый details после цитаты и перед контактом. Владелец попросил предложение в конце работы, поэтому этот пакет не меняет ни порядок, ни CSS блока.

Рекомендация: перенести источники после контакта к самому низу раскрытия и оставить одну спокойную свёрнутую строку. В ней достаточно документации, полезной для проверки конкретной модели. Российские каталоги и основания редакционных решений сохраняются в исследовательских журналах. Источники обеспечивают проверяемость; отдельная заметная плашка перед контактом не является условием технической индексации. Короткие поисковые входы сохраняют минимальную композицию.

## Граница завершения

Успешный выпуск точного содержательного SHA и публичная HTTP-сверка подтверждены. Их результаты закрепляет закрывающий документационный checkpoint: содержание сайта он не меняет и проходит собственный workflow. Дополнительный рекурсивный коммит только ради записи SHA этой фиксации не нужен.

Пакет не подтверждает собственные складские остатки, цену или наличие на дату. Дальнейшее содержательное расширение начинается с нового конкретного запроса или обнаруженного пробела; прежние закрытые очереди и keep не возобновляются автоматически.
