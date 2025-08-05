import argparse
import os
from google.cloud import storage

def sanitize_for_terraform(name):
    """Sanitizes a name for use as a Terraform resource name."""
    return name.replace('-', '_')

def generate_gcs_resources(project_id):
    """
    Fetches all GCS buckets in a project and generates Terraform resource
    blocks and import commands.
    """
    try:
        storage_client = storage.Client(project=project_id)
        buckets = storage_client.list_buckets()
    except Exception as e:
        print(f"Error connecting to GCP or fetching buckets: {e}")
        return

    output_dir = "generated_terraform/gcs"
    os.makedirs(output_dir, exist_ok=True)

    tf_file_path = os.path.join(output_dir, "buckets.tf")
    import_script_path = os.path.join(output_dir, "import.sh")

    with open(tf_file_path, "w") as tf_file, open(import_script_path, "w") as import_script:
        import_script.write("#!/bin/bash\n\n")
        import_script.write(f"# Run this script to import GCS buckets into your Terraform state.\n\n")

        print(f"Found buckets in project '{project_id}':")
        for bucket in buckets:
            print(f"  - {bucket.name}")

            resource_name = sanitize_for_terraform(bucket.name)

            # Generate Terraform resource block
            tf_block = f"""
resource "google_storage_bucket" "{resource_name}" {{
  name          = "{bucket.name}"
  project       = "{project_id}"
  location      = "{bucket.location}"
  storage_class = "{bucket.storage_class}"
  # Note: Additional attributes like versioning, lifecycle rules, etc.,
  # are not yet supported by this script. You may need to add them manually.
}}
"""
            tf_file.write(tf_block)

            # Generate import command
            import_command = f"terraform import google_storage_bucket.{resource_name} {bucket.name}\n"
            import_script.write(import_command)

    print(f"\nGenerated Terraform configuration in: {tf_file_path}")
    print(f"Generated import script in: {import_script_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCP GCS Bucket Scraper for Terraform")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    args = parser.parse_args()

    generate_gcs_resources(args.project)
