# © 2025 Numantic Solutions LLC
# MIT License
#
# Grant IAM permissions needed for the RAG agent to access the Search Engine
# Note: this script requires that the Identity and Access Management (IAM) API and
# Cloud Resource Manager APIs be enabled


import os
import sys
from google.cloud.iam_admin_v1 import IAMClient
from google.cloud.iam_admin_v1.types import Role, CreateRoleRequest, GetRoleRequest
from google.cloud import resourcemanager_v3
from google.api_core import exceptions
from google.iam.v1 import policy_pb2, iam_policy_pb2

# --- Configuration: UPDATED FOR SEARCH APP ---
ROLE_ID = "vaisEngineQueryRole"
ROLE_TITLE = "Vertex AI Search Engine Query Role"
# The required permission to query a Search App (engine)
RAG_PERMISSION = "discoveryengine.servingConfigs.search"
# The description reflects the change
ROLE_DESCRIPTION = "Custom role with permission to query the Vertex AI Search Engine."


def ensure_custom_role(project_id: str) -> str:
    """Creates a custom IAM role if it doesn't exist."""
    role_name = f"projects/{project_id}/roles/{ROLE_ID}"
    iam_client = IAMClient()

    print(f"🛠️ Checking/ensuring custom role '{ROLE_ID}'...")

    try:
        # Check if the role exists
        request = GetRoleRequest(name=role_name)
        iam_client.get_role(request=request)
        print(f"Custom role '{ROLE_ID}' already exists.")
        return ROLE_ID
    except exceptions.NotFound:
        # Create the custom role
        print(f"Role '{ROLE_ID}' not found. Creating it...")

        new_role = Role(
            title=ROLE_TITLE,
            description=ROLE_DESCRIPTION,
            included_permissions=[RAG_PERMISSION],
            stage="BETA",
        )
        request = CreateRoleRequest(
            parent=f"projects/{project_id}",
            role_id=ROLE_ID,
            role=new_role,
        )
        iam_client.create_role(request=request)
        print(f"Custom role '{ROLE_ID}' created successfully.")
        return ROLE_ID
    except Exception as e:
        print(f"Error managing custom role: {e}")
        sys.exit(1)

def grant_iam_binding(project_id: str, project_number: str, custom_role_id: str):
    """Fetches the project IAM policy, adds the binding, and sets the updated policy."""

    # The service account remains the same, as it's the Vertex AI Service Agent for the project
    # The 're' (Reasoning Engine) Service Account is generally used for RAG functions in Vertex AI
    service_account = f"service-{project_number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
    member = f"serviceAccount:{service_account}"
    role_path = f"projects/{project_id}/roles/{custom_role_id}"
    resource_name = f"projects/{project_id}"

    print(f"\nGranting role '{custom_role_id}' to: {member}...")

    rm_client = resourcemanager_v3.ProjectsClient()

    try:
        # 1. Get the current IAM Policy (Read)
        policy_request = iam_policy_pb2.GetIamPolicyRequest(resource=resource_name)
        policy = rm_client.get_iam_policy(request=policy_request)

        # 2. Modify the Policy (Add/Update Binding)
        target_binding = next((b for b in policy.bindings if b.role == role_path), None)

        if target_binding:
            if member not in target_binding.members:
                target_binding.members.append(member)
                print(f"Updated existing binding: added {member}.")
            else:
                print(f"Binding for {member} with role {custom_role_id} is already present.")
        else:
            new_binding = policy_pb2.Binding(
                role=role_path,
                members=[member]
            )
            policy.bindings.append(new_binding)
            print(f"Added new binding for role {custom_role_id}.")

        # 3. Set the updated IAM Policy (Write)
        set_policy_request = iam_policy_pb2.SetIamPolicyRequest(
            resource=resource_name,
            policy=policy,
        )
        rm_client.set_iam_policy(request=set_policy_request)

        print(f"Permissions granted successfully for project {project_id}.")
        print("The Vertex AI Service Agent can now query your Search Engine.")

    except Exception as e:
        print(f"Error setting IAM policy. Ensure you have the 'roles/resourcemanager.projectIamAdmin' role. Error: {e}")
        sys.exit(1)


# --- Main Execution ---
if __name__ == "__main__":

    # Numantic utilities
    try:
        if 'USER' in os.environ.keys() and os.environ['USER'] == 'numantic':
            utils_path = "/Users/numantic/Documents/GitHub/utilities/.."
        elif 'USER' in os.environ.keys() and os.environ['USER'] == 'stephengodfrey':
            utils_path = "/Users/stephengodfrey/Documents/Workbench/Numantic/utilities/.."
        else:
            utils_path = "utilities/"
    except:
        utils_path = "utilities/"

    sys.path.insert(0, utils_path)

    # Authenticate
    from utilities.osa_tools.authentication import ApiAuthentication
    api_configs = ApiAuthentication(client="CCC")

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    project_number = os.getenv("GOOGLE_CLOUD_PROJECT_ID")

    # 2. Ensure Custom Role exists
    custom_role_id = ensure_custom_role(project_id)

    # 3. Grant Policy Binding
    # Note: The third parameter is removed as it's no longer used in the grant function.
    grant_iam_binding(project_id, project_number, custom_role_id)