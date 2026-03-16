import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

from app.routers.predict import router as predict_router

app = FastAPI(title="MicroLens Teeth Detection API")


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Server is ready to accept traffic."}


app.include_router(predict_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
