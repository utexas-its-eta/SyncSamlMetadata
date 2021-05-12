# SyncSamlMetadata
Lambda function to synchronize IAM SAML metadata from a URL

# Description
Keeps AWS IAM SAML identity provider's (IDP) metadata document in sync.
Uses AWS Parameter Store parameters for IDP data. CloudFormation
template creates one IDP config parameter but others can be added.

# Using the CloudFormation template
1. Download [syncSaml.yaml](./syncSaml.yaml)
2. From the AWS Console, search or browse to CloudFormation
3. From the Create Stack button, choose "With new resources (standard)"
4. Choose "Upload a template file"
5. Select syncSaml.yaml from your local download
6. Click Next
7. Enter a name for the stack
8. Update any of the parameters as needed (see below)
9. Click Next
10. Click Next
11. Check the "I acknowledge that AWS CloudFormation might create IAM resources with custom names." checkbox
12. Click Create Stack

# CloudFormation parameters
* **Parameter Store path prefix** (i.e. folder path): the "folder" the Lambda function will be granted permissions
to read and will search for parameters
* **Parameter Store item name**: the first parameter to create under the path prefix that defines an IDP
* **JSON value that defines the SAML metadata**: JSON value for the first parameter. Expected JSON:
    * **Name**: friendly name of the IDP
    * **Source**: URL to the IDP metadata
    * **Destination**: Name of the IAM identity provider to create/update
    * **AppendEntityId** (optional): Value to append to the EntityId in the metadata. Required for some IDPs.
* **URL to zip file with Lambda function**: URL to zip file containing Lambda code. Defaults to the latest
version of this repo
* **Existing Bucket to copy Lambda zip to**: If you want to use an existing bucket to copy the zip to, enter 
the name here. Otherise, leave this blank and a new bucket will be created by the template.
* **Destination S3 key prefix (i.e. folder path)**: "folder" in the bucket to copy the zip to.
* **Destination S3 file name to copy zip to**: file name of the destination zip
