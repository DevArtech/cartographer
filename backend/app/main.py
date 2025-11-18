from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.mapper import router as mapper_router


def create_app() -> FastAPI:
	app = FastAPI(title="Cartographer Backend", version="0.1.0")

	# Allow local dev UIs
	app.add_middleware(
		CORSMiddleware,
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	app.include_router(mapper_router, prefix="/api")
	return app


app = create_app()


