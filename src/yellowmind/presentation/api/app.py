"""FastAPI application."""

from fastapi import FastAPI

from yellowmind import __version__


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="YellowMind API",
        version=__version__,
        description="Tour de France prediction platform",
    )

    @app.get("/health")
    def health() -> dict[str, str]:  # pyright: ignore[reportUnusedFunction]
        return {"status": "ok", "version": __version__}

    return app


app = create_app()
