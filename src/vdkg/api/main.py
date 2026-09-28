from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from vdkg.api.routes import router
from vdkg.config import WEB


def create_app() -> FastAPI:
    app = FastAPI(
        title="Vienna District KG",
        description="Knowledge Graph-based district similarity and lifestyle recommendation",
        version="0.1.0",
    )
    app.include_router(router)
    app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
    return app


app = create_app()
