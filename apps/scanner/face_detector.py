"""
Face detection and zone extraction using OpenCV
"""
import cv2
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)


def detect_face(image_path):
    """
    Detect if a face is present in the uploaded image using OpenCV Haar Cascade
    
    Args:
        image_path: Path to the image file (string or Path object)
    
    Returns:
        dict with keys: detected (bool), confidence (int), face_rect (tuple), message (str)
    """
    try:
        # Step 1: Load image
        image_path_str = str(image_path)
        img = cv2.imread(image_path_str)
        
        if img is None:
            raise ValueError("Cannot read image file")
        
        # Step 2: Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Step 3: Load Haar Cascade classifier
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Step 4: Detect faces — use multiple scale factors for better detection
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=4,
            minSize=(60, 60)
        )
        
        # If nothing found, retry with more lenient settings
        if len(faces) == 0:
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=3,
                minSize=(40, 40)
            )
        
        # Step 5: Check if face detected
        if len(faces) == 0:
            return {
                'detected': False,
                'confidence': 0,
                'face_rect': None,
                'message': 'No face detected in this image. Please ensure your face is clearly visible, well-lit, and looking directly at the camera.'
            }
        
        # Step 6: Get largest face by area
        largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
        x, y, w, h = largest_face
        
        # DEBUG: Log face box
        logger.info(f"Face Box: x={x}, y={y}, w={w}, h={h}")
        
        # Step 7: Calculate confidence
        face_area = w * h
        image_area = img.shape[0] * img.shape[1]
        raw_conf = (face_area / image_area) * 200
        confidence = min(100, int(raw_conf))
        
        # DEBUG: Log confidence
        logger.info(f"Face Confidence: {confidence}")
        
        # Step 8: Check if face is centered
        face_center_x = x + w // 2
        face_center_y = y + h // 2
        img_w = img.shape[1]
        img_h = img.shape[0]
        
        if (face_center_x < img_w * 0.12 or face_center_x > img_w * 0.88 or 
            face_center_y < img_h * 0.08 or face_center_y > img_h * 0.92):
            return {
                'detected': False,
                'confidence': confidence,
                'face_rect': (x, y, w, h),
                'message': 'Face detected but too close to the edge. Please position your face in the centre of the frame.'
            }
        
        # Step 9: Check if face is too small (FIXED: changed 15 to 8)
        if confidence < 8:
            return {
                'detected': False,
                'confidence': confidence,
                'face_rect': (x, y, w, h),
                'message': 'Face too small or far away. Please move closer to the camera so your face fills most of the frame.'
            }
        
        # Step 10: Success
        logger.info(f"Face detected successfully with confidence {confidence}%")
        return {
            'detected': True,
            'confidence': confidence,
            'face_rect': (x, y, w, h),
            'message': 'Face detected successfully'
        }
        
    except Exception as e:
        logger.error(f"Error in face detection: {str(e)}")
        return {
            'detected': False,
            'confidence': 0,
            'face_rect': None,
            'message': f'Error processing image: {str(e)}'
        }


def extract_face_roi(image_path, face_rect):
    """
    Extract the face region of interest from the image with 10% padding
    """
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError("Cannot read image file")
        
        x, y, w, h = face_rect
        
        padding_x = int(w * 0.1)
        padding_y = int(h * 0.1)
        
        x1 = max(0, x - padding_x)
        y1 = max(0, y - padding_y)
        x2 = min(img.shape[1], x + w + padding_x)
        y2 = min(img.shape[0], y + h + padding_y)
        
        face_roi = img[y1:y2, x1:x2]
        
        return face_roi
        
    except Exception as e:
        logger.error(f"Error extracting face ROI: {str(e)}")
        raise


def divide_face_into_zones(image, face_rect):
    """
    Divide the face into 5 zones for detailed analysis
    """
    try:
        x, y, w, h = face_rect
        zones = {}
        
        forehead_y1 = y
        forehead_y2 = y + int(h * 0.25)
        forehead_x1 = x
        forehead_x2 = x + w
        
        forehead = image[forehead_y1:forehead_y2, forehead_x1:forehead_x2]
        if forehead.shape[0] >= 20 and forehead.shape[1] >= 20:
            zones['forehead'] = forehead
        else:
            zones['forehead'] = None
        
        nose_y1 = y + int(h * 0.25)
        nose_y2 = y + int(h * 0.55)
        nose_x1 = x + int(w * 0.35)
        nose_x2 = x + int(w * 0.65)
        
        nose = image[nose_y1:nose_y2, nose_x1:nose_x2]
        if nose.shape[0] >= 20 and nose.shape[1] >= 20:
            zones['nose'] = nose
        else:
            zones['nose'] = None
        
        left_cheek_y1 = y + int(h * 0.40)
        left_cheek_y2 = y + int(h * 0.70)
        left_cheek_x1 = x
        left_cheek_x2 = x + int(w * 0.35)
        
        left_cheek = image[left_cheek_y1:left_cheek_y2, left_cheek_x1:left_cheek_x2]
        if left_cheek.shape[0] >= 20 and left_cheek.shape[1] >= 20:
            zones['left_cheek'] = left_cheek
        else:
            zones['left_cheek'] = None
        
        right_cheek_y1 = y + int(h * 0.40)
        right_cheek_y2 = y + int(h * 0.70)
        right_cheek_x1 = x + int(w * 0.65)
        right_cheek_x2 = x + w
        
        right_cheek = image[right_cheek_y1:right_cheek_y2, right_cheek_x1:right_cheek_x2]
        if right_cheek.shape[0] >= 20 and right_cheek.shape[1] >= 20:
            zones['right_cheek'] = right_cheek
        else:
            zones['right_cheek'] = None
        
        chin_y1 = y + int(h * 0.75)
        chin_y2 = y + h
        chin_x1 = x + int(w * 0.20)
        chin_x2 = x + int(w * 0.80)
        
        chin = image[chin_y1:chin_y2, chin_x1:chin_x2]
        if chin.shape[0] >= 20 and chin.shape[1] >= 20:
            zones['chin'] = chin
        else:
            zones['chin'] = None
        
        logger.info(f"Face divided into zones: {[k for k, v in zones.items() if v is not None]}")
        return zones
        
    except Exception as e:
        logger.error(f"Error dividing face into zones: {str(e)}")
        return {
            'forehead': None,
            'nose': None,
            'left_cheek': None,
            'right_cheek': None,
            'chin': None
        }