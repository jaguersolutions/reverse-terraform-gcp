import argparse
import os
import google.cloud.compute_v1 as compute_v1

def sanitize_for_terraform(name):
    """Sanitizes a name for use as a Terraform resource name."""
    return name.replace('-', '_')

def generate_instance_group_resources(project_id):
    """
    Fetches all instance groups in a project and generates Terraform resource
    blocks and import commands.
    """
    try:
        client = compute_v1.InstanceGroupsClient()
        all_instance_groups = client.aggregated_list(project=project_id)
    except Exception as e:
        print(f"Error connecting to GCP or fetching instance groups: {e}")
        return

    output_dir = "generated_terraform/instance_groups"
    os.makedirs(output_dir, exist_ok=True)

    tf_file_path = os.path.join(output_dir, "instance_groups.tf")
    import_script_path = os.path.join(output_dir, "import.sh")

    with open(tf_file_path, "w") as tf_file, open(import_script_path, "w") as import_script:
        import_script.write("#!/bin/bash\n\n")
        import_script.write(f"# Run this script to import instance groups into your Terraform state.\n\n")

        print(f"Found instance groups in project '{project_id}':")
        for zone, response in all_instance_groups:
            if response.instance_groups:
                for group in response.instance_groups:
                    print(f"  - {group.name} (Zone: {zone})")

                    resource_name = sanitize_for_terraform(group.name)

                    # Generate Terraform resource block
                    tf_block = f"""
resource "google_compute_instance_group" "{resource_name}" {{
  name    = "{group.name}"
  project = "{project_id}"
  zone    = "{zone.split('/')[-1]}"

  # WARNING: This is a simplified representation. The instances that are
  # members of this group are not included here. You will need to add
  # them manually or use a separate script to manage group membership.
}}
"""
                    tf_file.write(tf_block)

                    # Generate import command
                    import_command = f"terraform import google_compute_instance_group.{resource_name} {project_id}/{zone.split('/')[-1]}/{group.name}\n"
                    import_script.write(import_command)

    print(f"\nGenerated Terraform configuration in: {tf_file_path}")
    print(f"Generated import script in: {import_script_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCP Instance Group Scraper for Terraform")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    args = parser.parse_args()

    generate_instance_group_resources(args.project)
