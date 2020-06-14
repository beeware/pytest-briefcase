import sys

from briefcase.config import AppConfig, parse_config
from briefcase.platforms import get_platforms


__version__ = '0.1.1'


class BriefcasePytestConfigError(Exception):
    pass


def pytest_addoption(parser):
    # The app name. If there's only one app, this isn't required;
    # use * as a placeholder for this.
    parser.addoption(
        "--app",
        default="*",
        help="The Briefcase app name to test",
    )

    # The application platform
    default_platform = {
        'darwin': 'macOS',
        'linux': 'linux',
        'win32': 'windows',
    }[sys.platform]
    parser.addoption(
        "--platform",
        default=default_platform,
        help="The Briefcase app platform to test (default '{default_platform}')".format(
            default_platform=default_platform
        ),
    )

    # The output format. Will
    parser.addoption(
        "--output-format",
        dest="output_format",
        help="The Briefcase app output format to test",
    )


def pytest_cmdline_main(config):
    "Parse the command line, adding the sys.path entries needed to support the app"
    app_name = config.getoption("app")
    platform = config.getoption("platform")

    # Load the platform module and determine the default output format.
    platforms = get_platforms()
    platform_module = platforms[platform]

    # Determine the output format to target
    try:
        output_format = config.getoption("output_format")
    except ValueError:
        output_format = platform_module.DEFAULT_OUTPUT_FORMAT

    # Load the application config from the pyproject.toml
    # in the pytest rootdir
    _, app_configs = parse_config(
        config.rootdir / 'pyproject.toml',
        platform=platform,
        output_format=output_format
    )

    # If no app name has been provided, check to see if there is
    # a single app in the project. If there is, use it. Otherwise,
    # raise an error.
    # If an app name has been provided, load that app config.
    if app_name == '*':
        if len(app_configs) == 1:
            app = AppConfig(**list(app_configs.values())[0])
        else:
            raise BriefcasePytestConfigError(
                'More than one app in the porject. Specify an app name with --app'
            )
    else:
        try:
            app = AppConfig(**app_configs[app_name])
        except KeyError:
            raise BriefcasePytestConfigError(
                "'{app_name}' is not an app name in this project".format(
                    app_name=app_name
                )
            )

    # Process the `sources` list for the app, adding to the pythonpath.
    # This matches the PYTHONPATH configuration done by `briefcase dev`
    for path in app.PYTHONPATH:
        sys.path.insert(0, str(config.rootdir / path))
