"""DTS FB Activities - FastAPI application for dengue surveillance data."""

__version__ = "0.1.0"

def main() -> None:
    """Entry point for the application."""
    import uvicorn
    from .app import app

    uvicorn.run(app, host="0.0.0.0", port=8000)
