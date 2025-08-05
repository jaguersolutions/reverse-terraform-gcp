import argparse
import os
from google.cloud import run_v2

def sanitize_for_terraform(name):
    """Sanitizes a name for use as a Terraform resource name."""
    return name.replace('-', '_')

def generate_cloudrun_resources(project_id):
    """
    Fetches all Cloud Run services in a project and generates Terraform
    resource blocks and import commands.
    """
    try:
        client = run_v2.ServicesClient()
        parent = f"projects/{project_id}/locations/-"
        services = client.list_services(parent=parent)
    except Exception as e:
        print(f"Error connecting to GCP or fetching Cloud Run services: {e}")
        return

    output_dir = "generated_terraform/cloud_run"
    os.makedirs(output_dir, exist_ok=True)

    tf_file_path = os.path.join(output_dir, "services.tf")
    import_script_path = os.path.join(output_dir, "import.sh")

    with open(tf_file_path, "w") as tf_file, open(import_script_path, "w") as import_script:
        import_script.write("#!/bin/bash\n\n")
        import_script.write(f"# Run this script to import Cloud Run services into your Terraform state.\n\n")

        print(f"Found Cloud Run services in project '{project_id}':")
        for service in services:
            service_name = service.name.split("/")[-1]
            location = service.name.split("/")[-3]
            print(f"  - {service_name} (Location: {location})")

            resource_name = sanitize_for_terraform(service_name)

            # Generate Terraform resource block
            # This is a very simplified representation.
            tf_block = f"""
resource "google_cloud_run_v2_service" "{resource_name}" {{
  project  = "{project_id}"
  location = "{location}"
  name     = "{service_name}"

  # WARNING: The configuration for this service is complex and not fully
  # represented here. You will need to manually configure the template,
  # traffic, etc. This is just a placeholder to allow for import.

  template {{
    containers {{
      image = "gcr.io/cloudrun/placeholder" # Placeholder image
    }}
  }}
}}
"""
            tf_file.write(tf_block)

            # Generate import command
            import_command = f"terraform import google_cloud_run_v2_service.{resource_name} projects/{project_id}/locations/{location}/services/{service_name}\n"
            import_script.write(import_command)

    print(f"\nGenerated Terraform configuration in: {tf_file_path}")
    print(f"Generated import script in: {import_script_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCP Cloud Run Scraper for Terraform")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    args = parser.parse_args()

    generate_cloudrun_resources(args.project)
