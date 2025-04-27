# core/head_tracker.py
import numpy as np
from filterpy.kalman import KalmanFilter

class HeadTracker:
    def __init__(self, config, cursor):
        self.config = config
        self.cursor = cursor  
        self.kf = None
        self.current_x = self.current_y = 0
        self.dx_accum = self.dy_accum = 0
        self.moving = False
        self._init_kalman_filter()
    
    def _init_kalman_filter(self):
        self.kf = KalmanFilter(dim_x=4, dim_z=2)
        self.kf.x = np.array([[self.current_x], [self.current_y], [0], [0]])
        self.kf.F = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]])
        self.kf.H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]])
        self.kf.P *= 200
        self.kf.R = np.array([[4, 0], [0, 4]])
        self.kf.Q = np.eye(4) * 0.01
    
    def update_position(self, face_landmarks, frame_shape):
        h, w = frame_shape[:2]
        
        nose = face_landmarks.landmark[4]
        left_ear = face_landmarks.landmark[234]
        right_ear = face_landmarks.landmark[454]
        forehead = face_landmarks.landmark[10]
        chin = face_landmarks.landmark[152]

        face_width = right_ear.x - left_ear.x
        face_height = chin.y - forehead.y
        
        if face_width < 0.001 or face_height < 0.001:
            return self.current_x, self.current_y

        dx = (nose.x - (left_ear.x + right_ear.x) / 2) / face_width
        dy = (nose.y - (forehead.y + chin.y) / 2) / face_height

        if abs(dx) > self.config['neutral_threshold_x'] or abs(dy) > self.config['neutral_threshold_y']:
            self.moving = True
            self.dx_accum, self.dy_accum = dx, dy
        else:
            self.moving = False

        self.kf.predict()
        measurement = np.array([
            [self.dx_accum * self.config['sensitivity_x']],
            [self.dy_accum * self.config['sensitivity_y']]
        ])
        self.kf.update(measurement * 1000)

        smoothed_dx = self.kf.x[0][0] / 1000
        smoothed_dy = self.kf.x[1][0] / 1000
        
        speed_x = min(abs(self.dx_accum) * self.config['speed_gain_x'], 100)
        speed_y = min(abs(self.dy_accum) * self.config['speed_gain_y'] * 5, 100)
        
        if self.moving:
            move_x = smoothed_dx * speed_x * 30
            move_y = smoothed_dy * speed_y * 30
            self.current_x = np.clip(
                self.current_x + move_x, 
                0, 
                self.cursor.screen_width  
            )
            self.current_y = np.clip(
                self.current_y + move_y, 
                0, 
                self.cursor.screen_height  
            )
        
        return self.current_x, self.current_y