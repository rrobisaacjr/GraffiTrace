import tkinter
import customtkinter
from tkinter import filedialog
import os
from PIL import Image, ExifTags, ImageTk  # Import PIL for image processing
import threading  # Import the threading module
# import folium  # Import Folium - Removed
from customtkinter import CTkScrollableFrame, CTkLabel  # Import CTkScrollableFrame and CTkLabel
try:
    from tkinter import ttk
except ImportError:
    import tkinter.ttk as ttk
from tkintermapview import TkinterMapView # Import the map view
import tkinter.messagebox # Import messagebox


class ReportFrame(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_columnconfigure(0, weight=1)  # Configure the column to expand
        self.grid_rowconfigure(0, weight=1)  # Make the first row expandable for the map
        self.grid_rowconfigure(1, weight=1) # Make the second row expandable

        # Create the TkinterMapView widget to display the map
        self.map_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.map_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.map_widget = TkinterMapView(self.map_frame, width=800, height=400, corner_radius=0)  # Adjust size as needed
        self.map_widget.pack(fill="both", expand=True)
        self.map_widget.set_position(37.7749, -122.4194)  # Default: San Francisco
        self.map_widget.set_zoom(10)  # reasonable default zoom

        # Create a dummy frame for the lower half.  This is just a placeholder for now.  You can
        # add your table or other content here.
        self.lower_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.lower_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.lower_label = customtkinter.CTkLabel(self.lower_frame, text="Lower Frame Content Placeholder",
                                                  text_color="grey")  # Placeholder
        self.lower_label.pack(fill="both", expand=True)
        self.coordinates = []

    def create_map(self, coordinates):
        """
        Creates a Folium map centered on the given coordinates and adds markers.

        Args:
            coordinates (list of tuples): A list of (latitude, longitude) tuples.
        """
        self.coordinates = coordinates
        if not coordinates:
            # Handle the case where there are no coordinates
             self.map_widget.set_address("San Francisco, CA") #set to a default address.
             return

        # Get the average latitude and longitude to center the map
        latitudes = [coord[0] for coord in coordinates]
        longitudes = [coord[1] for coord in coordinates]
        center_lat = sum(latitudes) / len(latitudes)
        center_lon = sum(longitudes) / len(longitudes)

        self.map_widget.set_position(center_lat, center_lon)

        # Add markers for each coordinate
        for i, (lat, lon) in enumerate(coordinates):
            def marker_click_event(marker=None, marker_num=i+1):  # Changed the signature
                print(f"Marker {marker_num} clicked!")  # Example action: print to console
                tkinter.messagebox.showinfo("Marker Clicked", f"Graffiti Location {marker_num} clicked!") #show a message box

            marker = self.map_widget.set_marker(lat, lon, text=f"Graffiti {i+1}", marker_color_circle="red", marker_color_outside="black", command=marker_click_event)

        #set a reasonable zoom level
        self.map_widget.set_zoom(15)

if __name__ == "__main__":
    # This is just for testing the InputFrame in isolation
    root = customtkinter.CTk()
    root.geometry("800x600")
    report_frame = ReportFrame(root)
    report_frame.pack(fill="both", expand=True, padx=20, pady=20)
    # Example usage:
    # coordinates = [(37.7749, -122.4194), (34.0522, -118.2437), (40.7128, -74.0060)]  # Example coordinates
    coordinates = [(10.29551111111111, 123.89997500000001),
                   (10.294783333333333, 123.90085833333333),
                   (10.295669444444444, 123.89964444444445),
                   (10.295619444444444, 123.8994388888889),
                   (10.29545, 123.89938333333335),
                   (10.2951, 123.89927777777778),
                   (10.295013888888889, 123.89925000000001)]
    report_frame.create_map(coordinates)
    root.mainloop()
