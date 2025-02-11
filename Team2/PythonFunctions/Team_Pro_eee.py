import cv2
import numpy as np

def floorplan_to_maze(image_path, output_path):

    # Load the image
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    if image is None:
        raise FileNotFoundError(f"Image at {image_path} not found.")

    # Apply GaussianBlur to smooth out details and remove furniture or small objects
    blurred_image = cv2.GaussianBlur(image, (5, 5), 0)

    # Threshold the image to create a binary map (black and white)
    _, binary_image = cv2.threshold(blurred_image, 175, 255, cv2.THRESH_BINARY_INV)

    # Use morphological operations to remove noise and small gaps (e.g., doors)
    kernel = np.ones((3, 3), np.uint8)
    cleaned_image = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)

    # Normalize the values to 0 and 1 for better representation of walls and paths
    maze = (cleaned_image > 128).astype(np.uint8)
    print(np.array2string(maze, threshold=np.inf))

    return maze


# Example usage 
maze = floorplan_to_maze("floorplan.jpeg", "maze_output.jpg")

 