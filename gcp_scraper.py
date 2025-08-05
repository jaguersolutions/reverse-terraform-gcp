import argparse
import os
from google.cloud import storage
from google.cloud import secretmanager
from google.cloud import build_v1
from google.cloud import run_v2

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


def generate_cloudbuild_resources(project_id):
    """
    Fetches all Cloud Build triggers in a project and generates Terraform
    resource blocks and import commands.
    """
    try:
        client = build_v1.CloudBuildClient()
        parent = f"projects/{project_id}"
        # Note: Cloud Build API requires a location. Using 'global' as a default.
        # This might need to be adjusted if triggers are in other locations.
        triggers = client.list_build_triggers(project_id=project_id, location="global")
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
    parser = argparse.ArgumentParser(description="GCP Resource Scraper for Terraform")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    args = parser.parse_args()

    print("--- Scraping GCS Buckets ---")
    generate_gcs_resources(args.project)
    print("\n--- Scraping Secret Manager Secrets ---")
    generate_secret_manager_resources(args.project)
    print("\n--- Scraping Cloud Build Triggers ---")
    generate_cloudbuild_resources(args.project)
    print("\n--- Scraping Cloud Run Services ---")
    generate_cloudrun_resources(args.project)
