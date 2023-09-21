## I. Setup the configuration file

The `Makefile` gets configuration information like usernames and secrets from
[dotenv files](https://www.dotenv.org/docs/security/env.html).

Included is an empty template file, `.env.example`. Copy it to `.env` with:

```bash
cp .env.example .env
```

If you want a dev environment you can also copy it to `.env.dev`:

```bash
cp .env.example .env.dev
```

To switch between the production and development environments, set the `ENV` variable to `prod` or `dev`, respectively.

```bash
export ENV=dev  # set it as an environment variable
ENV=prod make help # or set it for each make command
```

## II. Prepare the Python environment

Use `pyenv` + `pyenv-virtualenv` to create virtual python environment to work in.

### 1 - Install `pyenv` + `pyenv-virtualenv`

Follow the installation instructions
[here for `pyenv`](https://github.com/pyenv/pyenv)
and [here for `pyenv-virtualenv`](https://github.com/pyenv/pyenv-virtualenv).
Don't forget to follow the instructions for
setting up your shell environment!

To activate `pyenv` and `pyenv-virtualenv`,
restart your shell after setting up the shell environment.

### 2 - Install Python

`pyenv` installs Python.

We use Python 3.11 and later in our development.
You can install it with:

```bash
pyenv install 3.11.5
```

### 3 - Create and activate the virtual environment

Environments isolate libraries used in one context from those used in another context.

For example, we can use them to isolate the libraries used in this project from those used in other projects.

Done naively, this would result in an explosion of space taken up by duplicated libraries.

Virtual environments allow the sharing of Python libraries across environments if they happen to be using the same version.

We create one for this project with:

```bash
pyenv virtualenv 3.11.5 youtube-search-rag-app
```

To start using it, we need to "activate" it:

```bash
pyenv activate youtube-search-rag-app
```

We've set it as the default environment for this directory with:

```bash
pyenv local youtube-search-rag-app
```

which generates a `.python-version` file in the current directory.

### 4 - Install the dependencies

Now that we have an environment for our project,
we can install the dependencies.

If you're interested in contributing, run

```bash
make dev-environment
```

which adds a few code quality checkers.
Otherwise, run

```bash
make environment
```
