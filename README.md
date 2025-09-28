# Сервис для поиска айтемов

## Для добавления каталогов:
- Добавить `.jsonl` файлы в item_search/app/src/catalogues
- После старта сервиса `POST` запрос на `http://<service>:8000/warmup` со следующим payload.
```json
{
    "catalog_id":"<your_catalogue_id_(can_be_random)>",
    "references":[
        "<your_catalogue_name>.jsonl"
    ], 
    "limit_items": 5000
}
```

## Для получения поискового ответа (текст):
- Дождаться status_code=`200` со стороны сервиса на `.../warmup`.
- Отправить `POST` запрос на `http://<service>:8000/search`
```json
{
    "catalog_id": "<your_catalogue_id_(from_your_warmup)>",
    "query_text": "Гипсокартон Кнауф 2500x1200 12.5мм",
    "top_k": 5,
    "threshold": 0.5
}
```
- Получить ответ

## Для получения поискового ответа из ФАЙЛА:
- Отправить `POST` multipart/form-data на `http://<service>:8000/search/file` с полями:
  - `catalog_id` (form field)
  - `file` (binary, ваш документ/изображение)
  - опционально: `top_k`, `threshold`

### Примеры запросов

#### curl

1) Warmup каталога
```bash
curl -X POST "http://<service>:8000/warmup" \
  -H "Content-Type: application/json" \
  -d '{
    "catalog_id": "my-catalog",
    "references": ["test_catalogue.jsonl"],
    "limit_items": 5000
  }'
```

2) Поиск по тексту
```bash
curl -X POST "http://<service>:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "catalog_id": "my-catalog",
    "query_text": "Гипсокартон Кнауф 2500x1200 12.5мм",
    "top_k": 5,
    "threshold": 0.5
  }'
```

3) Поиск по файлу
```bash
curl -X POST "http://<service>:8000/search/file" \
  -F "catalog_id=my-catalog" \
  -F "file=@/path/to/your/file.pdf" \
  -F "top_k=5" \
  -F "threshold=0.5"
```

#### Python (requests)

1) Warmup каталога
```python
import requests

BASE = "http://<service>:8000"

payload = {
    "catalog_id": "my-catalog",
    "references": ["test_catalogue.jsonl"],
    "limit_items": 5000,
}
r = requests.post(f"{BASE}/warmup", json=payload, timeout=120)
print(r.status_code, r.json())
```

2) Поиск по тексту
```python
import requests

BASE = "http://<service>:8000"

payload = {
    "catalog_id": "my-catalog",
    "query_text": "Гипсокартон Кнауф 2500x1200 12.5мм",
    "top_k": 5,
    "threshold": 0.5,
}
r = requests.post(f"{BASE}/search", json=payload, timeout=60)
print(r.status_code, r.json())
```

3) Поиск по файлу
```python
import requests

BASE = "http://<service>:8000"

data = {
    "catalog_id": "my-catalog",
    "top_k": "5",           # form fields должны быть строками
    "threshold": "0.5",
}
with open("/path/to/your/file.pdf", "rb") as f:
    files = {"file": ("file.pdf", f, "application/pdf")}
    r = requests.post(f"{BASE}/search/file", data=data, files=files, timeout=120)
    print(r.status_code, r.json())
```

### Вспомогательные эндпоинты
- `GET /healthz` — жив ли сервис
- `GET /readyz?catalog_id=<id>` — загружен ли конкретный каталог; без параметра возвращает список загруженных каталогов