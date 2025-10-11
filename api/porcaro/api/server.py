'''FastAPI backend for drum transcription data labeling interface.

This backend processes audio files through the porcaro transcription pipeline
and serves audio clips with ML predictions for manual labeling by users.
'''

import logging
from contextlib import asynccontextmanager
from collections.abc import Callable
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from porcaro.api.routers import clips
from porcaro.api.routers import labels
from porcaro.api.routers import sessions
from porcaro.api.database.connection import create_db_and_tables

logger = logging.getLogger(__name__)


def create_lifespan(
    create_tables: bool = True,
) -> Callable:
    '''Create lifespan function with configurable behavior.'''

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
        '''Application lifespan manager.'''
        logger.info('Starting porcaro labeling backend')
        if create_tables:
            # Create database tables on startup
            create_db_and_tables()
            logger.info('Database tables created')
        yield
        logger.info('Shutting down porcaro labeling backend')

    return lifespan


def create_app(*, create_tables: bool = True) -> FastAPI:
    '''Create and configure the FastAPI application.'''
    # Create FastAPI app
    app = FastAPI(
        title='Porcaro Data Labeling API',
        description='Backend API for drum transcription data labeling interface',
        version='0.1.0',
        lifespan=create_lifespan(create_tables),
    )

    # Add CORS middleware for frontend integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            'http://localhost:3000',
            'http://localhost:5173',
        ],  # Common React dev ports
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    # Include routers
    app.include_router(sessions.router, prefix='/api/sessions', tags=['sessions'])
    app.include_router(clips.router, prefix='/api/clips', tags=['clips'])
    app.include_router(labels.router, prefix='/api/labels', tags=['labels'])

    @app.get('/')
    async def root() -> dict[str, str]:
        '''Root endpoint.'''
        return {
            'message': 'Porcaro Data Labeling API',
            'version': '0.1.0',
            'docs': '/docs',
        }

    @app.get('/health')
    async def health_check() -> dict[str, str]:
        '''Health check endpoint.'''
        return {'status': 'healthy'}

    return app
