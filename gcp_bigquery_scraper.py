import argparse
import os
from google.cloud import bigquery

def sanitize_for_terraform(name):
    """Sanitizes a name for use as a Terraform resource name."""
    return name.replace('-', '_')

def generate_bigquery_resources(project_id):
    """
    Fetches all BigQuery datasets in a project and generates Terraform
    resource blocks and import commands.
    """
    try:
        client = bigquery.Client(project=project_id)
        datasets = list(client.list_datasets())
    except Exception as e:
        print(f"Error connecting to GCP or fetching BigQuery datasets: {e}")
        return

    output_dir = "generated_terraform/bigquery"
    os.makedirs(output_dir, exist_ok=True)

    tf_file_path = os.path.join(output_dir, "datasets.tf")
    import_script_path = os.path.join(output_dir, "import.sh")

    with open(tf_file_path, "w") as tf_file, open(import_script_path, "w") as import_script:
        import_script.write("#!/bin/bash\n\n")
        import_script.write(f"# Run this script to import BigQuery datasets into your Terraform state.\n\n")

        print(f"Found BigQuery datasets in project '{project_id}':")
        if datasets:
            for dataset in datasets:
                dataset_id = dataset.dataset_id
                print(f"  - {dataset_id}")

                resource_name = sanitize_for_terraform(dataset_id)

                # Generate Terraform resource block
                tf_block = f"""
resource "google_bigquery_dataset" "{resource_name}" {{
  dataset_id = "{dataset_id}"
  project    = "{project_id}"
  location   = "{dataset.location}"
}}
"""
                tf_file.write(tf_block)

                # Generate import command
                import_command = f"terraform import google_bigquery_dataset.{resource_name} {project_id}:{dataset_id}\n"
                import_script.write(import_command)

    print(f"\nGenerated Terraform configuration in: {tf_file_path}")
    print(f"Generated import script in: {import_script_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCP BigQuery Dataset Scraper for Terraform")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    args = parser.parse_args()

    generate_bigquery_resources(args.project)
