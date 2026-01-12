from bec_launcher.deployments import get_available_deployments


def launch(base_path: str) -> None:
    deployments = get_available_deployments(base_path)
    print(f"Launching BEC Launcher with base path: {base_path}")
    print(f"Available deployments: {deployments}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BEC Launcher")
    parser.add_argument(
        "--base-path",
        type=str,
        help="Base path for deployments, typically /sls/<beamline>/config/bec",
        required=True,
    )

    args = parser.parse_args()
    base_path = args.base_path
    launch(base_path)
