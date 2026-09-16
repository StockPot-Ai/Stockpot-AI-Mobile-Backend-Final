import os
from run import app

if __name__ == "__main__":
    from app.config import Config
    port = Config.PORT
    debug = Config.DEBUG
    app.run(host="0.0.0.0", port=port, debug=debug)
