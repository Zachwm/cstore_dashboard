# How to Run

## 1. Build the Docker Image

Run the following command in your project directory:

    docker build -t cstore-dashboard .

---

## 2. Run the Container

To access the data, you must have a service account key from the owner.  

1. Place the key in the project directory and name it:

    google_authentication.json

2. Run the container with the key mounted and environment variable set:

        docker run -p 8051:8051 -v "${PWD}/google_authentication.json:/key.json" -e GOOGLE_APPLICATION_CREDENTIALS=/key.json my-python-app

**Important:** Do **not** commit `google_authentication.json` to GitHub, the key gets deactiveted when exposed.

---

## 3. Open the App in Your Browser

Once the container is running, visit:

    http://localhost:8051
