
import os
import cv2
import numpy as np
import time
import re
from datetime import datetime, timedelta
import glob
import matplotlib.pyplot as plt


def capture_photos(camera, base_output_folder, exposure_times, label='test', delay_between_exposures=0.5):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_folder = os.path.join(base_output_folder, f"{label}_{timestamp}")
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created folder {output_folder}")

    if not camera.isOpened():
        print("Error: Failed to open the camera.")
        return

    print(f"Starting acquisition: {timestamp}")

   # Camera warm-up
    for _ in range(5):
        camera.read()
    success = True  # Flag to track if all captures were successful
    for i, exp in enumerate(exposure_times):
        
        camera.set(cv2.CAP_PROP_EXPOSURE, float(exp))
        ret, frame = camera.read()


        # Flush the buffer
        for _ in range(3):
            ret, frame = camera.read()

        # if ret:
        #     file_name = f"{output_folder}/{label}_{i}.png"
        #     cv2.imwrite(file_name, frame)
        #     print(f"Image {i} saved at {file_name}")
        #     time.sleep(delay_between_exposures)  # Delay added here

        # else:
        #     print(f"Error: Failed to capture image {i}.")

        if ret:
            file_name = f"{output_folder}/{label}_{i}.png"
            cv2.imwrite(file_name, frame)
        else:
            success = False  # Capture was not successful
            # break  # Exit the loop if an image fails to capture
        time.sleep(delay_between_exposures)

    # Print a single message summarizing the results of the captures
    if success:
        print(f"All images successfully captured for timepoint: {timestamp}")
    else:
        print(f"Image capture failed at timepoint: {timestamp}")






# Adjusted function for timed acquisitions
def timed_capture(camera, base_output_folder, exposure_times, timepoints, label='test'):
    timepoints.sort()
    current_timepoint_index = 0
    
    while current_timepoint_index < len(timepoints):
        now = datetime.now()
        if now >= timepoints[current_timepoint_index] and now <= timepoints[current_timepoint_index] + timedelta(seconds=30):
            capture_photos(camera, base_output_folder, exposure_times, label)
            current_timepoint_index += 1
        elif now > timepoints[current_timepoint_index]:
            current_timepoint_index += 1
        else:
            time.sleep(10)

    print("Completed all timepoints.")


def extract_datetime(text, year):
    date_format = "%b %d at %I:%M:%S %p %Y"
    # Regex pattern to match the given date format
    pattern = r"([A-Za-z]{3} \d{1,2} at \d{1,2}:\d{2}:\d{2} [apm]{2})"
    
    # Extract all matching date strings
    date_strings = re.findall(pattern, text)
    
    # Convert all date strings to datetime objects
    datetime_objects = []
    for date_string in date_strings:
        date_time_str = f"{date_string} {year}"
        datetime_obj = datetime.strptime(date_time_str, date_format)
        datetime_objects.append(datetime_obj)
    
    return datetime_objects


def generate_centered_timepoints(timepoints, interval_seconds=60):
    # Find the middle index
    middle_index = len(timepoints) // 2
    middle_time = timepoints[middle_index]

    # Calculate the total number of intervals to cover
    total_intervals = int((timepoints[-1] - timepoints[0]).total_seconds() / interval_seconds)
    
    # Generate timepoints from the middle outwards at the specified interval
    centered_timepoints = [middle_time + timedelta(seconds=i * interval_seconds) 
                           for i in range(-total_intervals // 2, total_intervals // 2 + 1)]
    
    # Ensure the original timepoints are included in the centered_timepoints
    centered_timepoints = sorted(set(centered_timepoints + timepoints))

    return centered_timepoints

# ####
# HDR photo processing functions
# ####

def load_and_align_images(image_folder):
    images = [cv2.imread(file) for file in glob.glob(f"{image_folder}/*.cr2")]
    alignMTB = cv2.createAlignMTB()
    alignMTB.process(images, images) # In-place alignment
    return images

def create_hdr_image(images, exposure_times):
    # Convert exposure times to the expected format for cv2.createMergeDebevec()
    # Assuming exposure_times is a list of exposure times in seconds (floats)
    times = np.array(exposure_times, dtype=np.float32)
    
    # Create HDR image
    mergeDebevec = cv2.createMergeDebevec()
    hdr = mergeDebevec.process(images, times=times)
    return hdr

def normalize_and_save_hdr_image(hdr_image, file_path, bit_depth=16):
    # Ensure HDR image values range between its min and max
    hdr_min, hdr_max = hdr_image.min(), hdr_image.max()
    hdr_normalized = (hdr_image - hdr_min) / (hdr_max - hdr_min)
    
    if bit_depth == 16:
        # Scale to 16-bit (0-65535 range) and convert to uint16
        image_16bit = np.clip(hdr_normalized * 65535, 0, 65535).astype('uint16')
        cv2.imwrite(file_path, image_16bit)
    elif bit_depth == 8:
        # Scale to 8-bit (0-255 range) and convert to uint8
        image_8bit = np.clip(hdr_normalized * 255, 0, 255).astype('uint8')
        cv2.imwrite(file_path, image_8bit)
    else:
        raise ValueError("Unsupported bit depth. Choose 8 or 16.")

def display_hdr_image_inline(hdr_image):
    # Check if there are any positive values in the hdr_image
    if np.max(hdr_image) <= 0:
        raise ValueError("The HDR image does not contain any positive values.")
    
    # Ensure the HDR image is in the correct format (floating point, 32-bit)
    hdr_image_32f = hdr_image.astype(np.float32)
    
    # Normalize the HDR image to have a max value of 1 if it doesn't already
    hdr_image_32f /= np.max(hdr_image_32f)

    # Apply tone mapping to convert the HDR image to 8-bit per channel
    tonemap = cv2.createTonemapDrago(1.0, 0.7)
    ldr_image = tonemap.process(hdr_image_32f)
    ldr_image = cv2.normalize(ldr_image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    # Convert color space from OpenCV's default BGR to RGB
    ldr_image = cv2.cvtColor(ldr_image, cv2.COLOR_BGR2RGB)
    
    # Display the image inline
    plt.figure(figsize=(12, 6))
    plt.imshow(ldr_image)
    plt.axis('off')  # Hide the axes
    plt.show()
