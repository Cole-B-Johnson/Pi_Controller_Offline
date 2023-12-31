import os
import pandas as pd
import boto3
from typing import Union, Dict
from tqdm import tqdm
import datetime

# Securely set your AWS credentials
AWS_ACCESS_KEY = 'AKIAVP5ZAHNWSDRBNF55'
AWS_SECRET_KEY = 'vVBQ6Kkd9B4h7jA6KJa4jc9tUPJInz6GQUxmFFFi'

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

def read_file_to_dataframe(path: str, filename: str, filetype: str) -> pd.DataFrame:
    if filetype == 'log':
        with open(path, 'r') as file:
            lines = file.readlines()
        df = pd.DataFrame(lines, columns=['data'])
    elif filetype == 'json':
        df = pd.read_json(path, lines=True)

    df['filename'] = filename
    return df


def concatenate_files(directory: str, extension: str) -> pd.DataFrame:
    all_files_df = pd.DataFrame()
    total_files = sum([len(files) for _, _, files in os.walk(directory) if any(file.endswith(extension) for file in files)])
    progress = tqdm(total=total_files, desc=f"Concatenating {extension} files")

    for foldername, _, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith(extension):
                subdirectory = os.path.relpath(foldername, directory)  # Relative path of the subdirectory
                full_filename = os.path.join(subdirectory, filename) if subdirectory != "." else filename  # Include subdirectory in filename
                path = os.path.join(foldername, filename)
                file_df = read_file_to_dataframe(path, full_filename, extension.strip('.'))
                all_files_df = pd.concat([all_files_df, file_df], ignore_index=True)
                progress.update(1)

    progress.close()
    return all_files_df

def process_and_upload_files(directory: str, bucket_name: str, folder_in_bucket: str, extension: str):
    print('Concatenating Files...')
    concatenated_df = concatenate_files(directory, extension)
    csv_data = concatenated_df.to_csv(index=False)
    filename = f"{datetime.datetime.now().strftime('%Y-%m-%d')}.csv"

    print('Uploading Files...')
    success = save_to_bucket(bucket_name, folder_in_bucket, filename, csv_data)
    
    if success:
        print('Deleting Files...')
        total_files = sum([len(files) for _, _, files in os.walk(directory) if files and files[0].endswith(extension)])
        progress = tqdm(total=total_files, desc=f"Deleting {extension} files")
        for foldername, _, filenames in os.walk(directory):
            for filename in filenames:
                if filename.endswith(extension):
                    os.remove(os.path.join(foldername, filename))
                    progress.update(1)
        progress.close()
        print(f"Successfully uploaded and deleted all {extension} files.")
    else:
        print(f"Failed to upload {extension} files. No files were deleted.")

def main():
    # Define local directory paths and bucket details
    log_dir = "/home/levitree/Desktop/logs/"
    data_dir = "/home/levitree/Desktop/Live-Data-Pathways/"
    bucket_name = "levitree-main"

    # Process, upload, and delete log files
    process_and_upload_files(log_dir, bucket_name, "uploaded_data/logs", ".log")

    # Process, upload, and delete JSON data files
    process_and_upload_files(data_dir, bucket_name, "uploaded_data/data", ".json")

if __name__ == "__main__":
    main()
