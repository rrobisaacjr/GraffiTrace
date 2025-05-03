import os
import numpy as np
from PIL import Image
import py360convert
from multiprocessing import Pool
import warnings # Import warnings

# Suppress UserWarnings
warnings.filterwarnings("ignore", category=UserWarning)

def process_image(args):
    file, datasets_directory, output_directory = args  # Unpack the tuple
    if file.lower().endswith(".jpg"):
        input_image_path = os.path.join(datasets_directory, file)
        filename = os.path.splitext(file)[0]

        # Load the equirectangular image
        print(f"Processing file: {filename}")
        equirectangular_image = np.array(Image.open(input_image_path))

        # Convert to cubemap with each face width of 512 pixels
        # Set cube_format='dict' to get each face as a separate numpy array
        cube_faces_dict = py360convert.e2c(
            equirectangular_image,
            face_w=2048,
            mode='bilinear',
            cube_format='dict'
        )

        # Save only the left ("L") and right ("R") faces in the Output folder
        for face_name, face_image_array in cube_faces_dict.items():
            if face_name in ["L", "R"]:
                face_image = Image.fromarray(face_image_array)
                face_image.save(os.path.join(output_directory, f"[{face_name}] {filename}.png"))

        print(f"Left and Right cubemap faces saved for {filename} to {output_directory}")

# Increase the decompression bomb limit (e.g., set it to 200 million pixels)
Image.MAX_IMAGE_PIXELS = 200000000

if __name__ == "__main__":
    # Get the directory of the current Python script
    script_directory = os.path.dirname(os.path.abspath(__file__))
    datasets_directory = os.path.join(script_directory, "Datasets")
    output_directory = os.path.join(script_directory, "Output")
    os.makedirs(output_directory, exist_ok=True)  # Create the Output directory if it doesn't exist

    # Get list of .jpg files in the Datasets folder
    image_files = [file for file in os.listdir(datasets_directory) if file.lower().endswith(".jpg")]

    # Define batch size for processing
    batch_size = 5  # Adjust this based on your system's memory and CPU capability

    # Process images in batches
    for i in range(0, len(image_files), batch_size):
        batch = image_files[i:i + batch_size]
        
        # Use a Pool to process each batch of images in parallel
        with Pool() as pool:
            pool.map(process_image, [(file, datasets_directory, output_directory) for file in batch])
        
        print(f"\nProcessed batch {i // batch_size + 1}/{(len(image_files) + batch_size - 1) // batch_size}\n")