import zipfile as zf


def get_file(uploaded_file):
    # Save the uploaded zip file object to binary
    bytes_data = uploaded_file.getvalue()

    # Write the binary into zip file
    with open(uploaded_file.name, "wb+") as file:
        file.write(bytes_data)

    # Unzip the zip file and save all files/folders in current folder
    with zf.ZipFile("./" + uploaded_file.name) as file:
        file_path = file.namelist()[0].strip("/") 
        file.extractall()

    return file_path