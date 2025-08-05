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

    for resource in tfstate_data["resources"]:
        resource_type = resource["type"]

        # We'll start by supporting only GCS buckets
        if resource_type == "google_storage_bucket":
            for instance in resource["instances"]:
                attributes = instance["attributes"]
                bucket_name = attributes["name"]
                resource_name = sanitize_for_terraform(bucket_name)

                # Create a directory for the resource type
                resource_dir = os.path.join(output_dir, "gcs")
                os.makedirs(resource_dir, exist_ok=True)
                tf_file_path = os.path.join(resource_dir, "buckets.tf")

                # Generate the resource block
                tf_block = f"""
resource "google_storage_bucket" "{resource_name}" {{
  name          = "{bucket_name}"
  project       = "{attributes['project']}"
  location      = "{attributes['location']}"
  storage_class = "{attributes['storage_class']}"
  # Note: This is a simplified representation. Other attributes
  # like versioning, lifecycle_rules, etc., are not included.
}}
"""
                with open(tf_file_path, "a") as tf_file:
                    tf_file.write(tf_block)

                print(f"Generated resource for GCS bucket: {bucket_name}")

    print(f"\nGenerated Terraform configurations in: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Terraform State Parser for GCP")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    parser.add_argument("--state-file-path", required=True, help="Full GCS path to the terraform.tfstate file (e.g., gs://bucket/path/to/terraform.tfstate)")
    args = parser.parse_args()

    tfstate_json = download_tfstate(args.project, args.state_file_path)
    if tfstate_json:
        generate_resources_from_state(tfstate_json)
