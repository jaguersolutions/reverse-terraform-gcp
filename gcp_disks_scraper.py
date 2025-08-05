import argparse
import os
import google.cloud.compute_v1 as compute_v1

def sanitize_for_terraform(name):
    """Sanitizes a name for use as a Terraform resource name."""
    return name.replace('-', '_')

def generate_disk_resources(project_id):
    """
    Fetches all persistent disks in a project and generates Terraform
    resource blocks and import commands.
    """
    try:
        client = compute_v1.DisksClient()
        all_disks = client.aggregated_list(project=project_id)
    except Exception as e:
        print(f"Error connecting to GCP or fetching disks: {e}")
        return

    output_dir = "generated_terraform/disks"
    os.makedirs(output_dir, exist_ok=True)

    tf_file_path = os.path.join(output_dir, "disks.tf")
    import_script_path = os.path.join(output_dir, "import.sh")

    with open(tf_file_path, "w") as tf_file, open(import_script_path, "w") as import_script:
        import_script.write("#!/bin/bash\n\n")
        import_script.write(f"# Run this script to import disks into your Terraform state.\n\n")

        print(f"Found disks in project '{project_id}':")
        for zone, response in all_disks:
            if response.disks:
                for disk in response.disks:
                    print(f"  - {disk.name} (Zone: {zone})")

                    resource_name = sanitize_for_terraform(disk.name)

                    # Generate Terraform resource block
                    tf_block = f"""
resource "google_compute_disk" "{resource_name}" {{
  name    = "{disk.name}"
  project = "{project_id}"
  zone    = "{zone.split('/')[-1]}"
  type    = "{disk.type.split('/')[-1]}"
  size    = {disk.size_gb}
}}
"""
                    tf_file.write(tf_block)

                    # Generate import command
                    import_command = f"terraform import google_compute_disk.{resource_name} {project_id}/{zone.split('/')[-1]}/{disk.name}\n"
                    import_script.write(import_command)

    print(f"\nGenerated Terraform configuration in: {tf_file_path}")
    print(f"Generated import script in: {import_script_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCP Disk Scraper for Terraform")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    args = parser.parse_args()

    generate_disk_resources(args.project)
