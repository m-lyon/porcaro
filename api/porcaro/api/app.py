'''FastAPI backend for drum transcription data labeling interface.

This backend processes audio files through the porcaro transcription pipeline
and serves audio clips with ML predictions for manual labeling by users.
'''

import uvicorn
import logging


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    uvicorn.run(
        'porcaro.api.server:app',
        host='0.0.0.0',
        port=8000,
        reload=True,
        log_level='info',
    )
