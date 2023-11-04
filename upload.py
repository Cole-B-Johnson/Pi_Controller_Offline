import os
import boto3
from typing import Union, Dict
from tqdm import tqdm

# Securely set your AWS credentials
AWS_ACCESS_KEY = 'AKIAVP5ZAHNW7TWQDNEG'
AWS_SECRET_KEY = 'iHbuzpSxrfaRdeGsj9/yfXI5sqm4R2rH1cl2RyzM'

s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

def save_to_bucket(bucket_name: str, folder_name: str, file_name: str, data: Union[Dict, str]):
    key = f"{folder_name}/{file_name}"
    encoded_data = str(data).encode('utf-8')
    for attempt in range(2):  # Attempt to upload twice
        try:
            s3.put_object(Body=encoded_data, Bucket=bucket_name, Key=key)
            return True
        except Exception as e:
            if attempt == 1:  # Log the error after the second failed attempt
                print(f"Failed to upload {file_name} after 2 attempts. Error: {e}")
    return False


def count_files(directory: str, extension: str) -> int:
    count = 0
    for _, _, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith(extension):
                count += 1
    return count

def main():
    # Define local directory paths and bucket details
    log_dir = "/home/levitree/Desktop/logs/"
    data_dir = "/home/levitree/Desktop/Live-Data-Pathways/"
    bucket_name = "levitree-main"
    
    # Preprocessing step to calculate total number of files
    total_log_files = count_files(log_dir, '.log')
    total_data_files = count_files(data_dir, '.json')

    print(f'Uploading {total_log_files} .log log files and {total_data_files} .json data files...')
    
    log_error_counter = 0
    log_success_counter = 0
    data_error_counter = 0
    data_success_counter = 0

    # Process log files
    print("Processing log files:")

    for foldername, subfolders, filenames in os.walk(log_dir):        
        for filename in tqdm(filenames, 
                            bar_format='{l_bar}{bar}| {percentage:3.0f}%  Success: {postfix[0]}, Failed: {postfix[1]}', 
                            postfix=[log_success_counter, log_error_counter]):
            if filename.endswith('.log'):
                local_path = os.path.join(foldername, filename)
                with open(local_path, 'r') as file:
                    data = file.read()
                success = save_to_bucket(bucket_name, "logs", filename, data)
                if success:
                    os.remove(local_path)
                    log_success_counter += 1
                else:
                    log_error_counter += 1

    print("\nProcessing data files:")

    for foldername, subfolders, filenames in os.walk(data_dir):
        for filename in tqdm(filenames, 
                            bar_format='{l_bar}{bar}| {percentage:3.0f}%  Success: {postfix[0]}, Failed: {postfix[1]}', 
                            postfix=[data_success_counter, data_error_counter]):
            if filename.endswith('.json'):
                local_path = os.path.join(foldername, filename)
                try:
                    with open(local_path, 'r') as file:
                        data = file.read()
                    folder_in_bucket = "uploaded_data/" + foldername.replace(data_dir, "").lstrip("/")
                    success = save_to_bucket(bucket_name, folder_in_bucket, filename, data)
                    if success:
                        os.remove(local_path)
                        data_success_counter += 1
                    else:
                        data_error_counter += 1
                except Exception as e:
                    data_error_counter += 1
                    os.remove(local_path)

    # Print the summary at the end
    print("\nUpload Summary:")

    # Log files summary
    print("Log Files:")
    if log_error_counter == 0:
        print(f"All {total_log_files} log files uploaded successfully!")
    else:
        print(f"{log_success_counter}/{total_log_files} log files uploaded successfully.")
        print(f"{log_error_counter} log files had issues and were not uploaded.")

    # Data files summary
    print("\nData Files:")
    if data_error_counter == 0:
        print(f"All {total_data_files} data files uploaded successfully!")
    else:
        print(f"{data_success_counter}/{total_data_files} data files uploaded successfully.")
        print(f"{data_error_counter} data files had issues and were not uploaded.")

if __name__ == "__main__":
    main()