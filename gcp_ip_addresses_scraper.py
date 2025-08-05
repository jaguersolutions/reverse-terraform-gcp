import argparse
import os
import google.cloud.compute_v1 as compute_v1

def sanitize_for_terraform(name):
    """Sanitizes a name for use as a Terraform resource name."""
    return name.replace('-', '_')

def generate_address_resources(project_id):
    """
    Fetches all addresses in a project and generates Terraform resource
    blocks and import commands.
    """
    try:
        client = compute_v1.AddressesClient()
        all_addresses = client.aggregated_list(project=project_id)
    except Exception as e:
        print(f"Error connecting to GCP or fetching addresses: {e}")
        return

    output_dir = "generated_terraform/ip_addresses"
    os.makedirs(output_dir, exist_ok=True)

    tf_file_path = os.path.join(output_dir, "addresses.tf")
    import_script_path = os.path.join(output_dir, "import.sh")

    with open(tf_file_path, "w") as tf_file, open(import_script_path, "w") as import_script:
        import_script.write("#!/bin/bash\n\n")
        import_script.write(f"# Run this script to import addresses into your Terraform state.\n\n")

        print(f"Found addresses in project '{project_id}':")
        for region, response in all_addresses:
            if response.addresses:
                for address in response.addresses:
                    print(f"  - {address.name} (Region: {region})")

                    resource_name = sanitize_for_terraform(address.name)

                    # Generate Terraform resource block
                    tf_block = f"""
resource "google_compute_address" "{resource_name}" {{
  name    = "{address.name}"
  project = "{project_id}"
  region  = "{region.split('/')[-1]}"
}}
"""
                    tf_file.write(tf_block)

                    # Generate import command
                    import_command = f"terraform import google_compute_address.{resource_name} {project_id}/{region.split('/')[-1]}/{address.name}\n"
                    import_script.write(import_command)

    print(f"\nGenerated Terraform configuration in: {tf_file_path}")
    print(f"Generated import script in: {import_script_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCP Address Scraper for Terraform")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    args = parser.parse_args()

    generate_address_resources(args.project)
