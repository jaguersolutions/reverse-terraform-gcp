import argparse
import os
import google.cloud.compute_v1 as compute_v1

def sanitize_for_terraform(name):
    """Sanitizes a name for use as a Terraform resource name."""
    return name.replace('-', '_')

def generate_vm_resources(project_id):
    """
    Fetches all VM instances in a project and generates Terraform resource
    blocks and import commands.
    """
    try:
        client = compute_v1.InstancesClient()
        # The list method returns a dict where the key is the zone and the value is a list of instances.
        all_instances = client.aggregated_list(project=project_id)
    except Exception as e:
        print(f"Error connecting to GCP or fetching VM instances: {e}")
        return

    output_dir = "generated_terraform/vm_instances"
    os.makedirs(output_dir, exist_ok=True)

    tf_file_path = os.path.join(output_dir, "instances.tf")
    import_script_path = os.path.join(output_dir, "import.sh")

    with open(tf_file_path, "w") as tf_file, open(import_script_path, "w") as import_script:
        import_script.write("#!/bin/bash\n\n")
        import_script.write(f"# Run this script to import VM instances into your Terraform state.\n\n")

        print(f"Found VM instances in project '{project_id}':")
        for zone, response in all_instances:
            if response.instances:
                for instance in response.instances:
                    print(f"  - {instance.name} (Zone: {zone})")

                    resource_name = sanitize_for_terraform(instance.name)

                    # Generate Terraform resource block
                    tf_block = f"""
resource "google_compute_instance" "{resource_name}" {{
  project      = "{project_id}"
  zone         = "{zone.split('/')[-1]}"
  name         = "{instance.name}"
  machine_type = "{instance.machine_type.split('/')[-1]}"

  # WARNING: This is a simplified representation. Disks, network interfaces,
  # and other configurations are not fully represented here. You will need
  # to manually configure these details. This is just a placeholder to
  # allow for import.

  boot_disk {{
    initialize_params {{
      image = "debian-cloud/debian-11" # Placeholder image
    }}
  }}

  network_interface {{
    network = "default"
  }}
}}
"""
                    tf_file.write(tf_block)

                    # Generate import command
                    import_command = f"terraform import google_compute_instance.{resource_name} {project_id}/{zone.split('/')[-1]}/{instance.name}\n"
                    import_script.write(import_command)

    print(f"\nGenerated Terraform configuration in: {tf_file_path}")
    print(f"Generated import script in: {import_script_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCP VM Instance Scraper for Terraform")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    args = parser.parse_args()

    generate_vm_resources(args.project)
