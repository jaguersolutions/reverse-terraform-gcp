#!/bin/bash

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Helper Functions ---
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}Error: '$1' is not installed. Please install it to continue.${NC}"
        exit 1
    fi
}

echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN} Welcome to the GCP Reverse Terraform Generator ${NC}"
echo -e "${GREEN}=============================================${NC}"
echo "This script will help you generate Terraform code for your existing GCP resources."
echo "It can either scan your project for resources or use an existing Terraform state file in GCS."
echo

# --- Dependency Check ---
echo -e "${YELLOW}Checking for required dependencies...${NC}"
check_dependency "gcloud"
check_dependency "terraform"
check_dependency "python3"
echo -e "${GREEN}All dependencies are satisfied.${NC}"
echo

# --- User Input ---
echo -e "${YELLOW}Please provide the following information:${NC}"

read -p "Enter your GCP Project ID: " gcp_project_id
while [ -z "$gcp_project_id" ]; do
    echo -e "${RED}Project ID cannot be empty.${NC}"
    read -p "Enter your GCP Project ID: " gcp_project_id
done

read -p "Enter the absolute path to your GCP Service Account JSON file: " gcp_sa_json_path
while [ ! -f "$gcp_sa_json_path" ]; do
    echo -e "${RED}File not found. Please enter a valid path.${NC}"
    read -p "Enter the absolute path to your GCP Service Account JSON file: " gcp_sa_json_path
done

read -p "Enter the GCS bucket name where your terraform.tfstate might be stored (e.g., my-tf-state-bucket): " gcs_bucket_name
while [ -z "$gcs_bucket_name" ]; do
    echo -e "${RED}GCS bucket name cannot be empty.${NC}"
    read -p "Enter the GCS bucket name where your terraform.tfstate might be stored: " gcs_bucket_name
done

echo
echo -e "${GREEN}Thank you! I have all the information I need.${NC}"
echo

# --- Authenticate with GCP ---
echo -e "${YELLOW}Authenticating with GCP using the provided service account...${NC}"
gcloud auth activate-service-account --key-file="$gcp_sa_json_path"
if [ $? -ne 0 ]; then
    echo -e "${RED}GCP authentication failed. Please check the path to your service account file and its permissions.${NC}"
    exit 1
fi

gcloud config set project "$gcp_project_id"
echo -e "${GREEN}Successfully authenticated and set project to '$gcp_project_id'.${NC}"
echo

# --- Check for Terraform State File ---
echo -e "${YELLOW}Searching for 'terraform.tfstate' or 'default.tfstate' in gs://${gcs_bucket_name}...${NC}"
tfstate_path=$(gsutil ls -r "gs://${gcs_bucket_name}/**/terraform.tfstate" | head -n 1)
if [ -z "$tfstate_path" ]; then
    tfstate_path=$(gsutil ls -r "gs://${gcs_bucket_name}/**/default.tfstate" | head -n 1)
fi

if [ -n "$tfstate_path" ]; then
    echo -e "${GREEN}Found Terraform state file at: $tfstate_path${NC}"
    echo -e "${YELLOW}Parsing the state file...${NC}"

    # --- Install Python Dependencies ---
    echo -e "${YELLOW}Installing Python dependencies from requirements.txt...${NC}"
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install Python dependencies. Please check your Python environment.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Python dependencies installed successfully.${NC}"

    # --- Run tfstate parser ---
    python3 tfstate_parser.py --project "$gcp_project_id" --state-file-path "$tfstate_path"
    echo -e "${GREEN}Terraform state parsing complete.${NC}"
else
    echo -e "${YELLOW}No existing Terraform state file found. Scanning GCP project for resources...${NC}"

    # --- Install Python Dependencies ---
    echo -e "${YELLOW}Installing Python dependencies from requirements.txt...${NC}"
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install Python dependencies. Please check your Python environment.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Python dependencies installed successfully.${NC}"

    # --- Run GCP Scraper ---
    echo -e "${YELLOW}Running the GCP resource scraper...${NC}"
    python3 gcp_scraper.py --project "$gcp_project_id"

    echo -e "${GREEN}Resource scraping complete.${NC}"
fi

# --- Generate README ---
echo -e "${YELLOW}Generating README.md for the infrastructure...${NC}"
python3 readme_generator.py
echo -e "${GREEN}README.md generated successfully.${NC}"

echo -e "\n${GREEN}All done! Please review the generated files in the 'generated_terraform' directory.${NC}"
