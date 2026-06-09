# Resource Partner AI

<!-- codex-repo-note:start -->
## Справка о репозитории / Repository note

**RU:** AI-помощник для планирования и подбора ресурсов.

**EN:** an AI assistant for resource planning and matching.

**Статус / Status:** активный проект 2026 года; ожидает ревизии README и кода. / active 2026 project; README and code review are pending.

**Текущее имя / Current name:** `resource-partner-ai`

**Плановое имя / Planned name:** `resource-partner-ai`

**Topics:** `ai`, `cleanup-pending`, `needs-review`, `python`, `resource-planning`, `status-active`, `type-app`
<!-- codex-repo-note:end -->


MVP B2B AI SaaS-портала для агентского канала продаж застройщика ГК «Ресурс».

## Что реализовано

- кабинет риелтора с защитой сделки по телефону клиента;
- интерактивная витрина лотов ЖК с бронированием;
- кабинет менеджера для подтверждения или отклонения брони;
- dashboard РОПа с KPI, конверсией, долей агентского канала и активностью партнеров;
- AI-помощник агента на rule-based логике, готовый к подключению LLM API;
- обзор альтернативных цифровых инструментов для расширения третьей главы диплома;
- seed-команда с демоданными для показа MVP на защите.

## Запуск

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

После запуска открыть: http://127.0.0.1:8000

## PyCharm

Откройте эту папку как проект PyCharm. В `.idea/runConfigurations` добавлена конфигурация
`Django Server`, которая запускает `manage.py runserver 127.0.0.1:8000`.
