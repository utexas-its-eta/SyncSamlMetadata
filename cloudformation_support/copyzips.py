import json
import logging
import threading
import boto3
import cfnresponse
import urllib.request

def copy_objects(source_urls, dest_bucket, prefix, objects):
  s3 = boto3.client('s3')
  for i in range(len(source_urls)):
    key = prefix + objects[i]
    req = urllib.request.Request(source_urls[i])
    resp = urllib.request.urlopen(req)
    print('copy_source: %s' %source_urls[i])
    print('dest_bucket = %s'%dest_bucket)
    print('dest_key = %s' %key)
    s3.upload_fileobj(resp, dest_bucket, key) 

def delete_objects(bucket, prefix, objects):
  s3 = boto3.client('s3')
  objects = {'Objects': [{'Key': prefix + o} for o in objects]}
  s3.delete_objects(Bucket=bucket, Delete=objects)

def timeout(event, context):
  logging.error('Execution is about to time out, sending failure response to CloudFormation')
  cfnresponse.send(event, context, cfnresponse.FAILED, {}, None)

def handler(event, context):
  timer = threading.Timer((context.get_remaining_time_in_millis()
            / 1000.00) - 0.5, timeout, args=[event, context])
  timer.start()

  print('Received event: %s' % json.dumps(event))
  status = cfnresponse.SUCCESS

  try:
    source_urls = event['ResourceProperties']['SourceURLs']
    dest_bucket = event['ResourceProperties']['DestBucket']
    prefix = event['ResourceProperties']['Prefix']
    objects = event['ResourceProperties']['DestObjects']
    print('source_urls: %s, objects: %s' % ( len(source_urls), len(objects)))
    assert len(source_urls) == len(objects)
    if event['RequestType'] == 'Delete':
        delete_objects(dest_bucket, prefix, objects)
    else:
        copy_objects(source_urls, dest_bucket, prefix, objects)
  except Exception as e:
    logging.error('Exception: %s' % e, exc_info=True)
    status = cfnresponse.FAILED
  finally:
    timer.cancel()
    cfnresponse.send(event, context, status, {}, None)