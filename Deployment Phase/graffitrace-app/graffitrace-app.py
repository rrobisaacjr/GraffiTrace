import tkinter
import tkinter.messagebox
import customtkinter
from initial_frame import InitialFrame
from report_frame import ReportFrame
import os
import data_preprocessing
from PIL import Image  # Import  Image
import warnings  # Import warnings

# Suppress Warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=Image.DecompressionBombWarning)


customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

customtkinter.FontManager.load_font("fonts/Inter_18pt-Regular")


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("GraffiTrace: Graffiti Image Detection Geoplot Reporter")
        self.geometry(f"{1100}x620")
        self.resizable(False, False)

        # configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)

        # Create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=3, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        self.logo_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="GraffiTrace",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.sidebar_button_1 = customtkinter.CTkButton(
            self.sidebar_frame, text="Settings", command=self.sidebar_button_event
        )
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        self.sidebar_button_2 = customtkinter.CTkButton(
            self.sidebar_frame, text="Help", command=self.sidebar_button_event
        )
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)
        self.appearance_mode_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Appearance Mode:", anchor="w"
        )
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode_event,
        )
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(10, 10))
        self.scaling_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="UI Scaling:", anchor="w"
        )
        self.scaling_label.grid(row=8, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["80%", "90%", "100%", "110%", "120%"],
            command=self.change_scaling_event,
        )
        self.scaling_optionemenu.grid(row=9, column=0, padx=20, pady=(10, 20))

        # Create input frame
        self.initial_frame = InitialFrame(
            self, corner_radius=10
        )  # Use the imported InitialFrame
        self.initial_frame.grid(row=0, column=1, padx=20, pady=(20, 0), sticky="nsew")

        # Create button frame for reset and submit
        self.button_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.button_frame.grid(row=1, column=1, padx=20, pady=20, sticky="ew")
        self.button_frame.columnconfigure(0, weight=1)
        self.button_frame.columnconfigure(1, weight=1)

        # Create reset and submit buttons
        self.reset_button = customtkinter.CTkButton(
            self.button_frame, text="Reset", command=self.reset_inputs
        )
        self.reset_button.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        self.submit_button = customtkinter.CTkButton(
            self.button_frame, text="Submit", command=self.click_submit
        )
        self.submit_button.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ew")

        # Create the new label and button frame, but hide them initially
        self.report_generation_frame = customtkinter.CTkFrame(self, corner_radius=10)  # Lighter color frame
        self.report_generation_frame.grid(row=0, column=1, padx=20, pady=(20, 0),
                                           sticky="nsew")  # Added grid
        self.report_generation_label = customtkinter.CTkLabel(
            self.report_generation_frame, #place the label in the new frame
            text="Data preprocessing complete.  Proceed with report generation.",
            font=customtkinter.CTkFont(size=18),
        )
        self.report_generation_label.pack(padx=20, pady=(20, 0),
                                         fill="both", expand=True) #use pack to place label inside frame
        self.report_generation_frame.grid_remove()  # Hide initially

        self.proceed_button_frame = customtkinter.CTkFrame(self, corner_radius=10)  # Lighter color
        self.proceed_button_frame.grid(row=1, column=1, padx=20, pady=20,
                                       sticky="ew")  # Added grid
        self.proceed_button_frame.columnconfigure(0, weight=1)
        self.proceed_button = customtkinter.CTkButton(
            self.proceed_button_frame, text="Proceed", command=self.proceed_to_report
        )
        self.proceed_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.proceed_button_frame.grid_remove()  # Hide initially

        # Set default values
        self.appearance_mode_optionemenu.set("Dark")
        self.scaling_optionemenu.set("100%")

        self.report_frame = None # Initialize report frame

    def click_submit(self):
        """
        Collects input from the InputFrame and generates a report.
        """
        name_of_place, project_directory, model_path = self.initial_frame.get_inputs()  # Get data from input frame

        # Input validation
        if not name_of_place:
            tkinter.messagebox.showerror(
                "Input Error", "Please enter the Name of Place."
            )
            return
        if not project_directory:
            tkinter.messagebox.showerror(
                "Input Error", "Please enter the Project Directory."
            )
            return
        if not os.path.isdir(project_directory):
            tkinter.messagebox.showerror(
                "Input Error", "Invalid Project Directory.  Please enter a valid path."
            )
            return
        if not model_path:
            tkinter.messagebox.showerror("Input Error", "Please enter the Model Path.")
            return
        if not os.path.isfile(model_path):
            tkinter.messagebox.showerror(
                "Input Error", "Invalid Model Path. Please enter a valid file path."
            )
            return

        # Call the function from data_preprocessing.py
        data_preprocessing.run_data_preprocessing(project_directory)

        # Destroy input frames after successful processing
        self.initial_frame.destroy()
        self.button_frame.destroy()

        # Show the report generation label and button
        self.report_generation_frame.grid()  # Show the frame
        self.proceed_button_frame.grid()  # Show the button frame

    def proceed_to_report(self):
        """
        This function will be called when the "Proceed" button is clicked.
        You can add your report generation logic here.
        For now, it just prints a message.
        """
        print("Proceeding to report generation...")
        
        if self.report_frame is None:
            self.report_frame = ReportFrame(self)
        self.report_frame.grid(row=0, column=1, padx=20, pady=(20, 20), sticky="nsew")
        self.report_generation_frame.destroy()
        self.proceed_button_frame.destroy()

    def reset_inputs(self):
        self.initial_frame.reset_inputs()  # call the reset function of the input frame

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    def sidebar_button_event(self):
        print("sidebar_button click")


if __name__ == "__main__":
    app = App()
    app.mainloop()
