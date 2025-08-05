import argparse
import os
from google.cloud import secretmanager

def sanitize_for_terraform(name):
    """Sanitizes a name for use as a Terraform resource name."""
    return name.replace('-', '_')

def generate_secret_manager_resources(project_id):
    """
    Fetches all secrets in a project and generates Terraform resource
    blocks and import commands.
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        parent = f"projects/{project_id}"
        secrets = client.list_secrets(request={"parent": parent})
    except Exception as e:
        print(f"Error connecting to GCP or fetching secrets: {e}")
        return

    output_dir = "generated_terraform/secret_manager"
    os.makedirs(output_dir, exist_ok=True)

    tf_file_path = os.path.join(output_dir, "secrets.tf")
    import_script_path = os.path.join(output_dir, "import.sh")

    with open(tf_file_path, "w") as tf_file, open(import_script_path, "w") as import_script:
        import_script.write("#!/bin/bash\n\n")
        import_script.write(f"# Run this script to import secrets into your Terraform state.\n\n")

        print(f"Found secrets in project '{project_id}':")
        for secret in secrets:
            secret_id = secret.name.split("/")[-1]
            print(f"  - {secret_id}")

            resource_name = sanitize_for_terraform(secret_id)

            # Generate Terraform resource block
            tf_block = f"""
resource "google_secret_manager_secret" "{resource_name}" {{
  project   = "{project_id}"
  secret_id = "{secret_id}"

  replication {{
    automatic = true
  }}

  # Note: This is a simplified representation. Other attributes
  # like labels, rotation, etc., are not included.
}}
"""
            tf_file.write(tf_block)

            # Generate import command
            import_command = f"terraform import google_secret_manager_secret.{resource_name} projects/{project_id}/secrets/{secret_id}\n"
            import_script.write(import_command)

    print(f"\nGenerated Terraform configuration in: {tf_file_path}")
    print(f"Generated import script in: {import_script_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCP Secret Manager Scraper for Terraform")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    args = parser.parse_args()

    generate_secret_manager_resources(args.project)
