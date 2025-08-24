'''FastAPI backend for drum transcription data labeling interface.

This backend processes audio files through the porcaro transcription pipeline
and serves audio clips with ML predictions for manual labeling by users.
'''

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from porcaro.api.routers import sessions, clips, labels

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    '''Application lifespan manager.'''
    logger.info('Starting porcaro labeling backend')
    yield
    logger.info('Shutting down porcaro labeling backend')


# Create FastAPI app
app = FastAPI(
    title='Porcaro Data Labeling API',
    description='Backend API for drum transcription data labeling interface',
    version='0.1.0',
    lifespan=lifespan,
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
async def root():
    '''Root endpoint.'''
    return {'message': 'Porcaro Data Labeling API', 'version': '0.1.0', 'docs': '/docs'}


@app.get('/health')
async def health_check():
    '''Health check endpoint.'''
    return {'status': 'healthy'}
