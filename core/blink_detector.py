# core/blink_detector.py
import time
from scipy.spatial import distance as dist

class BlinkDetector:
    def __init__(self, config):
        self.config = config
        self.blink_counter = 0
        self.blink_confirmed = False
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]
        
        # Blink sequence tracking
        self.last_blink_time = None
        self.blink_sequence = 0
        self.pending_blink_action = None

    def calculate_ear(self, eye_points):
        vertical_1 = dist.euclidean(eye_points[1], eye_points[5])
        vertical_2 = dist.euclidean(eye_points[2], eye_points[4])
        horizontal = dist.euclidean(eye_points[0], eye_points[3])
        return (vertical_1 + vertical_2) / (2.0 * horizontal)

    def detect(self, face_landmarks, frame_shape, is_moving):
        h, w = frame_shape[:2]
        
        left_eye = [(int(face_landmarks.landmark[i].x * w), 
                    int(face_landmarks.landmark[i].y * h)) for i in self.LEFT_EYE]
        right_eye = [(int(face_landmarks.landmark[i].x * w), 
                     int(face_landmarks.landmark[i].y * h)) for i in self.RIGHT_EYE]
        
        left_ear = self.calculate_ear(left_eye)
        right_ear = self.calculate_ear(right_eye)
        avg_ear = (left_ear + right_ear) / 2.0

        # Reset blink counter if eyes are open
        if avg_ear > self.config['blink_threshold']:
            self.blink_counter = 0
            self.blink_confirmed = False

        # Detect eye closure
        if not is_moving and avg_ear < self.config['blink_threshold']:
            self.blink_counter += 1

            # Immediate single blink detection
            if self.blink_counter == self.config['blink_frames']:
                self._update_blink_sequence()
                return "single"

        
        action = self._check_pending_actions()
        return action

    def _update_blink_sequence(self):
        current_time = time.time()
        
        if self.last_blink_time and (current_time - self.last_blink_time > self.config['blink_sequence_threshold']):
            self.blink_sequence = 0
        
        self.blink_sequence += 1
        self.last_blink_time = current_time
        self.pending_blink_action = current_time + self.config['blink_sequence_threshold']

    def _check_pending_actions(self):
        if self.pending_blink_action and time.time() >= self.pending_blink_action:
            if self.blink_sequence == 2:
                action = "double"
            elif self.blink_sequence >= 3:
                action = "triple"
            else:
                action = None
            
            self.blink_sequence = 0
            self.pending_blink_action = None
            return action
        return None