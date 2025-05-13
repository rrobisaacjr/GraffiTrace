import tkinter
import customtkinter
from tkinter import filedialog
import os
from PIL import Image, ExifTags, ImageTk  # Import PIL for image processing
import threading  # Import the threading module

class InitialFrame(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

        # Create name of place input
        self.name_label = customtkinter.CTkLabel(self, text="Target Place:", anchor="w")
        self.name_label.grid(row=0, column=0, padx= (20, 0), pady=(20, 0), sticky="ew")
        self.name_entry = customtkinter.CTkEntry(self)
        self.name_entry.grid(row=0, column=1, columnspan=2, padx= (10, 20), pady=(20, 0), sticky="ew")

        # Create project directory input
        self.project_dir_label = customtkinter.CTkLabel(self, text="Project Directory:", anchor="w")
        self.project_dir_label.grid(row=1, column=0, padx=(20, 0), pady=(10, 0), sticky="ew")
        self.project_dir_entry = customtkinter.CTkEntry(self)
        self.project_dir_entry.grid(row=1, column=1, padx=10, pady=(10, 0), sticky="ew")
        self.project_dir_button = customtkinter.CTkButton(self, text="Browse", command=self.select_project_directory, width=80)
        self.project_dir_button.grid(row=1, column=2, padx=(0, 20), pady=(10, 0), sticky="e")

        # Add instruction label below project directory
        self.project_instruction_label = customtkinter.CTkLabel(self,
                                                                text="Project folder should contain an 'images' folder with panoramic images containing EXIF location data.",
                                                                anchor="w",
                                                                text_color="grey")
        self.project_instruction_label.grid(row=2, column=1, columnspan=3, padx=10, pady=(0, 10), sticky="ew")

        # Create model path input
        self.model_path_label = customtkinter.CTkLabel(self, text="Model File (.pth):", anchor="w")
        self.model_path_label.grid(row=3, column=0, padx=(20, 0), pady=(10, 0), sticky="ew")
        self.model_path_entry = customtkinter.CTkEntry(self)
        default_model_path = r"C:\Users\MB-PC\Downloads\GraffiTrace\Validation Phase\first_tuning\optuna_output\0\model_final.pth"
        self.model_path_entry.insert(0, default_model_path)
        self.model_path_entry.grid(row=3, column=1, padx=10, pady=(10, 0), sticky="ew")
        self.model_path_entry.configure(state="readonly")
        self.model_path_button = customtkinter.CTkButton(self, text="Browse", command=self.select_model_path, width=80)
        self.model_path_button.grid(row=3, column=2, padx=(0, 20), pady=(10, 0), sticky="e")

        # Create the image frame (initially empty)
        self.image_frame = customtkinter.CTkFrame(self)
        self.image_frame.grid(row=4, column=0, columnspan=3, padx=20, pady=20, sticky="nsew")
        self.grid_rowconfigure(4, weight=1)  # Make it expandable

        # Create a placeholder label.  This will be replaced with the scrollable frame when the project directory is selected.
        self.image_frame_placeholder = customtkinter.CTkLabel(self.image_frame, text="Select a project directory to view images.", text_color="grey")
        self.image_frame_placeholder.pack(fill="both", expand=True)

        self.scrollable_image_frame = None  # declare as none and create only when the directory is selected
        self.header_labels = ["Thumbnail", "Filename", "Latitude", "Longitude"]
        self.loading_frame = None # Declare loading frame

    def create_scrollable_image_frame(self):
        """
        Creates the scrollable frame to display images.
        """
        # Destroy the placeholder label
        self.image_frame_placeholder.destroy()

        # Create the scrollable frame
        self.scrollable_image_frame = customtkinter.CTkScrollableFrame(self.image_frame, fg_color="transparent")
        self.scrollable_image_frame.pack(fill="both", expand=True)

        # Add the table headers as the first row
        for i, header in enumerate(self.header_labels):
            header_label = customtkinter.CTkLabel(self.scrollable_image_frame, text=header,
                                                    font=customtkinter.CTkFont(weight="bold"))
            header_label.grid(row=0, column=i, padx=10, pady=(5, 0), sticky="nsew")
        self.scrollable_image_frame.grid_columnconfigure(0, weight=5)  # Make the thumbnail column 50%
        for i in range(1, len(self.header_labels)):
            self.scrollable_image_frame.grid_columnconfigure(i, weight=1)
            
    def create_loading_frame(self):
        """Creates a frame with a progress bar and a label for showing loading status."""
        self.loading_frame = customtkinter.CTkFrame(self.image_frame, fg_color="transparent")
        self.loading_frame.pack(fill="both", expand=True)

        self.loading_label = customtkinter.CTkLabel(self.loading_frame, text="Loading images...", text_color="grey")
        self.loading_label.pack(pady=10)

        self.progressbar = customtkinter.CTkProgressBar(self.loading_frame)
        self.progressbar.pack(padx=20, fill="x", pady=20, anchor="center") # Added anchor
        self.progressbar.configure(mode="indeterminate")  # Set to indeterminate mode initially
        self.progressbar.start()

    def destroy_loading_frame(self):
        """Destroys the loading frame."""
        if self.loading_frame:
            self.loading_frame.destroy()
            self.loading_frame = None

    def update_image_list(self):
        """
        Updates the list of images in the scrollable frame based on the selected project directory.
        """
        project_directory = self.project_dir_entry.get().strip()

        if not project_directory:
            return  # Do nothing if no project directory is selected

        images_folder_path = os.path.join(project_directory, "images")
        if not os.path.isdir(images_folder_path):
            return  # Do nothing if the images folder doesn't exist

        # If the scrollable frame doesn't exist, create it.
        if self.scrollable_image_frame is None:
            self.create_scrollable_image_frame()

        # Clear any existing widgets in the scrollable frame (except the headers)
        for child in self.scrollable_image_frame.winfo_children():
            if isinstance(child, customtkinter.CTkLabel) and child.cget("font").cget("weight") == "bold":
                continue  # Skip the header labels
        for child in self.scrollable_image_frame.winfo_children(): #destroy the rest
            child.destroy()

        # Add the table headers as the first row
        for i, header in enumerate(self.header_labels):
            header_label = customtkinter.CTkLabel(self.scrollable_image_frame, text=header,
                                                    font=customtkinter.CTkFont(weight="bold"))
            header_label.grid(row=0, column=i, padx=10, pady=(5, 0), sticky="nsew")
            self.scrollable_image_frame.grid_columnconfigure(i, weight=1)

        image_files = [] #initialize image_files
        try:
            image_files = [f for f in os.listdir(images_folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        except FileNotFoundError:
            print(f"Error: The directory '{images_folder_path}' was not found.")
            return

        if not image_files:
            no_images_label = customtkinter.CTkLabel(self.scrollable_image_frame,
                                                    text="No images found in the 'images' folder.", text_color="grey")
            no_images_label.grid(row=1, column=0, columnspan=4, padx=10, pady=5, sticky="w")  # span 4 columns
            return

        # Show loading frame and start processing in a separate thread
        self.create_loading_frame()
        threading.Thread(target=self.process_images, args=(image_files, images_folder_path)).start()

    def process_images(self, image_files, images_folder_path):
        """
        Processes the images and updates the UI.  This function is run in a separate thread.

        Args:
            image_files (list): List of image file names.
            images_folder_path (str): Path to the folder containing the images.
        """
        total_images = len(image_files)
        for i, image_file in enumerate(image_files):
            # Get the full image path
            image_path = os.path.join(images_folder_path, image_file)
            latitude, longitude = self.get_image_location(image_path)

            # Generate thumbnail
            thumbnail = self.create_thumbnail(image_path, 50)  # Adjust size as needed

            # Update UI on the main thread using after()
            self.master.after(0, self.add_image_to_scrollable_frame, i, image_file, latitude, longitude, thumbnail)
            # Update progress bar
            self.master.after(0, self.update_progress, (i + 1) / total_images)

        self.master.after(0, self.finish_processing)  # Notify the main thread that processing is complete.

    def update_progress(self, progress):
        """Updates the progress bar."""
        if self.loading_frame and self.progressbar:
            self.progressbar.set(progress)

    def add_image_to_scrollable_frame(self, i, image_file, latitude, longitude, thumbnail):
        """Adds an image and its data to the scrollable frame.  This function runs on the main thread."""
        if self.scrollable_image_frame is None:
            return
        # Display thumbnail
        thumbnail_label = customtkinter.CTkLabel(self.scrollable_image_frame, image=thumbnail, text="")
        thumbnail_label.image = thumbnail  # Keep a reference to prevent garbage collection
        thumbnail_label.grid(row=i + 1, column=0, padx=10, pady=5, sticky="nsew")

        # Display filename
        filename_label = customtkinter.CTkLabel(self.scrollable_image_frame, text=image_file)
        filename_label.grid(row=i + 1, column=1, padx=10, pady=5, sticky="nsew")

        # Display latitude
        latitude_label = customtkinter.CTkLabel(self.scrollable_image_frame,
                                                text=str(latitude) if latitude else "N/A")
        latitude_label.grid(row=i + 1, column=2, padx=10, pady=5, sticky="nsew")

        # Display longitude
        longitude_label = customtkinter.CTkLabel(self.scrollable_image_frame,
                                                text=str(longitude) if longitude else "N/A")
        longitude_label.grid(row=i + 1, column=3, padx=10, pady=5, sticky="nsew")

    def finish_processing(self):
        """
        Called on the main thread after all images have been processed.
        """
        self.destroy_loading_frame()  # Destroy the loading frame
        #after the image list is updated, create the scrollable frame.
        if self.scrollable_image_frame is None:
            self.create_scrollable_image_frame()

    def create_thumbnail(self, image_path, size):
        """
        Creates a thumbnail image from the given image path.

        Args:
            image_path (str): Path to the image file.
            size (int): The size of the thumbnail (e.g., 50 for 50x50).

        Returns:
            CTkImage: A CTkImage object representing the thumbnail.
        """
        try:
            img = Image.open(image_path)
            # Crop the image to a square
            width, height = img.size
            if width > height:
                left = (width - height) / 2
                right = (width + height) / 2
                img = img.crop((left, 0, right, height))
            elif height > width:
                top = (height - width) / 2
                bottom = (height + width) / 2
                img = img.crop((0, top, width, bottom))

            img.thumbnail((size, size))  # Resize the image in-place
            return customtkinter.CTkImage(light_image=img, dark_image=img, size=(size,size))
        except Exception as e:
            print(f"Error creating thumbnail for {image_path}: {e}")
            return None  # Return None in case of error

    def get_image_location(self, image_path):
        """
        Extracts the latitude and longitude from the EXIF data of an image.

        Args:
            image_path (str): The path to the image file.

        Returns:
            tuple: A tuple containing (latitude, longitude).  Returns (None, None) if no EXIF data or location is found.
        """
        try:
            img = Image.open(image_path)
            if hasattr(img, '_getexif') and img._getexif() is not None:
                exif_data = img._getexif()
                #print(f"EXIF Data for {image_path}: {exif_data}")  # Print the entire EXIF data
                for tag_id, tag_value in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag_id, tag_value)
                    #print(f"Tag Name: {tag_name}, Tag Value: {tag_value}")
                    if tag_name == 'GPSInfo':
                        #print(f"GPSInfo Tag Value: {tag_value}")
                        latitude, longitude = self.get_coordinates(gps_info=tag_value)
                        return latitude, longitude
            return None, None
        except Exception as e:
            print(f"Error reading EXIF data from {image_path}: {e}")
            return None, None

    def get_coordinates(self, gps_info):
        """
        Helper function to extract latitude and longitude from GPSInfo.
        """

        def _convert_to_degrees(value):
            print(f"Value in _convert_to_degrees: {value}, type: {type(value)}")
            if isinstance(value, tuple):
                d = float(value[0])
                m = float(value[1]) / 60.0
                s = float(value[2]) / 3600.0
                return d + m + s
            elif hasattr(value, '__float__'):
                return float(value)
            else:
                return value

        latitude = None
        longitude = None
        #print(f"GPS Info in get_coordinates: {gps_info}, type: {type(gps_info)}")
        if 1 in gps_info and 2 in gps_info and 3 in gps_info and 4 in gps_info:
            latitude = _convert_to_degrees(gps_info[2])
            longitude = _convert_to_degrees(gps_info[4])
            if gps_info[1] == 'S':
                latitude = -latitude
            if gps_info[3] == 'W':
                longitude = -longitude
        return latitude, longitude

    def select_project_directory(self):
        """
        Opens a directory selection dialog and sets the selected path to the project_dir_entry.
        """
        project_directory = filedialog.askdirectory()
        if project_directory:
            # Check for the existence of the 'images' subfolder
            images_folder_path = os.path.join(project_directory, "images")
            if not os.path.isdir(images_folder_path):
                tkinter.messagebox.showerror("Error", "The selected folder does not contain an 'images' subfolder.")
                return
            self.project_dir_entry.delete(0, "end")
            self.project_dir_entry.insert(0, project_directory)
            print(f"Selected Project Directory: {project_directory}")
            self.update_image_list()  # call the function to update

    def select_model_path(self):
        """
        Opens a file selection dialog and sets the selected path to the model_path_entry.
        """
        model_path = filedialog.askopenfilename(filetypes=[("Model Files", "*.pth")])
        if model_path:
            self.model_path_entry.configure(state="normal") # Make it editable
            self.model_path_entry.delete(0, "end")
            self.model_path_entry.insert(0, model_path)
            print(f"Selected Model Path: {model_path}")
            self.model_path_entry.configure(state="readonly") # Then make it readonly again
        else:
            self.model_path_entry.configure(state="readonly") # keep it readonly if no file is selected

    def get_inputs(self):
        """
        Returns the values from the input fields.
        """
        name_of_place = self.name_entry.get().strip()
        project_directory = self.project_dir_entry.get().strip()
        model_path = self.model_path_entry.get().strip()
        return name_of_place, project_directory, model_path

    def reset_inputs(self):
        """
        Resets all input fields.
        """
        self.name_entry.delete(0, "end")
        self.project_dir_entry.delete(0, "end")
        self.model_path_entry.delete(0, "end")
        tkinter.messagebox.showinfo("Input Reset", "All input fields have been reset.")
        # Destroy the scrollable frame if it exists
        if  self.scrollable_image_frame is not None:
            self.scrollable_image_frame.destroy()
            self.scrollable_image_frame = None

        # Destroy all children of the image frame
        for child in self.image_frame.winfo_children():
            child.destroy()
        
        # Create a placeholder label.  This will be replaced with the scrollable frame when the project directory is selected.
        self.image_frame_placeholder = customtkinter.CTkLabel(self.image_frame, text="Select a project directory to view images.", text_color="grey")
        self.image_frame_placeholder.pack(fill="both", expand=True)



if __name__ == "__main__":
    # This is just for testing the InputFrame in isolation
    root = customtkinter.CTk()
    root.geometry("800x600")
    initial_frame = InitialFrame(root)
    initial_frame.pack(fill="both", expand=True, padx=20, pady=20)
    root.mainloop()

