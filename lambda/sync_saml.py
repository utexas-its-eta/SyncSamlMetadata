import json
import boto3
import cfnresponse
import logging
import os
from botocore.exceptions import ClientError
import requests
import threading
import re
from lxml import etree
from xmldiff import main as xmldiff
from xmldiff import actions as diffactions

iam = boto3.client('iam')
ssm = boto3.client('ssm')

def add_saml_source(param):
  """ Takes a Parameter store dictionary and adds data source metadata """
  regex = '(<EntityDescriptor[^>]+entityID=")(?P<EntityID>[^"]+)(")'
  source_text = requests.get(param['source']).text
  srcmatch = re.search(regex, source_text)
  assert srcmatch, 'Parameter: "{}" does not match entity regex'.format(param['name'])
  if 'appendEntityID' in param.keys():
    source_text = re.sub(regex, '\g<1>\g<2>' + param['appendEntityID'] + '\g<3>', source_text)
  param['source_text'] = source_text
  return param

def add_saml_destination(param):
  """ Takes a Parameter store dictionary and adds data about the IAM IDP """
  samlList = iam.list_saml_providers()['SAMLProviderList']
  matchingSaml = [saml for saml in samlList if saml['Arn'].endswith('/'+param['destination'])]
  if 1 == len(matchingSaml):
    param['destination_text'] = iam.get_saml_provider(SAMLProviderArn=matchingSaml[0]['Arn'])['SAMLMetadataDocument']
    param['iamArn'] = matchingSaml[0]['Arn']
  elif 0 == len(matchingSaml):
    param['destination_text'] = 'DNE'
  else:
    param['error'] = 'Received more than one SAML provider'
  return param

def clean_saml(xml_text):
  """ Remove dynamic elements from SAML metadata document for comparison """
  xml = etree.fromstring(xml_text)
  for node in xml.xpath("/*[local-name() = 'EntityDescriptor' and @ID]"):
    node.attrib.pop('ID', None)
  for node in xml.xpath("*[local-name() = 'Signature']/*[local-name() = 'SignedInfo']/*[local-name() = 'Reference' and @URI]"):
    node.attrib.pop('URI',None)
  for node in xml.xpath("*[local-name() = 'Signature']/*[local-name() = 'SignedInfo']/*[local-name() = 'Reference']/*[local-name() = 'DigestValue']"):
    node.text = ''
  for node in xml.xpath("*[local-name() = 'Signature']/*[local-name() = 'SignatureValue']"):
    node.text = ''
  return etree.tostring(xml)

def test_saml(param):
  """ Tests currently configured IAM provider's saml metadata
  True if update is required
  """
  if 'DNE' == param['destination_text']:
    return True
  sourceXMLtext = clean_saml(param['source_text'])
  destXMLtext = clean_saml(param['destination_text'])
  diff = xmldiff.diff_texts(sourceXMLtext, destXMLtext, diff_options={'F': 1})
  nonMoveDiffs = [elm for elm in diff if not isinstance(elm, diffactions.MoveNode)]
  return len(nonMoveDiffs) > 0

def update_saml_destination(param):
  """ Create or update the AWS SAML provider """
  try:
    if 'DNE' == param['destination_text']:
      iam.create_saml_provider(Name = param['destination'], SAMLMetadataDocument = param['source_text'])
    else:
      iam.update_saml_provider(SAMLProviderArn = param['iamArn'], SAMLMetadataDocument = param['source_text'])
  except ClientError as err:
    logging.error('Parameter: "{}" failed to update IAM destination object: {}'.format(param['name'], err))


def saml_handler(param):
  """ Processes AWS Parameter Store specification of a SAML indentity provider (IDP)

  Parameter Value should be JSON in the format (without comments):
  {
    # Required: Descriptive name
    "Name": "austin-test",
    # Required: URL of the SAML metadata document
    "Source": "https://login.austin.utexas.edu/FederationMetadata/2007-06/FederationMetadata.xml",
    # Required: IAM name SAML identity provider name
    "Destination": "austin-test",
    # Optional: Value to append to the SAML entity ID
    "AppendEntityId": "3"
  }

  The AppendEntityId is required in cases where the IDP can't handle multiple service providers with
  the same EntityID. 
  See https://aws.amazon.com/blogs/desktop-and-application-streaming/enabling-federation-with-azure-ad-single-sign-on-and-amazon-appstream-2-0/
  
  """
  param_value = json.loads(param['Value'])
  saml_parameter = {
    "name": param['Name'],
    "source": param_value['Source'],
    "destination": param_value['Destination'],
  }
  if 'AppendEntityId' in param_value.keys():
    saml_parameter['appendEntityID'] = param_value['AppendEntityId']
  saml_parameter = add_saml_source(saml_parameter)
  if 'error' in saml_parameter:
    logging.error('Parameter: "{}" error getting the source: {}'.format(saml_parameter['name'], saml_parameter['error']))
    return
  saml_parameter = add_saml_destination(saml_parameter)
  if 'error' in saml_parameter:
    logging.error('Parameter: "{}" error getting the destination: {}'.format(saml_parameter['name'], saml_parameter['error']))
    return
  if test_saml(saml_parameter):
    print('{} : destination needs update, updating now'.format(saml_parameter['name']))
    update_saml_destination(saml_parameter)
  else:
    print('{} : metadata source and destination match, skipping update'.format(saml_parameter['name']))

def timeout(event, context, IsCfn):
  logging.error('Execution is about to time out, sending failure response.')
  if IsCfn:
    cfnresponse.send(event, context, cfnresponse.FAILED, {}, None)

def lambda_handler(event, context):
  try:
    IsCfn = False
    if 'ResponseURL' in event:
      IsCfn = True
      status = cfnresponse.SUCCESS
    timer = threading.Timer((context.get_remaining_time_in_millis()
            / 1000.00) - 0.5, timeout, args=[event, context, IsCfn])
    timer.start()
    print('Received event: %s' % json.dumps(event))

    saml_parameters = ssm.get_parameters_by_path(
      Path=os.environ['ParameterPrefix'],
      Recursive=True,
      ParameterFilters=[{ 'Key': 'Type', 'Option': 'Equals', 'Values': ['String'] }]
    )
    for param in saml_parameters['Parameters']:
      saml_handler(param)
  except Exception as e:
    logging.error('Exception: %s' % e, exc_info=True)
    if IsCfn:
      status = cfnresponse.FAILED
  finally:
    timer.cancel()
    if IsCfn:
      cfnresponse.send(event, context, status, {}, None)

  