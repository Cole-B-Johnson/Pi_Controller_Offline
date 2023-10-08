import os
import boto3
from typing import Union, Dict

# Securely set your AWS credentials
AWS_ACCESS_KEY = 'AKIAVP5ZAHNW7TWQDNEG'
AWS_SECRET_KEY = 'iHbuzpSxrfaRdeGsj9/yfXI5sqm4R2rH1cl2RyzM'

s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

def save_to_bucket(bucket_name: str, folder_name: str, file_name: str, data: Union[Dict, str]):
    """
    Save data to a specified S3 bucket and folder.

    Parameters:
    bucket_name (str): The name of the S3 bucket.
    folder_name (str): The name of the folder within the bucket.
    file_name (str): The name of the file to create.
    data (Union[Dict, str]): The data to write to the file.
    """
    key = f"{folder_name}/{file_name}.json"
    encoded_data = str(data).encode('utf-8')
    for attempt in range(2):  # Attempt to upload twice
        try:
            s3.put_object(Body=encoded_data, Bucket=bucket_name, Key=key)
            print(f"Successfully wrote to file {file_name} in bucket {bucket_name}")
            return True
        except Exception as e:
            print(f"Error writing to file {file_name} in bucket {bucket_name} on attempt {attempt + 1}: {e}")
            if attempt == 1:  # Log the error after the second failed attempt
                print(f"Failed to upload {file_name} after 2 attempts. Moving on without deleting the file.")
    return False

def main():
    # Define local directory paths and bucket details
    log_dir = "/home/levitree/Desktop/logs/"
    data_dir = "/home/levitree/Desktop/Live-Data-Pathways/"
    bucket_name = "levitree-main"

    # Upload log files
    for foldername, subfolders, filenames in os.walk(log_dir):
        for filename in filenames:
            if filename.endswith('.log'):
                local_path = os.path.join(foldername, filename)
                with open(local_path, 'r') as file:
                    data = file.read()
                success = save_to_bucket(bucket_name, "logs", filename, data)
                if success:
                    os.remove(local_path)
                    print(f"Successfully deleted local file {local_path}")

    # Upload data files
    for foldername, subfolders, filenames in os.walk(data_dir):
        for filename in filenames:
            if filename.endswith('.json'):  # or other relevant extensions
                local_path = os.path.join(foldername, filename)
                with open(local_path, 'r') as file:
                    data = file.read()
                folder_in_bucket = foldername.replace(data_dir, "")
                success = save_to_bucket(bucket_name, folder_in_bucket, filename, data)
                if success:
                    os.remove(local_path)
                    print(f"Successfully deleted local file {local_path}")

if __name__ == "__main__":
    main()
