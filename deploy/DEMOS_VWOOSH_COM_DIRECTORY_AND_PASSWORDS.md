---
id: "12.02-202609210345"
title: "demos.vwoosh.com — Demos Directory, Passwords & Server Management"
aliases: ["VWOOSH Demos Directory", "AGNTCon Demo Manual", "Пароли демо-стендов vwoosh.com"]
domain: "Infrastructure"
type: guide
status: active
publish: false
tags:
  - "#demos"
  - "#vwoosh"
  - "#oracle-cloud"
  - "#infrastructure"
  - "#passwords"
  - "#admin"
  - "#mcp"
summary: "Справочник всех демо-проектов на demos.vwoosh.com, URL-адреса, пароли оператора, руководство пользователя и администратора, а также траблшутинг AGNTCon + MCPCon Europe 2026 Intelligence Hub."
created: "2026-09-21"
modified: "2026-09-21"
---

# 🌐 Демо-платформа `demos.vwoosh.com` — Справочник, пароли и управление

Единая суверенная витрина интерактивных прототипов и ИИ-ассистентов платформы **VWOOSH**.  
Хостинг на постоянно бесплатной инфраструктуре Oracle Cloud Always Free (Амстердам) с исходящим шифрованным туннелем Cloudflare (Zero Open Web Ports).

---

## 📌 1. Паспорт инфраструктуры

| Параметр | Значение | Примечание |
| :--- | :--- | :--- |
| **Хостинг** | Oracle Cloud Infrastructure (Always Free) | Дата-центр `eu-amsterdam-1` (Амстердам, Нидерланды) |
| **Сервер / Shape** | `agntcon-hub-prod` / Ampere A1 ARM64 | 1 OCPU / 6.0 GB RAM / 46.6 GB Balanced SSD (€0.00/мес) |
| **Белый IPv4** | `84.235.169.106` | Статический/Ephemeral IPv4 (входящие порты 80/443 закрыты) |
| **Сетевой шлюз** | Cloudflare Tunnel (`vwoosh-oracle-demos`) | Шифрованный исходящий туннель к Cloudflare Edge |
| **SSH-доступ** | `ssh ubuntu@84.235.169.106` | Ключ `~/.ssh/id_ed25519` (парольный вход отключен) |
| **Служба демо** | `agntcon-hub.service` | Автозапуск systemd, изоляция `ProtectSystem=strict` |
| **Keepalive** | `oci_keepalive.sh` (cron каждые 6 часов) | Защита от деактивации Oracle по 7-дневному простою |

---

## 🔑 2. Сводный реестр демо-проектов и доступов

| Демо-проект | Назначение | Публичный URL | Доступ / Пароль | Порт на сервере |
| :--- | :--- | :--- | :--- | :--- |
| **AGNTCon Hub 2026** | Интеллектуальный хаб и MCP-ассистент конференции (113 докладов) | `https://agntcon-demo.vwoosh.com/` | **Открытый** (без пароля) | `127.0.0.1:8088` |
| **Панель Mini-CRM** | Операторский пульт заявок на коллаборацию и споров спикеров | `https://agntcon-demo.vwoosh.com/admin` | Пароль: **`agntcon2026admin`** | `127.0.0.1:8088/admin` |
| **Приватные тикеты** | Веб-треды переписки с клиентами без регистрации | `https://agntcon-demo.vwoosh.com/ticket?id=...&key=...` | Секретный ключ в URL | `127.0.0.1:8088/ticket` |
| **Телеметрия очереди** | Мониторинг очереди и семафора инференса | `https://agntcon-demo.vwoosh.com/api/queue-status` | Открытый JSON | `127.0.0.1:8088/api/` |

> [!TIP] Как изменить пароль администратора:
> Подключитесь по SSH к серверу и выполните:
> ```bash
> sudo sed -i 's/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD="ВАШ_НОВЫЙ_ПАРОЛЬ"/' /etc/agntcon-hub/hub.env
> sudo systemctl restart agntcon-hub
> ```

---

## 👤 3. Руководство для Пользователей (User Experience)

### 3.1 Поиск и работа с базой знаний (113 докладов)
- **Полнотекстовый поиск FTS5:** Введите ключевые слова в поисковую строку. Поддерживается поиск по спикерам, компаниям, стеку технологий и ключевым выводам.
- **Фильтр «📄 Slides Attached Only»:** Показывает только 45 докладов, к которым спикеры прикрепили слайды.
- **Интерактивные модальные окна:** Клик по карточке открывает разбор доклада по методологии Карпаты (Суть, Ключевые выводы, Ловушки и грабли, Цитаты Sched).

### 3.2 Персонализация «🎯 My Profile»
1. Нажмите кнопку **«🎯 My Profile»** в верхнем меню.
2. Выберите свою роль, отметьте фокусные темы, выберите первичную цель и введите произвольные технические интересы (до 500 знаков).
3. Нажмите **«Save Profile»**. Все данные сохраняются **100% локально в вашем браузере (`localStorage`)** без передачи персональных данных на сервер.

