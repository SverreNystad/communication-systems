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

Setup the virtual environment by running the following command in the terminal:
```bash
python -m venv venv
```
Activate the virtual environment by running the following command in the terminal:
```bash
source venv/bin/activate
```

Install the required packages by running the following command in the terminal:
```bash
pip install -r requirements.txt
```


## Usage
To run MQTT broker run the following command in the terminal:
```bash
docker compose up --build
```

### Run Client Application
Then run the following commands on the client:
```bash
python src/app.py
```

### Run Server Application Raspberry Pi:
Run the following commands on the server:
```bash
python src/server.py
```

### Run Scooter Service on Raspberry Pi (Sense HAT):
```python
python src/scooter_service.py
```


## Tests
To run the tests, run the following commands in the terminal:
```bash
docker compose run backend python -m pytest
```
