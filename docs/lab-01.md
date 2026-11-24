# Лабораторная работа №1

## Ключи и партиционирование

Измерения сортируются по `id`, поскольку поиск идёт по идентификатору. Для
`dim_tariffs` ключ `(id, valid_from)` сохраняет отдельные версии одного тарифа.
Для привязок `(realty_id, gauge_id)` позволяет схлопнуть установку и аннулирование
одного счётчика. Показания сортируются по `(realty_id, reading_date)`, чтобы
корректировка заменяла значение за день; счета — по `(realty_id, created_at)` для
выборки по объекту и времени. Партиционирование не задано: объём лабораторного
датасета невелик, а дополнительные партиции усложнили бы слияние версий.

`make load` сначала очищает таблицы, поэтому повторная загрузка не добавляет дубли.

## SQL-проверки сценариев

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

Для сценария ошибочной строки сначала запоминаем корректное показание. Затем
вставляем строку за ту же дату, но с лишним нулём в `day_kw`. Ошибочной строке
задаём время `08:00:00`, раньше исходного показания (`09:00:00` или `12:00:00`),
чтобы фоновое слияние `ReplacingMergeTree` не вытеснило корректную версию.
У корректных показаний `day_kw` меньше `10000`, поэтому фильтр удаления
дополнительно отделяет строку с лишним нулём.

```sql
SELECT reading_date, day_kw, night_kw, created_at
FROM energosbyt.fact_meter_readings FINAL
WHERE realty_id = 1 AND reading_date = '2026-10-01';

INSERT INTO energosbyt.fact_meter_readings
    (realty_id, user_id, tariff_id, gauge_id,
     reading_date, day_kw, night_kw, created_at)
SELECT realty_id, user_id, tariff_id, gauge_id,
       reading_date, day_kw * 10, night_kw,
       toDateTime('2026-10-01 08:00:00')
FROM energosbyt.fact_meter_readings FINAL
WHERE realty_id = 1 AND reading_date = '2026-10-01';

SELECT day_kw, created_at FROM energosbyt.fact_meter_readings
WHERE realty_id = 1
  AND reading_date = '2026-10-01'
  AND day_kw >= 10000
  AND created_at = '2026-10-01 08:00:00';

ALTER TABLE energosbyt.fact_meter_readings DELETE
WHERE realty_id = 1
  AND reading_date = '2026-10-01'
  AND day_kw >= 10000
  AND created_at = '2026-10-01 08:00:00'
SETTINGS mutations_sync = 1;

SELECT count() FROM energosbyt.fact_meter_readings
WHERE realty_id = 1
  AND reading_date = '2026-10-01'
  AND day_kw >= 10000
  AND created_at = '2026-10-01 08:00:00';

SELECT reading_date, day_kw, night_kw, created_at
FROM energosbyt.fact_meter_readings FINAL
WHERE realty_id = 1 AND reading_date = '2026-10-01';
```

`count()` возвращает `0`: ошибочной строки больше нет. Последний запрос
возвращает то же корректное показание, что и первый.
