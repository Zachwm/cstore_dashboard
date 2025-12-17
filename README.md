# How to Run

Live Demo: https://cstore-dashboard-178610202074.us-west3.run.app

## 1. Build the Docker Image

Run the following command in your project directory:

    docker build -t cstore-dashboard .

---

## 2. Run the Container

To access the data, you must have a service account key from the owner.  

1. Place the key in the project directory and name it:

    google_authentication.json

2. Run the container with the key mounted and environment variable set:

        docker run -p 8080:8080 -v "${PWD}/google_authentication.json:/key.json" -e GOOGLE_APPLICATION_CREDENTIALS=/key.json -e PORT=8080 cstore-dashboard

**Important:** Do **not** commit `google_authentication.json` to GitHub, the key gets deactiveted when exposed.

---

## 3. Open the App in Your Browser

Once the container is running, visit:

    http://localhost:8080


1.	Explain the added value of using DataBricks in your Data Science process (using text, diagrams, and/or tables).
   
Databricks allows you to work with data that is much larger than any single pc can handle. Its very useful because they do all of the processing across servers that allows you to do much more than is possible on a standalone computer. It also is helpful to allow you to share data and collaborate on projects

2.	Compare and contrast PySpark to Pandas or the Tidyverse (using text, diagrams, and/or tables).
   
Pyspark and pandas are both used for data manipulation but pyspark is a much larger tool that allows you to do much more. Pandas is good if you need to make quick changes because of its flexibility but it runs into issues if the data gets to big. Pyspark on the other hand is built for that big data it can be more trouble than its worth if you don’t need it but when its needed its extremely useful.

3.	Explain Docker to somebody intelligent but not a tech person (using text, diagrams, and/or tables).
   
Docker is a tool any programmer can utilize to help make sure that things work properly. It can get messy trying to access certain file paths across different pcs and Docker is simply a tool that we use to make sure we have the same files and that they are in the same spot.

4.	Compare GCP to AWS for cost, features, and ease of use.
   
GCP is a simpler more predictable often cheaper option, AWS has a lot more options can be less predictable when it comes to price and can cost more. They both have data analytics and ml options but AWS does have more. Overall they both have good use cases AWS is just a larger more advanced option where as if you don’t need all those features GCP may be a better option.
