from fastapi import FastAPI

app = FastAPI(title="Beyond the Veil")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
