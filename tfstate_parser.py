import argparse
import json
import os
from google.cloud import storage

def sanitize_for_terraform(name):
    """Sanitizes a name for use as a Terraform resource name."""
    return name.replace('-', '_')

def download_tfstate(project_id, bucket_name):
    """Downloads the tfstate file from GCS."""
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)

    # Check for default.tfstate first, then terraform.tfstate
    blob = bucket.blob("default.tfstate")
    if not blob.exists():
        blob = bucket.blob("terraform.tfstate")
        if not blob.exists():
            print(f"Error: Neither 'default.tfstate' nor 'terraform.tfstate' found in bucket gs://{bucket_name}")
            return None

    print(f"Downloading gs://{bucket_name}/{blob.name}...")
    return json.loads(blob.download_as_string())

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
    parser.add_argument("--bucket", required=True, help="GCS bucket name for tfstate")
    args = parser.parse_args()

    tfstate_json = download_tfstate(args.project, args.bucket)
    if tfstate_json:
        generate_resources_from_state(tfstate_json)
