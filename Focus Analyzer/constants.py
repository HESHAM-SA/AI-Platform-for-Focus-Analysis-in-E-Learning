import cv2 as cv

# =========================
# Global Variables
# =========================
FONTS = cv.FONT_HERSHEY_SIMPLEX
# CENTER_THRESHOLD = 0.5
# SIDE_THRESHOLD = 3
# BLINK_THRESHOLD = 2
# DISCOUNT_CENTER = 0.3
# DISCOUNT_SIDE = 0.3
# DISCOUNT_EYES = 0.5

class Config:
    def __init__(self):
        self.CENTER_THRESHOLD = 0.5
        self.SIDE_THRESHOLD = 3
        self.BLINK_THRESHOLD = 3
        self.DISCOUNT_CENTER = 0.3
        self.DISCOUNT_SIDE = 0.3
        self.DISCOUNT_EYES = 0.5



# Create a single instance to share across files
config = Config()

LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249,
            263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155,
             133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# Initialize global variables for tracking
focus_score = 50  # Initialized start focus from 50
last_look_centered_time = None
not_looking_start_time = None
blink_start_time = None
total_blinks = 0
blink_detected = False
eyes_closed_start_time = None
# Variables to track the last time we increased or decreased the focus score
last_focus_increase_time = None
last_focus_decrease_time = None

# Initialize Whisper model and OpenAI API key placeholder
model = None  # We will load the model when needed
openai_api_key = None  # We will prompt the user to enter the API key