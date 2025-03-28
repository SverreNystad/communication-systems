# Communication Systems Project


## Prerequisites

- Ensure that git is installed on your machine. [Download Git](https://git-scm.com/downloads)
- Docker is used for the backend and database setup. [Download Docker](https://www.docker.com/products/docker-desktop)
- Python 3.8 or higher is required for the backend. [Download Python](https://www.python.org/downloads/)


Configure the pre-commit hooks by running the following command in the terminal:
```bash
pip install pre-commit
pre-commit install
```

## Usage
To run the project, run the following commands in the terminal:
```bash
docker compose up --build
```


## Tests
To run the tests, run the following commands in the terminal:
```bash
docker compose run backend python -m pytest
```
