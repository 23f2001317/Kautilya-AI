from fastapi import FastAPI

app = FastAPI(title="Kautilya AI Backend API")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to Kautilya AI API"}
