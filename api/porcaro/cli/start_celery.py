import sys

from dotenv import find_dotenv
from dotenv import load_dotenv

env_file = find_dotenv('.env.prod')
load_dotenv(env_file)


def main() -> None:
    '''Start Celery worker.'''
    from porcaro.api.celery import app

    argv = ['-A', 'porcaro.api.celery:app', 'worker', '--loglevel=INFO'] + sys.argv[1:]
    app.start(argv)


if __name__ == '__main__':
    main()
