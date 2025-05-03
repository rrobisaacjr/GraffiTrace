import tkinter
import customtkinter
from tkinter import filedialog
import os
from PIL import Image, ExifTags, ImageTk  # Import PIL for image processing
import threading  # Import the threading module
from customtkinter import CTkScrollableFrame, CTkLabel  # Import CTkScrollableFrame and CTkLabel
try:
    from tkinter import ttk
except ImportError:
    import tkinter.ttk as ttk
from tkintermapview import TkinterMapView  # Import the map view
import tkinter.messagebox  # Import messagebox
import pandas as pd
import warnings  # Import warnings

# Suppress Warnings
warnings.filterwarnings("ignore", category=UserWarning)


class ReportFrame(customtkinter.CTkFrame):
    def __init__(self, master, project_directory, **kwargs): # Added project_directory to init
        super().__init__(master, **kwargs)

        self.project_directory = project_directory # Store the project directory
        self.grid_columnconfigure(0, weight=1)  # Configure the column to expand
        self.grid_rowconfigure(0, weight=1)  # Make the first row expandable for the map
        self.grid_rowconfigure(1, weight=1)  # Make the second row expandable

        # Create the TkinterMapView widget to display the map
        self.map_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.map_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.map_widget = TkinterMapView(self.map_frame, width=800, height=300, corner_radius=0)  # Adjust size as needed
        self.map_widget.pack(fill="both", expand=True)
        self.map_widget.set_position(37.7749, -122.4194)  # Default: San Francisco
        self.map_widget.set_zoom(15)  # reasonable default zoom

        # Create the frame for the image and details
        self.lower_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.lower_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.lower_frame.grid_columnconfigure(0, weight=1)  # Image column
        self.lower_frame.grid_columnconfigure(1, weight=2)  # Details column

        # Image placeholder
        self.image_placeholder_frame = customtkinter.CTkFrame(self.lower_frame, width=200, height=200, fg_color="#383838")  # Adjust size as needed
        self.image_placeholder_frame.grid(row=0, column=0, padx=(0, 20), pady=0, sticky="nsew")
        self.image_placeholder_label = customtkinter.CTkLabel(self.image_placeholder_frame, text_color="white")
        self.image_placeholder_label.pack(fill="both", expand=True)
        self.image_label = None #keep track of the image label

        # Details frame
        self.details_frame = customtkinter.CTkFrame(self.lower_frame, fg_color="transparent")
        self.details_frame.grid(row=0, column=1, padx=0, pady=(0, 10), sticky="w")
        self.details_frame.grid_columnconfigure(0, weight=1)
        self.details_frame.grid_columnconfigure(1, weight=2)
        
        # New frame on the right
        self.right_frame = customtkinter.CTkFrame(self.lower_frame, fg_color="#383838", corner_radius=10, width=50)  # Example color
        self.right_frame.grid(row=0, column=2, padx=(20, 0), pady=(0, 20), sticky="ns")
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(0, weight=1)
        
        # Create three buttons inside the right frame
        self.button1 = customtkinter.CTkButton(self.right_frame, text="", width=60, height=60, corner_radius=8, fg_color="gray")
        self.button1.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nsew")

        self.button2 = customtkinter.CTkButton(self.right_frame, text="", width=60, height=60, corner_radius=8, fg_color="gray")
        self.button2.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        self.button3 = customtkinter.CTkButton(self.right_frame, text="", width=60, height=60, corner_radius=8, fg_color="gray")
        self.button3.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="nsew")

        # Labels for the details
        label_texts = ["Graffiti Name", "Source File Name", "Place", "Latitude", "Longitude", "Confidence Level"]
        self.detail_labels = []
        self.detail_values = []

        for i, text in enumerate(label_texts):
            label = customtkinter.CTkLabel(self.details_frame, text=text + ":", anchor="w")
            label.grid(row=i, column=0, padx=10, pady=(5, 5), sticky="ew")
            value_label = customtkinter.CTkLabel(self.details_frame, text="", anchor="w")  # Start with empty values
            value_label.grid(row=i, column=1, padx=10, pady=(5, 5), sticky="ew")
            self.detail_labels.append(label)
            self.detail_values.append(value_label)

        self.coordinates = []
        self.coordinates = []
        self.graffiti_data = [] #added
        self.load_data() # Load data in init
        
    def load_data(self):
        """Loads the data"""
        csv_path = os.path.join(self.project_directory, "results", "result.csv")
        self.load_graffiti_data(csv_path)

    def load_graffiti_data(self, csv_path):
        """
        Loads graffiti data from a CSV file.

        Args:
            csv_path (str): Path to the CSV file.
        """
        try:
            self.graffiti_data = pd.read_csv(csv_path)
            # Ensure the necessary columns exist
            required_columns = ["graffiti_id", "source_file_name", "place", "latitude", "longitude", "confidence_level"]
            if not all(col in self.graffiti_data.columns for col in required_columns):
                raise ValueError(f"CSV file is missing one or more required columns: {', '.join(required_columns)}")

            # Convert latitude and longitude to numeric
            self.graffiti_data['latitude'] = pd.to_numeric(self.graffiti_data['latitude'], errors='coerce')
            self.graffiti_data['longitude'] = pd.to_numeric(self.graffiti_data['longitude'], errors='coerce')

            # Drop rows where latitude or longitude are NaN after conversion
            self.graffiti_data.dropna(subset=['latitude', 'longitude'], inplace=True)

            self.coordinates = list(zip(self.graffiti_data['latitude'], self.graffiti_data['longitude']))

        except FileNotFoundError:
            tkinter.messagebox.showerror("Error", f"CSV file not found at {csv_path}")
            self.graffiti_data = pd.DataFrame()  # Initialize to empty DataFrame
            self.coordinates = []
        except ValueError as e:
            tkinter.messagebox.showerror("Error", f"Error reading CSV file: {e}")
            self.graffiti_data = pd.DataFrame()
            self.coordinates = []

    def create_map(self):
        """
        Creates a TkinterMapView map centered on the graffiti coordinates and adds markers.
        """
        if not self.coordinates:
            # Handle the case where there are no coordinates
            self.map_widget.set_address("San Francisco, CA")  # set to a default address.
            return

        # Get the average latitude and longitude to center the map
        latitudes = [coord[0] for coord in self.coordinates]
        longitudes = [coord[1] for coord in self.coordinates]
        center_lat = sum(latitudes) / len(latitudes)
        center_lon = sum(longitudes) / len(longitudes)

        self.map_widget.set_position(center_lat, center_lon)

        # Load the custom icon
        current_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_path, "assets", "pin.png")  # Adjust the path if needed
        try:
            pin_image = Image.open(icon_path).resize((30, 30), Image.LANCZOS)  # resizing
            self.marker_icon = ImageTk.PhotoImage(pin_image)
        except Exception as e:
            print(f"Error loading icon: {e}.  Using default marker.")
            self.marker_icon = None  # Ensure self.marker_icon is None in case of error

        # Add markers for each coordinate
        for i, (lat, lon) in enumerate(self.coordinates):
            # Use a lambda function to capture the current index i
            marker_click_event = lambda marker=None, index=i: self.update_details_frame(index)
            marker = self.map_widget.set_marker(lat, lon, icon=self.marker_icon, command=marker_click_event)

        # set a reasonable zoom level
        self.map_widget.set_zoom(17)

    def clear_lower_frame(self):
        """
        Destroys all widgets in the lower frame.
        """
        for child in self.lower_frame.winfo_children():
            child.destroy()
        self.image_label = None
        self.image_placeholder_frame = None

    def update_details_frame(self, index):
        """
        Updates the details frame with information for the selected graffiti index.

        Args:
            index (int): The index of the graffiti in the coordinates list.
        """
        self.clear_lower_frame()  # Clear the lower frame before updating it

        # Recreate the structure of the lower frame
        self.image_placeholder_frame = customtkinter.CTkFrame(self.lower_frame, width=200, height=200,
                                                            fg_color="#383838",
                                                            corner_radius=10)  # Adjust size as needed
        self.image_placeholder_frame.grid(row=0, column=0, padx=(0, 20), pady=0, sticky="nsew")
        self.image_placeholder_label = customtkinter.CTkLabel(self.image_placeholder_frame,
                                                            text_color="white")  # Keep this for "No Image"
        self.image_placeholder_label.pack(fill="both", expand=True)

        self.details_frame = customtkinter.CTkFrame(self.lower_frame, fg_color="transparent")
        self.details_frame.grid(row=0, column=1, padx=0, pady=(0, 10), sticky="nsew")
        self.details_frame.grid_columnconfigure(0, weight=1)
        self.details_frame.grid_columnconfigure(1, weight=2)

        # Re-create labels for the details
        label_texts = ["Graffiti Name", "Source File Name", "Place", "Latitude", "Longitude", "Confidence Level"]
        self.detail_labels = []
        self.detail_values = []
        for i, text in enumerate(label_texts):
            label = customtkinter.CTkLabel(self.details_frame, text=text + ":", anchor="w")
            label.grid(row=i, column=0, padx=10, pady=(5, 5), sticky="ew")
            value_label = customtkinter.CTkLabel(self.details_frame, text="", anchor="w")  # Start with empty values
            value_label.grid(row=i, column=1, padx=10, pady=(5, 5), sticky="ew")
            self.detail_labels.append(label)
            self.detail_values.append(value_label)

        if 0 <= index < len(self.coordinates):
            # Get the graffiti details from the dataframe
            graffiti_name = self.graffiti_data.iloc[index]['graffiti_id']
            source_file_name = self.graffiti_data.iloc[index]['source_file_name']
            place = self.graffiti_data.iloc[index]['place']
            latitude = self.graffiti_data.iloc[index]['latitude']
            longitude = self.graffiti_data.iloc[index]['longitude']
            confidence_level = self.graffiti_data.iloc[index]['confidence_level']

            details = [graffiti_name, source_file_name, place, latitude, longitude, confidence_level]

            for i, value in enumerate(details):
                self.detail_values[i].configure(text=str(value))

            # Update the image display
            self.update_image_placeholder(graffiti_name)
        else:
            # Clear the detail values if the index is out of range
            for value_label in self.detail_values:
                value_label.configure(text="")
            self.clear_image_placeholder()  # Clear image.

    def update_image_placeholder(self, graffiti_name):
        """
        Updates the image placeholder with the image corresponding to the graffiti name.
        Replaces the placeholder frame with the image.

        Args:
            graffiti_name (str): The name of the graffiti.
        """
        image_folder_path = os.path.join(self.project_directory, "results", "graffiti_instances")  # corrected path
        image_path = os.path.join(image_folder_path, graffiti_name + ".png")  # Assuming .png, adjust as needed

        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                # Calculate aspect ratio
                aspect_ratio = img.width / img.height
                # Use the available height (200) to determine the new width
                new_width = int(200 * aspect_ratio)
                img.thumbnail((new_width, 200))  # Resize for the placeholder
                photo = ImageTk.PhotoImage(img)

                # Create image label
                image_label = customtkinter.CTkLabel(self.lower_frame, image=photo, text="")
                image_label.image = photo
                image_label.grid(row=0, column=0, padx=(0, 20), pady=0, sticky="nsew")  # Place the image

                # Destroy the placeholder frame
                if self.image_placeholder_frame:  # Check if it exists before destroying
                    self.image_placeholder_frame.destroy()
                self.image_placeholder_frame = None  # Set it to None to indicate it's no longer there.
                self.image_label = image_label  # store the image_label

            except Exception as e:
                print(f"Error loading image {image_path}: {e}")
                self.clear_image_placeholder()  # This will now create a new placeholder if needed.
                self.image_placeholder_label.configure(text="Error loading image")
        else:
            self.clear_image_placeholder()
            self.image_placeholder_label.configure(text="Image not found")

    def clear_image_placeholder(self):
        """
        Clears the image placeholder.  Destroys any existing image and creates a new placeholder frame.
        """
        if self.image_label:
            self.image_label.destroy()
            self.image_label = None

        # Create a new placeholder frame.
        self.image_placeholder_frame = customtkinter.CTkFrame(self.lower_frame, width=300, height=200, fg_color="#383838",
                                                            corner_radius=10)
        self.image_placeholder_frame.grid(row=0, column=0, padx=(0, 20), pady=0, sticky="nsew")
        self.image_placeholder_label = customtkinter.CTkLabel(self.image_placeholder_frame, text_color="white")
        self.image_placeholder_label.pack(fill="both", expand=True)
        self.image_placeholder_label.configure(text="")  # Clear any previous text.



if __name__ == "__main__":
    # This is just for testing the InputFrame in isolation
    root = customtkinter.CTk()
    root.geometry("800x600")
    # Example Usage
    test_dir = r"D:\Downloads\SP\Test" #hardcoded
    report_frame = ReportFrame(root, test_dir)  # Pass the directory
    report_frame.pack(fill="both", expand=True, padx=20, pady=20)
    report_frame.create_map() #create map
    root.mainloop()
