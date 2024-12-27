import os
from datetime import datetime
from src import log
from flask import Flask
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

logger = log.configure()
app = Flask(__name__)


@app.route('/health-check', methods=['GET'])
def health_check():
    return {
        "status_code": 200,
        "datetime": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }


def main():
    debug = True if 'ORGANAIZER_ADMIN_DEBUG_MODE' not in os.environ else os.getenv('ORGANAIZER_ADMIN_DEBUG_MODE') == 'True'
    host = "0.0.0.0" if 'ORGANAIZER_ADMIN_HTTP_HOST' not in os.environ else os.getenv('ORGANAIZER_ADMIN_HTTP_HOST')
    port = 80 if 'ORGANAIZER_ADMIN_HTTP_PORT' not in os.environ else int(os.getenv('ORGANAIZER_ADMIN_HTTP_PORT'))
    
    log.app_print(logger, [
        f"Starting HTTP Service!",
        f"{'DEBUG MODE ENABLED' if debug else 'PRODUCTION MODE'}",
        f"HOST: {host}",
        f"PORT: {port}"
    ])
    
    app.run(debug=debug, host=host, port=port)

if __name__ == '__main__':
    main()