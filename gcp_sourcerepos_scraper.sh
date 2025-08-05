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

# --- Dependency Check ---
check_dependency "gcloud"
check_dependency "jq"

# --- User Input ---
if [ -z "$1" ]; then
    echo -e "${RED}Usage: $0 <project_id>${NC}"
    exit 1
fi
project_id=$1

# --- Scrape Source Repositories ---
echo -e "${YELLOW}Scraping Cloud Source Repositories from project '$project_id'...${NC}"
repos_json=$(gcloud source repos list --project="$project_id" --format=json)
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to list source repositories. Please check your permissions.${NC}"
    exit 1
fi

if [ -z "$repos_json" ] || [ "$repos_json" == "[]" ]; then
    echo -e "${GREEN}No source repositories found in project '$project_id'.${NC}"
    exit 0
fi

# --- Generate Terraform Files ---
output_dir="generated_terraform/source_repositories"
mkdir -p "$output_dir"

tf_file_path="$output_dir/repos.tf"
import_script_path="$output_dir/import.sh"

# Clear existing files
> "$tf_file_path"
> "$import_script_path"
chmod +x "$import_script_path"

echo "#!/bin/bash" >> "$import_script_path"
echo "# Run this script to import Cloud Source Repositories into your Terraform state." >> "$import_script_path"
echo "" >> "$import_script_path"

echo "Found Cloud Source Repositories:"
echo "$repos_json" | jq -r '.[] | .name' | while read -r repo_name_full; do
    repo_name=$(basename "$repo_name_full")
    echo "  - $repo_name"

    # Sanitize for Terraform resource name
    resource_name=$(echo "$repo_name" | tr '-' '_')

    # Generate Terraform resource block
    tf_block=$(cat <<EOF

resource "google_sourcerepo_repository" "$resource_name" {
  name    = "$repo_name"
  project = "$project_id"
}
EOF
)
    echo "$tf_block" >> "$tf_file_path"

    # Generate import command
    import_command="terraform import google_sourcerepo_repository.$resource_name $repo_name_full"
    echo "$import_command" >> "$import_script_path"
done

echo -e "\n${GREEN}Generated Terraform configuration in: $tf_file_path${NC}"
echo -e "${GREEN}Generated import script in: $import_script_path${NC}"
