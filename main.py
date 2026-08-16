from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.models import tenant, widget, submission
from app.routers import auth, widgets, public, submissions

app = FastAPI(title="Widget Platform API")

Base.metadata.create_all(bind=engine)

# CORS: the public config + submission endpoints must be reachable from
# any origin, since we don't control what site embeds the widget.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(auth.router)
app.include_router(widgets.router)
app.include_router(public.router)
app.include_router(submissions.router)


@app.get("/")
def root():
    return {"name": "Widget Platform API", "version": "1.0"}


@app.get("/health")
def health():
    return {"status": "ok"}