import argparse

from nonbonded.frontend import index
from nonbonded.frontend.app import app


def main():

    parser = argparse.ArgumentParser(description="Launches the GUI server.")
    parser.add_argument("--debug", action="store_true")

    arguments = parser.parse_args()

    index.initialize()
    app.run_server(debug=arguments.debug)


if __name__ == "__main__":
    main()
