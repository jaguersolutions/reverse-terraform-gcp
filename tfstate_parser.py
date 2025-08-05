import argparse
import json
import os
from google.cloud import storage

def sanitize_for_terraform(name):
    """Sanitizes a name for use as a Terraform resource name."""
    return name.replace('-', '_')

def download_tfstate(project_id, state_file_path):
    """Downloads the tfstate file from a GCS path."""
    if not state_file_path.startswith("gs://"):
        print("Error: Invalid GCS path. It must start with 'gs://'.")
        return None

    # Tira o gs://
    path_without_prefix = state_file_path[5:]
    # Pega o nome do bucket
    bucket_name = path_without_prefix.split('/')[0]
    # Pega o caminho do arquivo
    blob_name = "/".join(path_without_prefix.split('/')[1:])

    try:
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        if not blob.exists():
            print(f"Error: The file does not exist at the specified path: {state_file_path}")
            return None

        print(f"Downloading {state_file_path}...")
        return json.loads(blob.download_as_string())
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def generate_resources_from_state(tfstate_data):
    """Generates Terraform resource blocks from a tfstate file."""
    if not tfstate_data or "resources" not in tfstate_data:
        print("No resources found in the state file.")
        return

    output_dir = "generated_terraform"
    os.makedirs(output_dir, exist_ok=True)

    # Dictionary to hold file handlers
    file_handlers = {}

    for resource in tfstate_data["resources"]:
        resource_type = resource["type"]

        if resource_type == "google_storage_bucket":
            output_subdir = "gcs"
            output_filename = "buckets.tf"
            for instance in resource["instances"]:
                attributes = instance["attributes"]
                bucket_name = attributes["name"]
                resource_name = sanitize_for_terraform(bucket_name)
                tf_block = f"""
resource "google_storage_bucket" "{resource_name}" {{
  name          = "{bucket_name}"
  project       = "{attributes['project']}"
  location      = "{attributes['location']}"
  storage_class = "{attributes['storage_class']}"
}}
"""
                print(f"Generated resource for GCS bucket: {bucket_name}")

        elif resource_type == "google_secret_manager_secret":
            output_subdir = "secret_manager"
            output_filename = "secrets.tf"
            for instance in resource["instances"]:
                attributes = instance["attributes"]
                secret_id = attributes["secret_id"]
                resource_name = sanitize_for_terraform(secret_id)
                tf_block = f"""
resource "google_secret_manager_secret" "{resource_name}" {{
  project   = "{attributes['project']}"
  secret_id = "{secret_id}"
  replication {{ automatic = true }}
}}
"""
                print(f"Generated resource for Secret Manager secret: {secret_id}")

        elif resource_type == "google_cloudbuild_trigger":
            output_subdir = "cloud_build"
            output_filename = "triggers.tf"
            for instance in resource["instances"]:
                attributes = instance["attributes"]
                trigger_id = attributes["trigger_id"]
                name = attributes["name"]
                resource_name = sanitize_for_terraform(name if name else trigger_id)
                tf_block = f"""
resource "google_cloudbuild_trigger" "{resource_name}" {{
  project  = "{attributes['project']}"
  location = "{attributes['location']}"
  name     = "{name}"
  filename = "cloudbuild.yaml" # Placeholder
}}
"""
                print(f"Generated resource for Cloud Build trigger: {name}")

        elif resource_type == "google_cloud_run_v2_service":
            output_subdir = "cloud_run"
            output_filename = "services.tf"
            for instance in resource["instances"]:
                attributes = instance["attributes"]
                name = attributes["name"]
                location = attributes["location"]
                resource_name = sanitize_for_terraform(name)
                tf_block = f"""
resource "google_cloud_run_v2_service" "{resource_name}" {{
  project  = "{attributes['project']}"
  location = "{location}"
  name     = "{name}"
  template {{
    containers {{
      image = "gcr.io/cloudrun/placeholder"
    }}
  }}
}}
"""
                print(f"Generated resource for Cloud Run service: {name}")
        else:
            continue

        # Get or create the file handler
        if output_subdir not in file_handlers:
            resource_dir = os.path.join(output_dir, output_subdir)
            os.makedirs(resource_dir, exist_ok=True)
            tf_file_path = os.path.join(resource_dir, output_filename)
            file_handlers[output_subdir] = open(tf_file_path, "w")

        file_handlers[output_subdir].write(tf_block)

    # Close all file handlers
    for handler in file_handlers.values():
        handler.close()

    print(f"\nGenerated Terraform configurations in: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Terraform State Parser for GCP")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    parser.add_argument("--state-file-path", required=True, help="Full GCS path to the terraform.tfstate file (e.g., gs://bucket/path/to/terraform.tfstate)")
    args = parser.parse_args()

    tfstate_json = download_tfstate(args.project, args.state_file_path)
    if tfstate_json:
        generate_resources_from_state(tfstate_json)
