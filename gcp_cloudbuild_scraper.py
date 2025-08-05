import argparse
import os
from google.cloud.devtools import cloudbuild_v1

def sanitize_for_terraform(name):
    """Sanitizes a name for use as a Terraform resource name."""
    return name.replace('-', '_')

def generate_cloudbuild_resources(project_id, location):
    """
    Fetches all Cloud Build triggers in a project and generates Terraform
    resource blocks and import commands.
    """
    try:
        client = cloudbuild_v1.CloudBuildClient()
        parent = f"projects/{project_id}/locations/{location}"
        triggers = client.list_build_triggers(parent=parent)
    except Exception as e:
        print(f"Error connecting to GCP or fetching Cloud Build triggers: {e}")
        return

    output_dir = "generated_terraform/cloud_build"
    os.makedirs(output_dir, exist_ok=True)

    tf_file_path = os.path.join(output_dir, "triggers.tf")
    import_script_path = os.path.join(output_dir, "import.sh")

    with open(tf_file_path, "w") as tf_file, open(import_script_path, "w") as import_script:
        import_script.write("#!/bin/bash\n\n")
        import_script.write(f"# Run this script to import Cloud Build triggers into your Terraform state.\n\n")

        print(f"Found Cloud Build triggers in project '{project_id}':")
        for trigger in triggers:
            trigger_id = trigger.id
            print(f"  - {trigger.name} (ID: {trigger_id})")

            resource_name = sanitize_for_terraform(trigger.name if trigger.name else trigger_id)

            # Generate Terraform resource block
            # This is a very simplified representation. Cloud Build triggers have
            # many complex fields (e.g., build steps, substitutions).
            tf_block = f"""
resource "google_cloudbuild_trigger" "{resource_name}" {{
  project  = "{project_id}"
  location = "global" # Assuming global location
  name     = "{trigger.name}"

  # WARNING: The configuration for this trigger is complex and not fully
  # represented here. You will need to manually configure the trigger
  # details (e.g., filename, substitutions, included_files).
  # This is just a placeholder to allow for import.

  # Example placeholder for a build definition:
  filename = "cloudbuild.yaml"
}}
"""
            tf_file.write(tf_block)

            # Generate import command
            import_command = f"terraform import google_cloudbuild_trigger.{resource_name} projects/{project_id}/locations/global/triggers/{trigger_id}\n"
            import_script.write(import_command)

    print(f"\nGenerated Terraform configuration in: {tf_file_path}")
    print(f"Generated import script in: {import_script_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCP Cloud Build Scraper for Terraform")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    parser.add_argument("--location", required=True, help="The location of the Cloud Build triggers (e.g., 'global', 'us-central1')")
    args = parser.parse_args()

    generate_cloudbuild_resources(args.project, args.location)
