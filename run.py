import os
from app import create_app
from app.config import Config

app = create_app()

if __name__ == "__main__":
    port = Config.PORT
    debug = Config.DEBUG
    print(f"==================================================")
    print(f" StockPot AI Backend Server Running")
    print(f" Local URL:   http://localhost:{port}")
    print(f" Network URL: http://0.0.0.0:{port}")
    print(f" Health API:  http://localhost:{port}/api/health")
    print(f" Mock Mode:   {Config.USE_MOCK_DATA}")
    print(f"==================================================")
    app.run(host="0.0.0.0", port=port, debug=debug)
