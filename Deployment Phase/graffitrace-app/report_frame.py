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
import random
import warnings  # Import warnings

# Suppress Warnings
warnings.filterwarnings("ignore", category=UserWarning)


class ReportFrame(customtkinter.CTkFrame):
    def __init__(self, master, project_directory, **kwargs):  # Added project_directory to init
        super().__init__(master, **kwargs)

        self.project_directory = project_directory  # Store the project directory
        self.grid_columnconfigure(0, weight=1)  # Configure the column to expand
        self.grid_rowconfigure(0, weight=1)  # Make the first row expandable for the map
        self.grid_rowconfigure(1, weight=1)  # Make the second row expandable

        print(self.project_directory)

        # Create the TkinterMapView widget to display the map
        self.map_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.map_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.map_widget = TkinterMapView(self.map_frame, width=800, height=300, corner_radius=0)  # Adjust size as needed
        self.map_widget.pack(fill="both", expand=False)
        self.map_widget.set_position(37.7749, -122.4194)  # Default: San Francisco
        self.map_widget.set_zoom(15)  # reasonable default zoom

        # Create the frame for the image and details
        self.lower_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.lower_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.lower_frame.grid_columnconfigure(0, weight=1)  # Image column
        self.lower_frame.grid_columnconfigure(1, weight=2)  # Details column
        self.lower_frame.grid_rowconfigure(0, weight=1)

        # Image placeholder
        self.image_placeholder_frame = customtkinter.CTkFrame(self.lower_frame, width=200, height=200, fg_color="#383838")  # Adjust size as needed
        self.image_placeholder_frame.grid(row=0, column=0, padx=(0, 20), pady=0, sticky="nsew")
        self.image_placeholder_label = customtkinter.CTkLabel(self.image_placeholder_frame, text_color="white", text="", width=225)
        self.image_placeholder_label.pack(fill="both", expand=True)
        self.image_label = None  # keep track of the image label

        # Details frame
        self.details_frame = customtkinter.CTkFrame(self.lower_frame, fg_color="transparent")
        self.details_frame.grid(row=0, column=1, padx=0, pady=(0, 10), sticky="w")
        self.details_frame.grid_columnconfigure(0, weight=1)
        self.details_frame.grid_columnconfigure(1, weight=2)

        # New frame on the right. Moved to the lower frame.
        self.right_frame = customtkinter.CTkFrame(self.lower_frame, fg_color="transparent", corner_radius=10)
        self.right_frame.grid(row=0, column=2, padx=(20, 0), pady=(0, 30), sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)  # Ensure the column expands
        self.right_frame.grid_rowconfigure(0, weight=1)  # Don't give weight to the rows initially.
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_rowconfigure(2, weight=1)

        # Load the custom icon
        current_path = os.path.dirname(os.path.abspath(__file__))
        random_icon_path = os.path.join(current_path, "assets", "random.png")
        info_icon_path = os.path.join(current_path, "assets", "info.png")
        print_icon_path = os.path.join(current_path, "assets", "print.png")

        try:
            self.random_image = Image.open(random_icon_path).resize((30, 30), Image.LANCZOS)
            self.random_icon = ImageTk.PhotoImage(self.random_image)
            self.info_image = Image.open(info_icon_path).resize((30, 30), Image.LANCZOS)
            self.info_icon = ImageTk.PhotoImage(self.info_image)
            self.print_image = Image.open(print_icon_path).resize((30, 30), Image.LANCZOS)
            self.print_icon = ImageTk.PhotoImage(self.print_image)
        except Exception as e:
            print(f"Error loading icon: {e}.  Using default marker.")
            self.random_icon = None  # Ensure None in case of error
            self.info_icon = None  # Ensure None in case of error
            self.print_icon = None  # Ensure None in case of error

        # Create three buttons inside the right frame
        self.random_button = customtkinter.CTkButton(self.right_frame, text="", corner_radius=8, image=self.random_icon,
                                                    command=self.on_random_button_click, width=50, height=60, fg_color="transparent")
        self.random_button.pack(fill="both", expand=False, pady=(10, 10), padx=15)  # Use pack, fill horizontally, no expansion
        self.info_button = customtkinter.CTkButton(self.right_frame, text="", corner_radius=8, image=self.info_icon, width=50, height=60, fg_color="transparent")
        self.info_button.pack(fill="both", expand=False, pady=5, padx=15)
        self.print_button = customtkinter.CTkButton(self.right_frame, text="", corner_radius=8, image=self.print_icon, width=50, height=60, fg_color="transparent")
        self.print_button.pack(fill="both", expand=False, pady=(10, 18), padx=15)

        # Labels for the details
        label_texts = ["Graffiti ID", "Source File Name", "Place", "Latitude", "Longitude", "Confidence Level"]
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
        self.graffiti_data = []  # added
        self.load_data()  # Load data in init
        self.markers = []

    def load_data(self):
        """Loads the data"""
        csv_path = os.path.join(self.project_directory, "results", "results.csv")

        print(csv_path)

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
            required_columns = ["graffiti_id", "source_file_name", "place", "latitude", "longitude", "num_graffiti_instances"]
            if not all(col in self.graffiti_data.columns for col in required_columns):
                raise ValueError(f"CSV file is missing one or more required columns: {', '.join(required_columns)}")

            # Convert latitude and longitude to numeric
            self.graffiti_data['latitude'] = pd.to_numeric(self.graffiti_data['latitude'], errors='coerce')
            self.graffiti_data['longitude'] = pd.to_numeric(self.graffiti_data['longitude'], errors='coerce')

            # Drop rows where latitude or longitude are NaN after conversion
            self.graffiti_data.dropna(subset=['latitude', 'longitude'], inplace=True)

            self.coordinates = list(zip(self.graffiti_data['latitude'], self.graffiti_data['longitude']))

            self.create_map()

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
        Destroys all widgets in the lower frame, except for self.right_frame and its children.
        """
        for child in self.lower_frame.winfo_children():
            if child != self.right_frame:  # Skip the right frame
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
        self.details_frame.grid(row=0, column=1, padx=0, pady=(0, 5), sticky="nsew")
        self.details_frame.grid_columnconfigure(0, weight=1)
        self.details_frame.grid_columnconfigure(1, weight=2)
        self.details_frame.grid_rowconfigure(0, weight=1)
        self.details_frame.grid_rowconfigure(1, weight=1)
        self.details_frame.grid_rowconfigure(2, weight=1)
        self.details_frame.grid_rowconfigure(3, weight=1)
        self.details_frame.grid_rowconfigure(4, weight=1)
        self.details_frame.grid_rowconfigure(5, weight=1)

        # Re-create labels for the details
        label_texts = ["Graffiti Name", "Source File Name", "Place", "Latitude", "Longitude", "Graffiti Instances"]
        self.detail_labels = []
        self.detail_values = []
        for i, text in enumerate(label_texts):
            label = customtkinter.CTkLabel(self.details_frame, text=text + ":", anchor="w")
            label.grid(row=i, column=0, padx=5, pady=(2.5, 2.5), sticky="ew")
            value_label = customtkinter.CTkLabel(self.details_frame, text="", anchor="w")  # Start with empty values
            value_label.grid(row=i, column=1, padx=10, pady=(2.5, 2.5), sticky="ew")
            self.detail_labels.append(label)
            self.detail_values.append(value_label)

        if 0 <= index < len(self.coordinates):
            # Get the graffiti details from the dataframe
            graffiti_name = self.graffiti_data.iloc[index]['graffiti_id']
            source_file_name = self.graffiti_data.iloc[index]['source_file_name']
            place = self.graffiti_data.iloc[index]['place']
            latitude = self.graffiti_data.iloc[index]['latitude']
            longitude = self.graffiti_data.iloc[index]['longitude']
            num_graffiti_instances = self.graffiti_data.iloc[index]['num_graffiti_instances']

            details = [graffiti_name, source_file_name, place, latitude, longitude, num_graffiti_instances]

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
        image_path = os.path.join(image_folder_path, graffiti_name + ".jpg")

        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                # Calculate aspect ratio
                aspect_ratio = img.width / img.height
                # Use the available height (200) to determine the new width
                new_width = int(325 * aspect_ratio)
                img.thumbnail((new_width, 325))  # Resize for the placeholder
                photo = ImageTk.PhotoImage(img)

                # Create image label
                image_label = customtkinter.CTkLabel(self.lower_frame, image=photo, text="")
                image_label.image = photo
                image_label.grid(row=0, column=0, padx=(0, 20), pady=0, sticky="nsew")  # Place the image

                # Make the image label clickable
                image_label.bind("<Button-1>", lambda event, path=image_path: self.on_image_click(event, path))  # Pass the image path
                image_label.configure(cursor="hand2")  # Change cursor to a pointer

                # Destroy the placeholder frame
                if self.image_placeholder_frame:  # Check if it exists before destroying
                    self.image_placeholder_frame.destroy()
                self.image_placeholder_frame = None  # Set it to None to indicate it's no longer there.
                self.image_label = image_label  # store the image_label

            except Exception as e:
                print(f"Error loading image {image_path}: {e}")
                self.clear_image_placeholder()  # This will now create a new placeholder if needed.
                self.image_placeholder_frame.grid_configure(padx=125)
                self.image_placeholder_label.configure(text="Error loading image")
        else:
            self.clear_image_placeholder()
            self.image_placeholder_frame.grid_configure(padx=125)
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

    def on_image_click(self, event, image_path):
        """
        Opens the full-size image in a new popup window.

        Args:
            event (tkinter.Event): The click event.
            image_path (str): The path to the image.
        """
        try:
            # Create a new top-level window (popup)
            popup_window = customtkinter.CTkToplevel(self)
            popup_window.title("Graffiti Image Viewer")

            # Open the image using PIL
            img = Image.open(image_path)
            # Calculate the aspect ratio to fit the image within a maximum size
            max_width = 800  # You can adjust these values
            max_height = 800
            img.thumbnail((max_width, max_height), Image.LANCZOS)  # Resize while maintaining aspect ratio
            photo = ImageTk.PhotoImage(img)

            # Create a label to display the image in the popup
            image_label = customtkinter.CTkLabel(popup_window, image=photo, text="")
            image_label.image = photo  # Keep a reference to the PhotoImage to prevent it from being garbage collected
            image_label.pack(padx=10, pady=10, fill="both", expand=True)  # Use pack or grid as needed

            # Make the popup window resizable
            popup_window.resizable(True, True)

            # Center the popup window on the screen
            screen_width = popup_window.winfo_screenwidth()
            screen_height = popup_window.winfo_screenheight()
            popup_width = img.width if img.width < max_width else max_width
            popup_height = img.height if img.height < max_height else max_height
            x = (screen_width / 2) - (popup_width / 2)
            y = (screen_height / 2) - (popup_height / 2)
            popup_window.geometry(f"{popup_width}x{popup_height}+{int(x)}+{int(y)}")

        except Exception as e:
            tkinter.messagebox.showerror("Error", f"Error opening image: {e}")

    def on_random_button_click(self):
        """
        Selects a random graffiti entry, updates the details frame, and zooms the map.
        """
        if not self.coordinates:
            tkinter.messagebox.showinfo("No Data", "No graffiti data available to select.")
            return

        random_index = random.randint(0, len(self.coordinates) - 1)
        self.update_details_frame(random_index)

        # Zoom to the selected marker's position.
        latitude, longitude = self.coordinates[random_index]
        self.map_widget.set_position(latitude, longitude)
        self.map_widget.set_zoom(19)


if __name__ == "__main__":
    # This is just for testing the InputFrame in isolation
    root = customtkinter.CTk()
    root.geometry("800x600")
    # Example Usage
    test_dir = r"C:\Users\MB-PC\Downloads\Test"  # hardcoded
    report_frame = ReportFrame(root, test_dir)  # Pass the directory
    report_frame.pack(fill="both", expand=True, padx=20, pady=20)
    report_frame.create_map()  # create map
    root.mainloop()
