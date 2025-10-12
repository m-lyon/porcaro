'''FastAPI backend for drum transcription data labeling interface.

This backend processes audio files through the porcaro transcription pipeline
and serves audio clips with ML predictions for manual labeling by users.
'''

import logging

import uvicorn
from dotenv import find_dotenv
from dotenv import load_dotenv


def main() -> None:
    '''Main entry point to run the FastAPI app with Uvicorn.'''
    env_file = find_dotenv('.env.prod')
    load_dotenv(env_file)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    uvicorn.run(
        'porcaro.api.main:app',
        host='localhost',
        port=8000,
        reload=True,
        log_level='info',
    )


if __name__ == '__main__':
    main()
