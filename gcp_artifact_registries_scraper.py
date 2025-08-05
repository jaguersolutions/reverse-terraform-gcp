import argparse
import os
from google.cloud import artifactregistry_v1

def sanitize_for_terraform(name):
    """Sanitizes a name for use as a Terraform resource name."""
    return name.replace('-', '_')

def generate_artifact_registry_resources(project_id):
    """
    Fetches all Artifact Registry repositories in a project and generates
    Terraform resource blocks and import commands.
    """
    try:
        client = artifactregistry_v1.ArtifactRegistryClient()
        parent = f"projects/{project_id}/locations/-"
        repos = client.list_repositories(parent=parent)
    except Exception as e:
        print(f"Error connecting to GCP or fetching Artifact Registry repositories: {e}")
        return

    output_dir = "generated_terraform/artifact_registries"
    os.makedirs(output_dir, exist_ok=True)

    tf_file_path = os.path.join(output_dir, "registries.tf")
    import_script_path = os.path.join(output_dir, "import.sh")

    with open(tf_file_path, "w") as tf_file, open(import_script_path, "w") as import_script:
        import_script.write("#!/bin/bash\n\n")
        import_script.write(f"# Run this script to import Artifact Registry repositories into your Terraform state.\n\n")

        print(f"Found Artifact Registry repositories in project '{project_id}':")
        for repo in repos:
            repo_name = repo.name.split("/")[-1]
            location = repo.name.split("/")[-3]
            print(f"  - {repo_name} (Location: {location})")

            resource_name = sanitize_for_terraform(repo_name)

            # Generate Terraform resource block
            tf_block = f"""
resource "google_artifact_registry_repository" "{resource_name}" {{
  project       = "{project_id}"
  location      = "{location}"
  repository_id = "{repo_name}"
  format        = "{repo.format_.name}"
}}
"""
            tf_file.write(tf_block)

            # Generate import command
            import_command = f"terraform import google_artifact_registry_repository.{resource_name} {repo.name}\n"
            import_script.write(import_command)

    print(f"\nGenerated Terraform configuration in: {tf_file_path}")
    print(f"Generated import script in: {import_script_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCP Artifact Registry Scraper for Terraform")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    args = parser.parse_args()

    generate_artifact_registry_resources(args.project)