### 3.3 Интерактивный планировщик «📦 My Track Studio»
1. Откройте **«📦 My Track»** в верхнем меню.
2. Нажмите **«✨ Auto-Curate (AI Fit)»** — система автоматически рассчитает аффинити всех 113 докладов к вашему профилю.
3. **Регулятор отсечки (Cut-Off Level):** Выберите минимальный процент совпадения (`≥75%` по умолчанию, `≥85%` для жесткого отбора, `≥60%` для широкого охвата). Список адаптируется на лету!
4. **Экспорт программы:** 
   - **«📄 Save / Print Single PDF Dossier»** — формирует чистый векторный PDF буклет для печати или сохранения.
   - **«💾 Download Obsidian Vault (.zip)»** — скачивает архив заметок с YAML-метаданными и `[[wikilinks]]` для импорта в ваш Obsidian.

### 3.4 Чат-ассистент «💬 Ask Conference Assistant»
- **Режим 1: ☁️ Managed Cloud Demo (Free):** Работает из коробки без настроек. Запросы обслуживаются бесплатным каскадом OpenRouter (`openrouter/free`) $\to$ Kilocode (`kilo-auto/free`).
- **Режим 2: 💻 Local BYOM (LM Studio / Ollama):** В настройках (Settings) можно подключить локальный инференс (`http://127.0.0.1:1234`). В браузерах Chrome/Brave/Edge подключение работает автоматически.

---

## 🛠️ 4. Руководство для Администратора (Admin Operations)

### 4.1 Работа в пульте Mini-CRM (`/admin`)
1. Откройте `https://agntcon-demo.vwoosh.com/admin` и введите `agntcon2026admin`.
2. В левой колонке отображаются все входящие тикеты с бейджами:
   - `💼 Collaboration` (Заявки на проекты, пилоты, консалтинг)
   - `🚨 Dispute` (Запросы спикеров на коррекцию или отзыв доклада)
3. **Обработка тикета:**
   - Выберите тикет в списке.
   - Переключите вкладку *«Send Reply»* (клиент увидит ответ в своем приватном веб-треде) или *«Internal Note»* (желтая внутренняя заметка, скрытая от клиента).
   - Смена статуса: `Open` $\to$ `In Progress` $\to$ `Resolved` $\to$ `Archived`.
   - Мгновенные уведомления о новых заявках дублируются в Telegram через бота `ToyProjectsBot`.

### 4.2 Управление сервисом через SSH
```bash
# Подключение к серверу
ssh ubuntu@84.235.169.106

# Проверка статуса сервиса
sudo systemctl status agntcon-hub

# Перезапуск сервиса
sudo systemctl restart agntcon-hub

# Просмотр логов в реальном времени
sudo journalctl -u agntcon-hub -f

# Проверка Cloudflare Tunnel
sudo systemctl status cloudflared
```

### 4.3 Обновление кода из репозитория
```bash
# На ноутбуке (ThinkPad):
git -C 02_public_hub push origin main
rsync -avz --exclude='.venv' 02_public_hub/site/ ubuntu@84.235.169.106:/opt/agntcon-hub/site/

# На сервере (при необходимости перезапуска бэкенда):
sudo systemctl restart agntcon-hub
```

### 4.4 Резервное копирование базы заявок (CRM SQLite)
База тикетов находится в `/opt/agntcon-hub/data/crm.sqlite`.
```bash
# Скачать бэкап базы на свой ноутбук:
scp ubuntu@84.235.169.106:/opt/agntcon-hub/data/crm.sqlite ~/Backups/agntcon_crm_$(date +%F).sqlite
```

---

## 🚨 5. Траблшутинг и решение инцидентов (Troubleshooting)

### Инцидент 1: «All community free inference tiers are temporarily busy» (HTTP 503)
* **Причина:** Превышен минутный лимит запросов (5 req/min на IP), суточный лимит площадки (200 req/day) или временная задержка upstream OpenRouter/Kilocode.
* **Решение:** Подождите 15–30 секунд. Если нагрузка велика, в настройках (Settings) можно включить локальный LM Studio или ввести персональный API-ключ.

### Инцидент 2: «Connection error to /api/chat. Is serve.py running?»
* **Причина:** Процесс сервера был перезапущен во время удержания соединения, либо служба упала.
* **Решение:** Проверьте `sudo systemctl status agntcon-hub`. Если служба остановлена, запустите: `sudo systemctl start agntcon-hub`.

### Инцидент 3: «Insecure Local Endpoint over HTTPS» при подключении LM Studio
* **Поведение:** Предупреждение носит чисто информационный характер. В браузерах на базе Chromium (Chrome, Brave, Edge) локальный `127.0.0.1` разрешен по стандарту безопасности.
* **Проверка:** Нажмите кнопку *«Test Model Endpoint»*. Если внизу появился зеленый статус `✓ Online & Validated LLM inference! (HTTP 200)`, значит модель работает идеально и на предупреждение можно не обращать внимания.
* **Для Safari / Firefox:** Если браузер жестко режет `http` с `https`, используйте бесплатный туннель Cloudflare на своем компьютере:
  ```bash
  cloudflared tunnel --url http://127.0.0.1:1234
  ```
  И вставьте полученный `https://...trycloudflare.com` адрес в поле Base URL.

### Инцидент 4: Сервер не отвечает по публичному домену
* **Проверка 1:** Проверьте доступность туннеля: `sudo systemctl status cloudflared`.
* **Проверка 2:** Проверьте локальный отклик бэкенда: `curl -s http://127.0.0.1:8088/api/queue-status`.
* **Проверка 3:** Проверьте дашборд Cloudflare Zero Trust $\to$ Networks $\to$ Tunnels $\to$ `vwoosh-oracle-demos` (статус должен быть `HEALTHY`).
