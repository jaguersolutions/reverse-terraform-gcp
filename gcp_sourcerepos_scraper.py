import argparse
import os
from google.cloud import sourcerepo_v1

def sanitize_for_terraform(name):
    """Sanitizes a name for use as a Terraform resource name."""
    return name.replace('-', '_')

def generate_sourcerepo_resources(project_id):
    """
    Fetches all Cloud Source Repositories in a project and generates Terraform
    resource blocks and import commands.
    """
    try:
        client = sourcerepo_v1.SourceRepoClient()
        parent = f"projects/{project_id}"
        repos = client.list_repos(name=parent)
    except Exception as e:
        print(f"Error connecting to GCP or fetching Cloud Source Repositories: {e}")
        return

    output_dir = "generated_terraform/source_repositories"
    os.makedirs(output_dir, exist_ok=True)

    tf_file_path = os.path.join(output_dir, "repos.tf")
    import_script_path = os.path.join(output_dir, "import.sh")

    with open(tf_file_path, "w") as tf_file, open(import_script_path, "w") as import_script:
        import_script.write("#!/bin/bash\n\n")
        import_script.write(f"# Run this script to import Cloud Source Repositories into your Terraform state.\n\n")

        print(f"Found Cloud Source Repositories in project '{project_id}':")
        for repo in repos:
            repo_name = repo.name.split("/")[-1]
            print(f"  - {repo_name}")

            resource_name = sanitize_for_terraform(repo_name)

            # Generate Terraform resource block
            tf_block = f"""
resource "google_sourcerepo_repository" "{resource_name}" {{
  name    = "{repo_name}"
  project = "{project_id}"
}}
"""
            tf_file.write(tf_block)

            # Generate import command
            import_command = f"terraform import google_sourcerepo_repository.{resource_name} {repo.name}\n"
            import_script.write(import_command)

    print(f"\nGenerated Terraform configuration in: {tf_file_path}")
    print(f"Generated import script in: {import_script_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCP Cloud Source Repositories Scraper for Terraform")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    args = parser.parse_args()

    generate_sourcerepo_resources(args.project)
