#eclipse_hdr_timelapse.py

# Import modules
import cv2
from config import *
from timelapse_hdr import *

print('Starting acquisition...')
exposure_times = [2 ** base for base in EXPOSURE_BASES]
formatted_exposure_times = [f"{time:.5f}" if time < 1 else str(int(time)) for time in exposure_times]
print('Camera exposures:')
# Print the list of all timepoints
for exp in formatted_exposure_times:
    print(exp)

# Initialize camera
camera = cv2.VideoCapture(0)

# Extract datetime objects
print('Eclipse timepoints:')
extracted_datetimes = extract_datetime(ECLIPSE_TEXT, YEAR)
for dt in extracted_datetimes:
    print(dt)

if TEST_RUN:
    TEST_OFFSET = -3.5 #h
    print(f'Test run of eclipse timelapse today with {TIMELAPSE_INTERVAL}s intervals, offset {TEST_OFFSET}h from actual time of eclipse.')
  
    # Change each of the datetime objects to be for today (FOR TESTING)
    today = datetime.now().date()
    datetimes_for_today = [datetime.combine(today, dt.time()) for dt in extracted_datetimes]

    # Offset the timepoints around the eclipse a user-defined amount
    adjusted_timepoints = [tp + timedelta(hours=TEST_OFFSET) for tp in datetimes_for_today]

    # Now create 1min intervals centered on the middle one.
    centered_timepoints = generate_centered_timepoints(adjusted_timepoints, TIMELAPSE_INTERVAL)


# Otherwise use the real eclipse date and time
else:

    # Now create 1min intervals centered on the middle one.
    centered_timepoints = generate_centered_timepoints(extracted_datetimes, TIMELAPSE_INTERVAL)

print('A list of all timepoints to be captured:')
# Add a timepoint for 1 minute from now at the start to test the aquisition is running properly
one_minute_from_now = datetime.now() + timedelta(minutes=1)
if one_minute_from_now < centered_timepoints[0]:
    centered_timepoints.insert(0, one_minute_from_now)

# Print the list of all timepoints
for tp in centered_timepoints:
    print(tp)


print('--------')
print('Starting the acquisition...')
print('Please pay attention for the next minute to ensure the acquisition starts correctly andoutputs files. If it fails, then check your camera and re-start the script.')

if camera.isOpened():

    timed_capture(camera, BASE_OUTPUT_FOLDER, EXPOSURE_BASES, centered_timepoints, label='eclipse')
    # camera.release()
else:
    print("Camera could not be initialized.")