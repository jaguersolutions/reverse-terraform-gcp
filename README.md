# GCP Reverse Terraform Generator

This tool helps you generate Terraform code from your existing Google Cloud Platform (GCP) resources. It's designed for teams who need to bring an existing, manually-created GCP infrastructure under Terraform management.

The script can work in two modes:
1.  **Scan Mode**: It scans your GCP project for active resources and generates Terraform HCL code and import commands for them.
2.  **State-Parse Mode**: If you already have a Terraform state file in a GCS bucket, it can parse this file and generate the corresponding HCL resource blocks.

## Prerequisites

Before you begin, ensure you have the following tools installed and configured:

- **gcloud CLI**: The command-line tool for Google Cloud.
- **Terraform**: The infrastructure-as-code tool.
- **Python 3**: Along with the `pip` package manager.

You will also need a GCP Service Account with sufficient permissions to read the resources in your project. You should have the JSON key file for this service account downloaded to your local machine.

## How to Use

1.  **Clone this repository** to your local machine.

2.  **Make the script executable**:
    ```bash
    chmod +x reverse_terraform.sh
    ```

3.  **Run the script**:
    ```bash
    ./reverse_terraform.sh
    ```

4.  **Follow the prompts**: The script will ask for the following information:
    - Your **GCP Project ID**.
    - The **absolute path** to your GCP Service Account JSON key file.
    - The name of the **GCS bucket** where a `terraform.tfstate` file might be stored.

## What to Expect

The script will first check the specified GCS bucket for a Terraform state file.

- **If a state file is found**, the script will parse it and generate Terraform resource blocks for the resources defined in the state.
- **If no state file is found**, the script will proceed to scan your GCP project for resources. Currently, it supports scanning for GCS buckets.

All generated files will be placed in a `generated_terraform` directory. Inside this directory, you will find:
- Subdirectories for each resource type (e.g., `gcs/`).
- Terraform `.tf` files containing the resource blocks.
- A `README.md` with instructions on how to initialize Terraform, import the resources, and verify your setup.
- For scanned resources, you will also find `import.sh` scripts to help you run the necessary `terraform import` commands.

## Important Notes

- The generated code is a starting point. It may not capture all the attributes of your resources. You should review the generated files carefully and make any necessary adjustments.
- The resource scanner is currently limited to GCS buckets. Support for more resource types (like Compute Engine VMs, GKE clusters, etc.) can be added by extending the `gcp_scraper.py` script.
