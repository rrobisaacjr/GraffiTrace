import os
import csv
import numpy as np
from PIL import Image, ImageFile, ExifTags
import py360convert
from multiprocessing import Pool, get_context
from PIL import Image  # Import  Image
import warnings  # Import warnings

# Suppress Warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=Image.DecompressionBombWarning)


def prepare_directory(base_directory):
    """
    Creates the 'Preprocessed' directory and the 'preprocessed.csv' file.

    Args:
        base_directory (str): The base directory where 'Preprocessed' should be created.
    """
    preprocessed_dir = os.path.join(base_directory, "Preprocessed")
    os.makedirs(preprocessed_dir, exist_ok=True)  # Create the directory, no error if it exists

    csv_path = os.path.join(preprocessed_dir, "preprocessed.csv")
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["image_name", "latitude", "longitude"])  # Write the header row

    print(f"Created directory: {preprocessed_dir}")
    print(f"Created CSV file: {csv_path}")
    return preprocessed_dir  # Return the path to the preprocessed directory

def _convert_to_degrees(value):
    """
    Helper function to convert GPS coordinates from degree/minute/second
    to decimal degrees.
    """
    #print(f"Value in _convert_to_degrees: {value}, type: {type(value)}") #commented out
    if isinstance(value, tuple):
        d = float(value[0])
        m = float(value[1]) / 60.0
        s = float(value[2]) / 3600.0
        return d + m + s
    elif hasattr(value, '__float__'):
        return float(value)
    else:
        return value


def get_coordinates(gps_info):
    """
    Helper function to extract latitude and longitude from GPSInfo.
    """
    latitude = None
    longitude = None
    #print(f"GPS Info in get_coordinates: {gps_info}, type: {type(gps_info)}") #commented out
    if 1 in gps_info and 2 in gps_info and 3 in gps_info and 4 in gps_info:
        latitude = _convert_to_degrees(gps_info[2])
        longitude = _convert_to_degrees(gps_info[4])
        if gps_info[1] == 'S':
            latitude = -latitude
        if gps_info[3] == 'W':
            longitude = -longitude
    return latitude, longitude

def get_exif_data(img):
    """Extract EXIF data from an image."""
    exif_data = {}
    try:
        info = img._getexif()
        if info:
            for tag, value in info.items():
                decoded_tag = ExifTags.TAGS.get(tag, tag)
                exif_data[decoded_tag] = value
    except AttributeError:
        # If the image doesn't have _getexif() method
        pass
    return exif_data

