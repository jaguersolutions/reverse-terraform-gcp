import argparse
import os
from google.iam.admin_v1 import IAMClient

def sanitize_for_terraform(name):
    """Sanitizes a name for use as a Terraform resource name."""
    return name.replace('-', '_').replace('.', '_').replace('@', '_')

def generate_service_account_resources(project_id):
    """
    Fetches all service accounts in a project and generates Terraform
    resource blocks and import commands.
    """
    try:
        client = IAMClient()
        parent = f"projects/{project_id}"
        service_accounts = client.list_service_accounts(name=parent)
    except Exception as e:
        print(f"Error connecting to GCP or fetching service accounts: {e}")
        return

    output_dir = "generated_terraform/service_accounts"
    os.makedirs(output_dir, exist_ok=True)

    tf_file_path = os.path.join(output_dir, "service_accounts.tf")
    import_script_path = os.path.join(output_dir, "import.sh")

    with open(tf_file_path, "w") as tf_file, open(import_script_path, "w") as import_script:
        import_script.write("#!/bin/bash\n\n")
        import_script.write(f"# Run this script to import service accounts into your Terraform state.\n\n")

        print(f"Found service accounts in project '{project_id}':")
        for sa in service_accounts:
            account_id = sa.email.split('@')[0]
            print(f"  - {sa.email}")

            resource_name = sanitize_for_terraform(account_id)

            # Generate Terraform resource block
            tf_block = f"""
resource "google_service_account" "{resource_name}" {{
  project      = "{project_id}"
  account_id   = "{account_id}"
  display_name = "{sa.display_name}"
}}
"""
            tf_file.write(tf_block)

            # Generate import command
            import_command = f"terraform import google_service_account.{resource_name} {sa.name}\n"
            import_script.write(import_command)

    print(f"\nGenerated Terraform configuration in: {tf_file_path}")
    print(f"Generated import script in: {import_script_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCP Service Account Scraper for Terraform")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    args = parser.parse_args()

    generate_service_account_resources(args.project)
