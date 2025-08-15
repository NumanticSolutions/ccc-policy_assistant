# © 2025 Numantic Solutions LLC
# MIT License
#
# Operating system tools

import os
import shutil



def copy_and_replace_recursive(src_dir, dst_dir):
    '''
    Function to copy and replace a directory including all files in all subdirectories
    '''
    # Ensure source directory exists
    if not os.path.isdir(src_dir):
        raise FileNotFoundError(f"Source directory does not exist: {src_dir}")

    # Create the destination directory if it doesn't exist
    os.makedirs(dst_dir, exist_ok=True)

    for item in os.listdir(src_dir):
        src_path = os.path.join(src_dir, item)
        dst_path = os.path.join(dst_dir, item)

        if os.path.isdir(src_path):
            # Recursively copy subdirectory
            copy_and_replace_recursive(src_path, dst_path)
        elif os.path.isfile(src_path):
            # Copy and replace file
            shutil.copy2(src_path, dst_path)
            # print(f"Copied and replaced: {dst_path}")


