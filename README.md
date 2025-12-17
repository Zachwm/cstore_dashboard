# How to run

## Build the Docker image
docker build -t my-python-app .

## Run the container
docker run -p 8051:8051 -v "${PWD}/vibrant-keyword-481505-f4-dd23afe5a12d.json:/key.json" -e GOOGLE_APPLICATION_CREDENTIALS=/key.json my-python-app

This also mounts a key that in the real would everyone would have their own and would not be in the repo.

## Then open in browser:
http://localhost:8051
