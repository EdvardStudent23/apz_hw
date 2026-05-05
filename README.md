# Lab 5 — Мікросервіси з Consul

## Структура проекту

```
lab5/
├── docker-compose.yml          ← запуск всієї системи
├── test_report.py              ← тестові POST/GET запити для звіту
├── benchmark.py                ← вимірювання продуктивності
├── test_failover.py            ← демонстрація failover (вимога 5)
│
├── consul-init/
│   ├── init.sh                 ← завантажує KV конфіги в Consul
│   └── consul_helper.py        ← спільний модуль (реєстрація, discovery, KV)
│
├── facade-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 ← resolve() через Consul; MQ конфіг з KV
│   └── consul_helper.py
│
├── logging-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 ← Hazelcast конфіг з Consul KV
│   └── consul_helper.py
│
└── counter-service/
    ├── Dockerfile
    ├── requirements.txt
    ├── main.py                 ← MQ конфіг з Consul KV; MongoDB
    └── consul_helper.py
```

---

## Як Consul виконує кожну роль

| Роль | Що робить | Де в коді |
|---|---|---|
| **Service Register** | Кожен сервіс реєструється при старті | `register_service()` в `lifespan` |
| **Service Discovery** | facade знаходить адреси logging/counter | `resolve("logging-service")` |
| **Config Server** | Hazelcast і MQ конфіги зберігаються в KV | `kv_get("config/hazelcast/*")` |

### Consul KV структура:
```
config/hazelcast/members        = hz1:5701,hz2:5701,hz3:5701  ← читає logging-service
config/hazelcast/cluster-name   = dev
config/hazelcast/map-name       = logs_map
config/mq/members               = hz1:5701,hz2:5701,hz3:5701  ← читають facade + counter
config/mq/cluster-name          = dev
config/mq/queue-name            = transactions_queue
config/mq/poll-timeout-sec      = 2
```

---

## Покрокова інструкція для звіту

### Крок 1 — Запустити систему

```bash
cd lab5
docker-compose up --build
```

Дочекайтесь поки всі сервіси стартують (30–60 сек).

### Крок 2 — Перевірити Consul UI (скріншот для звіту)

Відкрити браузер: **http://localhost:8500**

Має відображатись:
- `facade-service` — 2 instances
- `logging-service` — 3 instances  
- `counter-service` — 2 instances

Перейти у **Key/Value** → побачити всі `config/hazelcast/*` та `config/mq/*`

### Крок 3 — Запустити тестові запити

```bash
pip install requests
python3 test_report.py
```

Скопіювати весь вивід у звіт.

### Крок 4 — Запустити benchmark

```bash
python3 benchmark.py
```

Значення з виводу вставити в таблицю звіту (колонка Task 5).

### Крок 5 — Демонстрація failover

```bash
python3 test_failover.py
```

Під час виконання зробити скріншот **http://localhost:8500** — видно що logging-2 змінив статус.

---

## Порти сервісів

| Сервіс | Порт |
|---|---|
| facade-service-1 | :8000 |
| facade-service-2 | :8003 |
| counter-service-1 | :8001 |
| counter-service-2 | :8002 |
| logging-1/2/3 | без прямого порту (внутрішні) |
| Consul UI | :8500 |
| Hazelcast 1/2/3 | :5701/:5702/:5703 |
| MongoDB | :27017 |

## Ручні curl запити (для звіту)

```bash
# POST — транзакція
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "amount": 500}'

# GET — баланс конкретного user
curl http://localhost:8000/user/alice

# GET — всі баланси
curl http://localhost:8000/accounts

# GET — метрики часу
curl http://localhost:8000/stats

# GET — Consul KV (всі конфіги)
curl "http://localhost:8500/v1/kv/?recurse"

# GET — живі екземпляри logging-service
curl "http://localhost:8500/v1/health/service/logging-service?passing=true"
```

## Таблиця продуктивності (заповнити після benchmark.py)

| Test scenarios | Task 1 (in-mem) | Task 3 (DB) | Task 5 (final) |
|---|---|---|---|
| **10 accounts** | | | |
| Total time | ___ ms | ___ ms | ___ ms |
| logging-service contribution | ___ ms | ___ ms | ___ ms |
| counter-service contribution | ___ ms | ___ ms | ___ ms |
| **1 account** | | | |
| Total time | ___ ms | ___ ms | ___ ms |
| logging-service contribution | ___ ms | ___ ms | ___ ms |
| counter-service contribution | ___ ms | ___ ms | ___ ms |

## GitHub

```bash
git checkout -b micro_consul
git add .
git commit -m "Lab 5: Consul service discovery + KV config"
git push origin micro_consul
```
