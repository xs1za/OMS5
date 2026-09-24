# OMS5 Operations Service

`OMS5` - микросервис операционного контура. На текущем этапе он объединяет бизнес-сущности `Клиент`, `Смена`, `Задание`, `Табель`.

## Почему эти сущности объединены

На старте эти сущности тесно связаны одним бизнес-процессом:

- клиент заказывает работы;
- под клиента создаются смены;
- внутри смен создаются задания;
- по сменам и сотрудникам формируется табель.

Поэтому отдельные микросервисы для каждой сущности пока были бы избыточны. Когда модель усложнится, можно выделить `Client Service`, `Planning Service` и `Timesheet Service`.

## Функции

- Создание клиента.
- Создание смены по клиенту.
- Создание задания внутри смены.
- Создание табельной записи по сотруднику и смене.
- Получение краткой сводки по операционным данным.
- Публикация доменных событий в Kafka.

## Технологии

- Python 3.11
- FastAPI
- Uvicorn
- in-memory хранилище для стартового прототипа
- confluent-kafka

## API

### Health check

```http
GET /health
```

### Создать клиента

```http
POST /clients
Content-Type: application/json
```

Тело запроса:

```json
{
  "name": "ООО Клиент",
  "external_id": "CLIENT-0001"
}
```

### Создать смену

```http
POST /shifts
Content-Type: application/json
```

Тело запроса:

```json
{
  "client_id": "client-uuid",
  "starts_at": "2026-01-20T09:00:00Z",
  "ends_at": "2026-01-20T18:00:00Z",
  "location": "Москва"
}
```

### Создать задание

```http
POST /tasks
Content-Type: application/json
```

Тело запроса:

```json
{
  "shift_id": "shift-uuid",
  "title": "Проверить объект",
  "description": "Выполнить стартовую проверку объекта перед сменой",
  "assignee_employee_id": 1
}
```

### Создать табельную запись

```http
POST /timesheets
Content-Type: application/json
```

Тело запроса:

```json
{
  "employee_id": 1,
  "shift_id": "shift-uuid",
  "work_date": "2026-01-20",
  "hours": 8
}
```

### Получить сводку

```http
GET /operations/summary
```

Ответ:

```json
{
  "clients": 1,
  "shifts": 1,
  "tasks": 1,
  "timesheets": 1
}
```

## Kafka events

- `operations.client_created` - создан клиент.
- `operations.shift_created` - создана смена.
- `operations.task_created` - создано задание.
- `operations.timesheet_created` - создана табельная запись.

## Переменные окружения

| Переменная | Значение по умолчанию | Назначение |
| --- | --- | --- |
| `SERVICE_NAME` | `OMS5` | Имя сервиса |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka.oms.svc.cluster.local:9092` | Kafka bootstrap servers |

## Локальный запуск

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8005
```

Встроенный Swagger UI FastAPI для OMS5:

```text
http://localhost:8005/docs
```

Это Swagger только текущего сервиса OMS5. Общая Swagger UI страница для единой спецификации `platform/contracts/openapi_oms_microservices.json` запускается отдельно из корня проекта и открывается без `/docs`:

```powershell
docker run --rm `
  --name oms-swagger-ui `
  -p 8088:8080 `
  -e SWAGGER_JSON=/spec/platform/contracts/openapi_oms_microservices.json `
  -v "D:/ProjectsDocker/extrawork:/spec" `
  swaggerapi/swagger-ui:v5.17.14
```

```text
http://localhost:8088
```

Через Ingress сервис доступен без port-forward. Встроенный Swagger UI OMS5:

```text
http://oms.local/oms5/docs
```

## Docker

```bash
docker build -t oms5:latest .
docker run --rm -p 8005:8000 oms5:latest
```

## Kubernetes

```bash
kubectl apply -f ../platform/k8s/namespace.yaml
kubectl apply -f k8s/
kubectl -n oms port-forward svc/oms5 8005:80
```

После port-forward встроенный Swagger UI OMS5 доступен по адресу:

```text
http://localhost:8005/docs
```

## Важно для production

- Сейчас используется in-memory хранилище, данные теряются при рестарте.
- Нужно добавить БД, миграции и полноценные CRUD-операции.
- Нужно добавить проверку существования сотрудника через `OMS2`.
- Нужно добавить авторизацию через `OMS1`.
- Для табеля нужно добавить бизнес-правила: пересечения смен, лимиты часов, статусы согласования.