def process_image(args):
    """
    Processes a single image: converts it to cubemap, saves left and right faces,
    and saves the coordinates in a csv file.

    Args:
        args (tuple): A tuple containing:
            - file (str): The filename of the image.
            - images_directory (str): The directory containing the input images.
            - output_directory (str): The directory to save the output images.
            - image_counter (int): A counter for naming the output files.
    """
    file, images_directory, output_directory, image_counter = args
    if file.lower().endswith(".jpg") or file.lower().endswith(".jpeg"):
        input_image_path = os.path.join(images_directory, file)
        filename = os.path.splitext(file)[0]

        # Load the equirectangular image
        print(f"Processing file: {filename}")
        try:
            equirectangular_image = np.array(Image.open(input_image_path))
        except Exception as e:
            print(f"Error opening image {input_image_path}: {e}")
            return image_counter, f"Error opening image: {e}"

        latitude = None
        longitude = None
        try:
            # Get EXIF data and extract GPS info
            original_image = Image.open(input_image_path)
            exif_data = get_exif_data(original_image)
            original_image.close()
            if "GPSInfo" in exif_data:
                latitude, longitude = get_coordinates(exif_data["GPSInfo"])
        except Exception as e:
            print(f"Error extracting GPS data from {filename}: {e}")
            # Continue processing, but log the error

        # Convert to cubemap
        try:
            cube_faces_dict = py360convert.e2c(
                equirectangular_image,
                face_w=2048,
                mode='bilinear',
                cube_format='dict'
            )
        except Exception as e:
            print(f"Error converting {filename} to cubemap: {e}")
            return image_counter, f"Error converting to cubemap: {e}"

        # Save left and right faces, and write to CSV
        saved_faces = 0
        for face_name, face_image_array in cube_faces_dict.items():
            if face_name in ["L", "R"]:
                face_image = Image.fromarray(face_image_array)
                try:
                    face_image_name = f"[{face_name}] {filename}.png"  # Changed to use face name in filename
                    face_image.save(os.path.join(output_directory, face_image_name))
                    saved_faces += 1
                    # Write to CSV
                    csv_path = os.path.join(output_directory, "preprocessed.csv")
                    with open(csv_path, 'a', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([face_image_name, latitude, longitude])
                except Exception as e:
                    print(f"Error saving cubemap face {face_name} for {filename}: {e}")
                    return image_counter, f"Error saving cubemap face: {e}"
        if saved_faces>0:
            image_counter += saved_faces #increment image counter by the number of saved faces
            print(f"Left and Right cubemap faces saved for {filename} to {output_directory}")
            return image_counter, None
        else:
            return image_counter, "No faces saved"
    return image_counter, None



# Increase the decompression bomb limit
ImageFile.MAX_IMAGE_PIXELS = 200000000


def rename_preprocessed_images(output_directory):
    """
    Renames the processed image files in the output directory to "0001.png", "0002.png", etc.,
    and updates the corresponding filenames in the preprocessed.csv file.

    Args:
        output_directory (str): The path to the directory containing the preprocessed images
                                and the preprocessed.csv file.
    """
    print("Renaming preprocessed images...")
    csv_path = os.path.join(output_directory, "preprocessed.csv")
    temp_csv_path = os.path.join(output_directory, "temp_preprocessed.csv")  # Create a temporary CSV file

    # Create a dictionary to store the old and new file names from the CSV
    old_new_names = {}
    image_counter = 1

    try:
        # Read the original CSV file and store the old and new names
        with open(csv_path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)  # Read the header
            for row in reader:
                old_image_name = row[0]
                new_image_name = f"{image_counter:04d}.png"
                old_new_names[old_image_name] = new_image_name
                image_counter += 1

        # Rename the image files and create a new CSV with updated names
        with open(csv_path, 'r', newline='') as csvfile, \
                open(temp_csv_path, 'w', newline='') as temp_csvfile:

            reader = csv.reader(csvfile)
            writer = csv.writer(temp_csvfile)

            writer.writerow(header)  # Write the header to the new CSV

            for row in reader:
                old_image_name = row[0]
                latitude = row[1]
                longitude = row[2]
                if old_image_name in old_new_names:
                    new_image_name = old_new_names[old_image_name]
                    # Rename the file
                    old_file_path = os.path.join(output_directory, old_image_name)
                    new_file_path = os.path.join(output_directory, new_image_name)
                    try:
                        os.rename(old_file_path, new_file_path)
                    except Exception as e:
                        print(f"Error renaming file {old_image_name} to {new_image_name}: {e}")
                        new_image_name = old_image_name #keep the old name if renaming fails

                    writer.writerow([new_image_name, latitude, longitude])
                else:
                    writer.writerow(row)  # Keep the original row if filename not found (shouldn't happen)

        # Replace the original CSV with the temporary CSV
        os.remove(csv_path)
        os.rename(temp_csv_path, csv_path)

        print("Images renamed and CSV updated successfully.")

    except Exception as e:
        print(f"An error occurred during renaming: {e}")




def process_images(project_directory):
    """
    Processes images in the given project directory, converts them to cubemap
    faces, saves left and right faces, and saves coordinates to a CSV file.

    Args:
        project_directory (str): The path to the project directory.
    """
    print(f"Processing images in directory: {project_directory}")
    images_directory = os.path.join(project_directory, "images")
    output_directory = os.path.join(project_directory, "Preprocessed")

    if not os.path.exists(images_directory):
        print(f"Error: 'images' directory not found in {project_directory}")
        return

    image_files = [
        file for file in os.listdir(images_directory)
        if file.lower().endswith(".jpg") or file.lower().endswith(".jpeg")
    ]

    batch_size = 5

    image_counter = 1

    context = get_context("spawn")
    for i in range(0, len(image_files), batch_size):
        batch = image_files[i:i + batch_size]
        with context.Pool() as pool:
            results = pool.map(
                process_image,
                [(file, images_directory, output_directory, image_counter) for file in batch]
            )

        for result in results:
            if isinstance(result, tuple):
                image_counter, error_message = result
                if error_message:
                    print(f"Error during processing: {error_message}")
        print(f"\nProcessed batch {i // batch_size + 1}/{ (len(image_files) + batch_size - 1) // batch_size}\n")
    rename_preprocessed_images(output_directory) #call the function here



def run_data_preprocessing(project_directory):
    """
    Encapsulates the entire data preprocessing sequence.

    Args:
        project_directory (str): The path to the project directory.
    """
    print("Starting data preprocessing...")
    preprocessed_directory = prepare_directory(project_directory)
    process_images(project_directory)
    print("Data preprocessing complete.")



if __name__ == "__main__":
    test_directory = "D:\Downloads\SP\Test"
    run_data_preprocessing(test_directory)
