# SyncSamlMetadata
Lambda function to synchronize IAM SAML metadata from a URL

# Description
Keeps AWS IAM SAML identity provider's (IDP) metadata document in sync.
Uses AWS Parameter Store parameters for IDP data. CloudFormation
template creates one IDP config parameter but others can be added.

# Using the CloudFormation template
1. Download [syncSaml.yaml](./syncSaml.yaml)
1. From the AWS Console, search or browse to CloudFormation
1. From the Create Stack button, choose "With new resources (standard)"
1. Choose "Upload a template file"
1. Select syncSaml.yaml from your local download
1. Click Next
1. Enter a name for the stack
1. Click Next
1. Click Next
1. Check the "I acknowledge that AWS CloudFormation might create IAM resources with custom names." checkbox
1. Click Create Stack

# CloudFormation parameters
* **Parameter Store path prefix** (i.e. folder path): the "folder" the Lambda function will be granted permissions
to read and will search for parameters
* **Parameter Store item name**: the first parameter to create under the path prefix
* **JSON value that defines the SAML metadata**: JSON for the first parameter. Expected JSON
    * **Name**: friendly name of the IDP
    * **Source**: URL to the IDP metadata
    * **Destination**: Name of the IAM identity provider to create/update
    * **AppendEntityId** (optional): Value to append to the EntityId in the metadata. Required for some IDPs.
