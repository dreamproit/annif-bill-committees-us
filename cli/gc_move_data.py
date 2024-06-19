import click
import gcsfs
from datetime import datetime
import pathlib
import shutil

import os
import zipfile
from google.cloud import storage
import streamlit as st    


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), 
                       os.path.relpath(os.path.join(root, file), 
                                       os.path.join(path, '..')))


def get_st_gcs_secrets():
    gcs_secrets_dict = st.secrets['connections']['gcs']
    return gcs_secrets_dict


def create_cloud_client_with_streamlit():
    gcs_secrets_dict = get_st_gcs_secrets()
    client = storage.Client.from_service_account_info(gcs_secrets_dict)
    return client


def archive_data(source, archive_folder: str = './archives'):
    now_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archives_folder_path = pathlib.Path(archive_folder)
    source_path = pathlib.Path(source)
    archives_folder_path.mkdir(parents=True, exist_ok=True)
    archive_file_name = f"{now_time}_{source_path.stem}.zip"
    archive_dest_path = archives_folder_path / archive_file_name
    with zipfile.ZipFile(archive_dest_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipdir(source, zipf)
    print(f"Succesfully archived {source} to {archive_dest_path}.")
    return archive_dest_path


def upload_to_gc(source, project_id: str, bucket_name: str, creds_file_path: str):
    source_file_path = pathlib.Path(source)
    cloud_storage_client = create_cloud_client_with_streamlit()
    bucket = cloud_storage_client.get_bucket(bucket_name)
    blob = bucket.blob(source_file_path.name)
    blob.upload_from_filename(source_file_path)
    print(f'Uploaded {source_file_path} to {bucket_name}.')
    return source_file_path


def upload_data(source, project_id: str, bucket_name: str, creds_file_path: str, archive: bool):
    if archive:
        to_upload_filepath = archive_data(source)
    else:
        to_upload_filepath = source
    to_upload_filepath = './archives/2024-06-18_17-48-59_data.zip'
    upload_to_gc(to_upload_filepath, project_id, bucket_name, creds_file_path)


def download_from_gc(project_id: str, bucket_name: str, creds_file_path: str, destination:str = './'):
    cloud_storage_client = create_cloud_client_with_streamlit()
    bucket = cloud_storage_client.get_bucket(bucket_name)
    latest_blob = None
    sorted_blobs = sorted(bucket.list_blobs(), key=lambda blob: blob.time_created)
    for blob in sorted_blobs:
        latest_blob = blob
    if not latest_blob:
        print(f"No files in bucket {bucket_name}.")
        return
    destination_file_path = pathlib.Path(destination) / latest_blob.name
    latest_blob.download_to_filename(destination_file_path)
    print(f'Downloaded {latest_blob.name} to {destination_file_path}.')
    return destination_file_path


def download_data(project_id: str, bucket_name: str, creds_file_path: str, archive: bool, destination):
    dowloaded_filename = download_from_gc(project_id, bucket_name, creds_file_path, destination)
    if archive:
        with zipfile.ZipFile(dowloaded_filename, 'r') as zip_ref:
            zip_ref.extractall(destination)
        print(f"Extracted {dowloaded_filename} to {destination}.")


def gc_move_data(mode: str, source: str = './data', destination: str = './', project_id: str = None, bucket_name: str = None, creds_file_path: str = None, archive: bool = True):
    if mode == 'upload':
        upload_data(source, project_id, bucket_name, creds_file_path, archive)
    elif mode == 'download':
        download_data(project_id, bucket_name, creds_file_path, archive, destination)
    else:
        print(f"Invalid mode: {mode}")


@click.command()
@click.option('--mode', 'mode', help='Mode of the move data command.', default='upload')
@click.option('--source', 'source', help='Source folder or file to upload.', default='./data')
@click.option('--destination', 'destination', help='Destination folder or file to download.', default='./')
@click.option('--project-id', 'project_id', help='The project id of the google cloud project.', default='models')
@click.option('--bucket-name', 'bucket_name', help='The name of the google cloud storage bucket.', default='annif-models')
@click.option('--creds-file-path', 'creds_file_path', help='The filepath to google creds .json file', default='./creds.json')
@click.option('--archive', 'archive', help='Whether to archive the data.', default=False, is_flag=True)
def main(mode: str, source: str, destination: str, project_id: str, bucket_name: str, creds_file_path: str, archive: bool):
    """Move data from local to google cloud storage or vice versa."""
    try:
        gc_move_data(mode, source, destination, project_id, bucket_name, creds_file_path, archive)
    except Exception as e:
        print(f"Error: {e}")
        raise e


if __name__ == '__main__':
    main()
