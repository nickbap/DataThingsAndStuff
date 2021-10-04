import argparse

from dtns import create_app

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run the app with a specific config")
    parser.add_argument("app_config", type=str, help="The config to use for the app")

    args = parser.parse_args()

    app = create_app(args.app_config)

    app.run()
