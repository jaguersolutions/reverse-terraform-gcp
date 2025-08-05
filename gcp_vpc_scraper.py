import argparse
import os
import google.cloud.compute_v1 as compute_v1

def sanitize_for_terraform(name):
    """Sanitizes a name for use as a Terraform resource name."""
    return name.replace('-', '_')

def generate_vpc_resources(project_id):
    """
    Fetches all VPC networks in a project and generates Terraform resource
    blocks and import commands.
    """
    try:
        client = compute_v1.NetworksClient()
        networks = client.list(project=project_id)
    except Exception as e:
        print(f"Error connecting to GCP or fetching VPC networks: {e}")
        return

    output_dir = "generated_terraform/vpc"
    os.makedirs(output_dir, exist_ok=True)

    tf_file_path = os.path.join(output_dir, "vpcs.tf")
    import_script_path = os.path.join(output_dir, "import.sh")

    with open(tf_file_path, "w") as tf_file, open(import_script_path, "w") as import_script:
        import_script.write("#!/bin/bash\n\n")
        import_script.write(f"# Run this script to import VPC networks into your Terraform state.\n\n")

        print(f"Found VPC networks in project '{project_id}':")
        for network in networks:
            print(f"  - {network.name}")

            resource_name = sanitize_for_terraform(network.name)

            # Generate Terraform resource block
            tf_block = f"""
resource "google_compute_network" "{resource_name}" {{
  name                    = "{network.name}"
  project                 = "{project_id}"
  auto_create_subnetworks = {str(network.auto_create_subnetworks).lower()}
}}
"""
            tf_file.write(tf_block)

            # Generate import command
            import_command = f"terraform import google_compute_network.{resource_name} {network.name}\n"
            import_script.write(import_command)

    print(f"\nGenerated Terraform configuration in: {tf_file_path}")
    print(f"Generated import script in: {import_script_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCP VPC Network Scraper for Terraform")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    args = parser.parse_args()

    generate_vpc_resources(args.project)
