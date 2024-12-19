# AI Publishing Feedback Experimentation

**Archived** - Repository of experimentation that may get picked up later.

A store of Data Science experimental work, started in Feb 2024, on how AI could help in understanding user feedback in GOV.UK Publishing.

## Nomenclature

TODO

## Technical documentation

You have two options for running the application locally:

1. run it over the remote vector store (Qdrant collection), or
2. populate a local collection and run over that.

You can run locally either with docker from the command line, or using docker-compose to run everything with one command. You can also deploy the application to Cloud Run using Cloud Build which allows you to run the application in the cloud.


### Populating the collection only

You can run `collection/main.py` to populate the collection, setting environment variables to relevant IP addresses and ports, depending on whether you are running locally or remotely (e.g. on a VM). Set the arguments "-ev" to only populate the evaluation collection, and "-rs" to attempt to restore the collection(s) from the latest available snapshot. If this is not set, or fails, the script will query BigQuery, create vectors and populate the collection(s) with these.

### Running the application locally using Docker compose

Note: This will run the Streamlit app, the Qdrant database, and the evaluation script on your local machine.

To run the application, make sure you have docker and docker-compose installed and have the relevant environment variables stored (speak with the AI team). Then run `docker-compose up`.

You will also need to download data to fill the dashboard dropdowns. The script `app/get_metadata_for_filters.py` does this and is run in `app/main.py`.

### Running the application locally using Docker

To run locally using Docker, you can run `docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant` and then run `python collection/create_collection.py` to populate the local collection, ensuring QDRANT_HOST is set to "localhost" in your environment variables. This may take a while to run

You can then run `streamlit run app/main.py` to run the application locally.

### Running the application locally using a remote Qdrant database in Compute Engine

Note: This will run ONLY the Streamlit app on your local machine.

To run the application locally using a remote Qdrant database in Compute engine you can simply run `streamlit run app/main.py` from the root directory. This will start the application on your local machine and connect to the remote Qdrant database IF you have the correct environment variables set. The environment variables are stored in the `compute_engine.env` file in the root directory.

_Troubleshooting: Pay particular attention to the QDRANT_HOST environment variable, and ensure that the VM instance is running in Google Compute Engine. If the collection on the VM has not been created/populated yet, run `python collection/create_collection.py` to populate it._

### Deploy the application to Cloud Run with Cloud Build

Note: This will deploy the Streamlit app to Cloud Run using Cloud Build.

Check that the root directory contains a `cloudbuild.yaml` and a `Dockerfile`. These files define the build process and app requirements.

1. **Build the Image**: From the root directory, run `gcloud builds submit --config cloudbuild.yaml`. This command builds the app's container image using Cloud Build, based on instructions in `cloudbuild.yaml`, and pushes it to Google Artifact Registry.

2. **Deploy to Cloud Run**: Instead of manually setting environment variables in the cloud console, run the `deploy_to_cloudrun.sh` script locally using `bash deploy_to_cloudrun.sh`. This script automates the deployment to Cloud Run, including setting environment variables.

_Troubleshooting: if the service is deployed but the application fails saying that it cannot find a folder/file, then you can use `gcloud builds submit --config cloudbuild_ls.yaml`. This takes the image pushed to Artifact Registry, opens it, and runs a command to recursively list the files in the container. This can help you debug what files are missing. This will not download the image to your local machine which saves space (~8GB) but will still take a while to run._

### A note on Poetry

To install dependencies into a new environment, run `poetry install`. This will create an environment if one does not already exist, following the naming convention "project-name-py3.XX".

To add and remove more packages to the Poetry toml and lock, and therefore the environment, use `poetry add package-name` and `poetry remove package-name`. For dev dependencies (e.g. black), use the --group dev flag.

To run commands in the virtual env managed by poetry, either run `poetry shell` to open a terminal in the environment, or use `poetry run python scripts/myscript.py...`, where `poetry run` runs the subsequent command in the poetry virtual environment.

To run an ipython notebook in a virtual environment managed by poetry, run `poetry run python -m ipykernel install --user --name myname` to add a jupyter kernel for the existing poetry environment.

## To download data from GCS

To download a file from a Google Cloud Storage (GCS) bucket using the gsutil command-line tool, you can use the cp command.
To download the file to a specific directory, specify the full path to the directory in the command.

e.g. `gsutil cp gs://example-bucket/example.json /path/to/your/local/directory`

If you're in the root directory of our folder you can download the data using the following command:

`gsutil cp gs://example-bucket/example.json $(pwd)/data/file.json`

*Make sure you have the necessary permissions to access the GCS bucket and download the file. If you're not already authenticated,
you may need to run `gcloud auth login` to set up your credentials.*

## Licence

[MIT License](LICENCE)
