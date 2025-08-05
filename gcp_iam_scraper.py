import argparse
import os
from google.cloud import resourcemanager_v3

def sanitize_for_terraform(name):
    """Sanitizes a name for use as a Terraform resource name."""
    return name.replace('-', '_').replace('.', '_').replace('@', '_')

def generate_iam_resources(project_id):
    """
    Fetches the IAM policy for a project and generates Terraform resource
    blocks for each binding.
    """
    try:
        client = resourcemanager_v3.ProjectsClient()
        policy = client.get_iam_policy(resource=f"projects/{project_id}")
    except Exception as e:
        print(f"Error connecting to GCP or fetching IAM policy: {e}")
        return

    output_dir = "generated_terraform/iam"
    os.makedirs(output_dir, exist_ok=True)

    tf_file_path = os.path.join(output_dir, "iam_bindings.tf")
    import_script_path = os.path.join(output_dir, "import.sh")

    with open(tf_file_path, "w") as tf_file, open(import_script_path, "w") as import_script:
        import_script.write("#!/bin/bash\n\n")
        import_script.write(f"# Run this script to import IAM bindings into your Terraform state.\n\n")

        print(f"Found IAM bindings in project '{project_id}':")
        for binding in policy.bindings:
            role = binding.role
            members = binding.members

            # We will create a separate resource for each member in a binding
            # to avoid issues with managing the whole list.
            for member in members:
                print(f"  - Role: {role}, Member: {member}")

                # Sanitize role and member for the resource name
                sanitized_role = sanitize_for_terraform(role.split('/')[-1])
                sanitized_member = sanitize_for_terraform(member.split(':')[-1])
                resource_name = f"{sanitized_role}_{sanitized_member}"

                # Generate Terraform resource block
                tf_block = f"""
resource "google_project_iam_member" "{resource_name}" {{
  project = "{project_id}"
  role    = "{role}"
  member  = "{member}"
}}
"""
                tf_file.write(tf_block)

                # Generate import command
                import_command = f"terraform import 'google_project_iam_member.{resource_name}' 'projects/{project_id} {role} {member}'\n"
                import_script.write(import_command)

    print(f"\nGenerated Terraform configuration in: {tf_file_path}")
    print(f"Generated import script in: {import_script_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCP IAM Scraper for Terraform")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    args = parser.parse_args()

    generate_iam_resources(args.project)
