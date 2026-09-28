import subprocess


def get_docker_state():
    result = subprocess.run(
        [
            "docker",
            "ps",
            "-a",
            "--format",
            "{{.Names}}|{{.State}}",
        ],
        capture_output=True,
        text=True,
    )

    containers = {}

    if result.returncode != 0:
        return containers

    for line in result.stdout.splitlines():
        if "|" not in line:
            continue

        name, state = line.split(
            "|",
            1,
        )

        containers[name] = (
            state.strip().lower() == "running"
        )

    return containers