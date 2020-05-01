import argparse

import uvicorn

from nonbonded.frontend import index
from nonbonded.frontend.app import app


def main_gui():

    parser = argparse.ArgumentParser(description="Launches the GUI server.")
    parser.add_argument("--debug", action="store_true")

    arguments = parser.parse_args()

    index.initialize()
    app.run_server(debug=arguments.debug)


def main_rest():

    parser = argparse.ArgumentParser(description="Launches the RESTful API.")
    parser.add_argument("--debug", action="store_true")

    arguments = parser.parse_args()

    uvicorn.run(
        "nonbonded.backend.app:app",
        host="127.0.0.1",
        port=5000,
        log_level="info",
        reload=arguments.debug,
    )
