# Local Development Start

This project can run even if Windows blocks or reserves port `8000`.

## 1. Start Backend

```powershell
cd "C:\Users\HAMZA KHAN\Desktop\DNN project\backend"
python scripts\dev_start_backend.py
```

The helper checks `8000`, then falls back to `8001`, `8002`, or `8010`.
It prints the selected backend URL and the health endpoint.

For no-reload mode:

```powershell
python scripts\dev_start_backend.py --no-reload
```

If every port fails, run:

```powershell
netstat -ano | findstr :8000
netsh interface ipv4 show excludedportrange protocol=tcp
```

## 2. Point Frontend At Backend

Default frontend backend URL:

```text
http://127.0.0.1:8000
```

If the backend helper starts on `8001`, create or update `.env.local` in the project root:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8001
```

Then restart the Next.js dev server.

## 3. Start Frontend

```powershell
cd "C:\Users\HAMZA KHAN\Desktop\DNN project"
npm run dev -- --hostname 127.0.0.1 --port 3001
```

Open:

```text
http://localhost:3001/cases
```

## 4. Verify Research Workflow

With backend running:

```powershell
cd "C:\Users\HAMZA KHAN\Desktop\DNN project\backend"
python scripts\verify_cors_research.py
python scripts\verify_case_research_ui_flow.py
python scripts\verify_research_endpoints.py
```

These scripts work without OpenAI credentials by using the local deterministic fallback.
