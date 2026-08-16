from fastapi import FastAPI
from app.database import Base, engine
from app.models import tenant, widget, submission

app = FastAPI(title="Widget Platform API")

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"name": "Widget Platform API", "version": "1.0"}


@app.get("/health")
def health():
    return {"status": "ok"}