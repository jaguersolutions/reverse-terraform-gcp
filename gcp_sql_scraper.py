import argparse
import os
from googleapiclient import discovery

def sanitize_for_terraform(name):
    """Sanitizes a name for use as a Terraform resource name."""
    return name.replace('-', '_')

def generate_sql_resources(project_id):
    """
    Fetches all Cloud SQL instances in a project and generates Terraform
    resource blocks and import commands.
    """
    try:
        service = discovery.build('sqladmin', 'v1beta4')
        req = service.instances().list(project=project_id)
        resp = req.execute()
    except Exception as e:
        print(f"Error connecting to GCP or fetching Cloud SQL instances: {e}")
        return

    output_dir = "generated_terraform/sql"
    os.makedirs(output_dir, exist_ok=True)

    tf_file_path = os.path.join(output_dir, "instances.tf")
    import_script_path = os.path.join(output_dir, "import.sh")

    with open(tf_file_path, "w") as tf_file, open(import_script_path, "w") as import_script:
        import_script.write("#!/bin/bash\n\n")
        import_script.write(f"# Run this script to import Cloud SQL instances into your Terraform state.\n\n")

        print(f"Found Cloud SQL instances in project '{project_id}':")
        if 'items' in resp:
            for instance in resp['items']:
                instance_name = instance['name']
                print(f"  - {instance_name}")

                resource_name = sanitize_for_terraform(instance_name)

                # Generate Terraform resource block
                tf_block = f"""
resource "google_sql_database_instance" "{resource_name}" {{
  name             = "{instance_name}"
  project          = "{project_id}"
  database_version = "{instance['databaseVersion']}"
  region           = "{instance['region']}"

  settings {{
    tier = "{instance['settings']['tier']}"
  }}
}}
"""
                tf_file.write(tf_block)

                # Generate import command
                import_command = f"terraform import google_sql_database_instance.{resource_name} {project_id}/{instance_name}\n"
                import_script.write(import_command)

    print(f"\nGenerated Terraform configuration in: {tf_file_path}")
    print(f"Generated import script in: {import_script_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCP SQL Instance Scraper for Terraform")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    args = parser.parse_args()

    generate_sql_resources(args.project)
