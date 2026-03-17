.PHONY: init lint test docker-up

init:
\tpython -m pip install --upgrade pip
\tpip install -r requirements.txt
\tpre-commit install

lint:
\tblack --check .
\truff check .

test:
\tSECRET_KEY=test-secret python -m pytest -q tests

docker-up:
\tdocker-compose up --build
