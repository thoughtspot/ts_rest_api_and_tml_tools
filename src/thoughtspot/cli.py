import subprocess as sp
import pathlib
import os

from typer import Argument as A_, Option as O_
import requests
import typer

from thoughtspot import ThoughtSpot, MetadataNames


_ERROR = typer.style(f'[ERROR] ', fg='red', bold=True)
_INFO  = typer.style(f'[INFO]  ', fg='blue', bold=True)


app = typer.Typer(
    name="ts-examples",
    help="""
    ThoughtSpot Rest API and TML Examples

    \b
    To get started, please see the repository on GitHub:
      https://github.com/thoughtspot/ts_rest_api_and_tml_tools
    """,
    no_args_is_help=True,
    add_completion=False,
    context_settings={
        # global settings
        'help_option_names': ['--help', '-h'],

        # increase terminal width because it's not 1990.
        'max_content_width': 120,

        # allow case-insensitive commands
        'token_normalize_func': lambda x: x.lower()
    }
)


@app.command(no_args_is_help=True)
def info(
    ts_server: str = O_(
        ...,
        help='your ThoughtSpot cluster URL',
        envvar='TS_SERVER',
        prompt=True
    ),
    ts_username: str = O_(
        ...,
        help='your ThoughtSpot local user',
        envvar='TS_USERNAME',
        prompt=True
    ),
    ts_password: str = O_(
        ...,
        help='your ThoughtSpot local user password (input is hidden)',
        envvar='TS_PASSWORD',
        prompt=True,
        hide_input=True,
        confirmation_prompt=True
    )
):
    """
    Show information about your ThoughtSpot cluster.
    """
    ts = ThoughtSpot(server_url=ts_server)

    try:
        ts.login(username=ts_username, password=ts_password)
    except requests.exceptions.HTTPError as e:
        typer.echo(f'Login to ThoughtSpot failed: {e.response.content}')
        return

    r = ts.tsrest.session.get(ts.tsrest.base_url + 'session/info')
    data = r.json()

    typer.echo(
        _INFO + f"""Hello {data['userDisplayName']}!

        ThoughtSpot Version: {data['releaseVersion']}
        Branch: {'Cloud' if 'cl' in data['releaseVersion'] else 'Software'}

        Server URL: {ts_server}
        Local User: {data['userName']}
        Timezone: {data['timezone']}
        """
    )


@app.command(no_args_is_help=True, hidden=True)
def prep(
    example_subdirectory: pathlib.Path = A_(
        ...,
        help='the directory to run a pre-commit check on',
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    )
):
    """
    Run the pre-commit pipeline on your code (prior to submitting a PR).
    """
    if not (example_subdirectory / 'README.md').exists():
        typer.echo(_ERROR + 'You must include a README.md describing the example functionality!')

    isort = (
        'isort',
        '--length-sort',
        '--reverse-sort',
        example_subdirectory.as_posix()
    )

    black = (
        'black',
        '--line-length', '120',
        '--target-version', 'py36',
        example_subdirectory.as_posix()
    )

    for cmd in (isort, black):
        typer.echo(_INFO + 'Running ' + typer.style(cmd[0], fg='yellow', bold=True))

        with sp.Popen(cmd, stdout=sp.PIPE) as proc:
            for line in proc.stdout:
                typer.echo(typer.style(line.decode().strip(), fg='white', bold=True))


def run():
    """
    Main function of the basic CLI.
    """
    app()
