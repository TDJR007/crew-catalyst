## Watch the App in Action!

<video src="./demo.mp4" controls width="800">
  Your browser does not support the video tag.
</video>

[Download / watch the demo video](./demo.mp4)

---

### Local Development Instructions

#### Prerequisites

* **Python** (version specified in `backend/pyproject.toml`)
* **Node.js** (LTS recommended)
* **uv** installed

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

---

### 1. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run build
```

This generates the production build in `frontend/dist`.

---

### 2. Backend (Flask + uv)

```bash
cd ../backend
uv sync
```

---

### 3. Run the application (Waitress)

```bash
uv run app.py
```

The Flask app will start using **Waitress** on port **8080**.

---

### 4. Access the app

Open your browser at:

```
http://localhost:8080
```

---

### Notes

* Re-run `npm run build` in `frontend/` when frontend changes are made.
* Set required environment variables (refer `.env.sample`) before running the backend.
