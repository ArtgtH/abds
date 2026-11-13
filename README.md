# Лабораторный проект

[![labs](https://github.com/{your_username}/{your_repo}/actions/workflows/energosbyt.energosbyt.lab.yml/badge.svg)](https://github.com/{your_username}/{your_repo}/actions/workflows/energosbyt.energosbyt.lab.yml)

Backend-сервис вымышленной ЖКХ-компании для практики по курсу «Архитектура систем обработки больших данных».

## С чего начать

1. **‼️ Настройте репозиторий** — проведите обязательную настройку контрибьюторов и защиты ветки (см. ниже)
2. **[Лабораторные работы](https://github.com/sitnikovik/abds/tree/master/lab)** — технические задания для каждой лабораторной работы
3. **[CONTRIBUTING.md](CONTRIBUTING.md)** — требования к структуре проекта, процесс разработки и проверки
4. **[Документация курса](https://github.com/sitnikovik/abds)** — методические материалы и дополнительные ресурсы

> [!IMPORTANT]
> Поменяйте `{your_username}` и `{your_repo}` в badge на ваши имя пользователя и название репозитория.

## Настройка репозитория

### Защита основной ветки

После создания репозитория из шаблона **обязательно настройте правила защиты для ветки `main`**:

1. Откройте **Settings** → **Branches** → **Add classic branch protection rule**
2. В поле **Branch name pattern** укажите: `main`
3. Включите следующие опции:
   - **Require a pull request before merging**
     - Require approvals: **1**: требует минимум одного одобрения перед слиянием
   - ***Require status checks to pass before merging***
     - Выберите *"autograder"*: проверит все лабораторные работы автоматически
     - ***Require branches to be up to date before merging*** (рекомендуется):
     требует, чтобы ветка PR была синхронизирована с последними изменениями из основной ветки перед слиянием
   - ***Do not allow bypassing the above settings***: запрещает обход настроек защиты ветки
4. Нажмите **Create** или **Save changes**

> ⚠️ **Важно:** Без этих настроек автоматические проверки не будут блокировать PR с ошибками.

### Добавление коллабораторов

Чтобы преподаватели могли проводить код-ревью:

1. Откройте **Settings** → **Collaborators**
2. Нажмите **Add people**
3. Добавьте всех кто есть в списке ревьюеров в файле [CODEOWNERS](CODEOWNERS)
4. Выберите роль: **Write** (или выше), иначе ревьюер не сможет одобрить PR

## Помощь

Возникли вопросы? → [@sitnikovik](https://t.me/sitnikovik)

## Лабораторная работа №1

### Ключи и партиционирование

Измерения сортируются по `id`, поскольку поиск идёт по идентификатору. Для
`dim_tariffs` ключ `(id, valid_from)` сохраняет отдельные версии одного тарифа.
Для привязок `(realty_id, gauge_id)` позволяет схлопнуть установку и аннулирование
одного счётчика. Показания сортируются по `(realty_id, reading_date)`, чтобы
корректировка заменяла значение за день; счета — по `(realty_id, created_at)` для
выборки по объекту и времени. Партиционирование не задано: объём лабораторного
датасета невелик, а дополнительные партиции усложнили бы слияние версий.

`make load` сначала очищает таблицы, поэтому повторная загрузка не добавляет дубли.

### SQL-проверки сценариев

После `PATCH /users/1` с новым ФИО результат запроса содержит только новое ФИО
в актуальном состоянии SCD 1:

```sql
SELECT id, fio FROM energosbyt.dim_users FINAL WHERE id = 1;
```

После двух последовательных смен телефона запрос SCD 3 показывает последний
телефон в `phone`, а предыдущий — в `phone_prev`:

```sql
SELECT phone, phone_prev FROM energosbyt.dim_users FINAL WHERE id = 1;
```

Две версии тарифа SCD 2 разделены границей `2025-11-01`. Запрос показывает
непересекающиеся интервалы и открытую версию до 2099 года:

```sql
SELECT valid_from, valid_to, price_day_kwph, price_night_kwph
FROM energosbyt.dim_tariffs FINAL WHERE id = 1 ORDER BY valid_from;
```

Старый счёт остаётся в таблице с первоначальной суммой; для пересчёта тарифа
за старый месяц используется версия, действовавшая на дату счёта:

```sql
SELECT created_at, day_kw, night_kw, price FROM energosbyt.fact_invoice
WHERE realty_id = 1 AND created_at = '2025-10-01 10:00:00';
SELECT valid_from, valid_to, price_day_kwph, price_night_kwph
FROM energosbyt.dim_tariffs FINAL
WHERE valid_from <= '2025-10-01 10:00:00'
  AND '2025-10-01 10:00:00' < valid_to;
```

После повторной передачи показания за дату `FINAL` возвращает одну последнюю
версию, хотя старая строка физически ещё может существовать:

```sql
SELECT reading_date, day_kw, night_kw, created_at
FROM energosbyt.fact_meter_readings FINAL
WHERE realty_id = 1 AND reading_date = '2026-10-01';
```

После `POST /realty/1/gauges` запрос показывает только новую активную установку
с увеличенной версией:

```sql
SELECT gauge_id, version FROM energosbyt.fact_gauge_bindings FINAL
WHERE realty_id = 1;
```

Ошибочное показание удаляется SQL-мутацией. Последний запрос возвращает `0`:

```sql
ALTER TABLE energosbyt.fact_meter_readings DELETE
WHERE realty_id = 1 AND reading_date = '2026-10-01'
SETTINGS mutations_sync = 1;
SELECT count() FROM energosbyt.fact_meter_readings FINAL
WHERE realty_id = 1 AND reading_date = '2026-10-01';
```
