import cv2 as cv
import mediapipe as mp
import numpy as np
import math
import time
import av
import tempfile
import pandas as pd
from constants import *
from constants import config

mp_face_mesh = mp.solutions.face_mesh

def euclidean_distance(point1, point2):
    return math.hypot(point2[0] - point1[0], point2[1] - point1[1])

def blink_ratio(landmarks, right_indices, left_indices):
    rh_distance = euclidean_distance(landmarks[right_indices[0]], landmarks[right_indices[8]])
    rv_distance = euclidean_distance(landmarks[right_indices[12]], landmarks[right_indices[4]])
    lh_distance = euclidean_distance(landmarks[left_indices[0]], landmarks[left_indices[8]])
    lv_distance = euclidean_distance(landmarks[left_indices[12]], landmarks[left_indices[4]])

    if rv_distance == 0 or lv_distance == 0:
        return float('inf')

    re_ratio = rh_distance / rv_distance
    le_ratio = lh_distance / lv_distance
    return (re_ratio + le_ratio) / 2

def landmarks_detection(img, results):
    img_height, img_width = img.shape[:2]
    return [(int(point.x * img_width), int(point.y * img_height)) for point in results.multi_face_landmarks[0].landmark]

def eye_direction(eye_points, iris_center, ratio):
    eye_left = np.min(eye_points[:, 0])
    eye_right = np.max(eye_points[:, 0])

    hor_range = eye_right - eye_left
    iris_x, _ = iris_center

    if ratio > 5.5:
        return "Blink"
    elif iris_x < eye_left + hor_range * 0.3:
        return "Left"
    elif iris_x > eye_right - hor_range * 0.3:
        return "Right"
    else:
        return "Center"

def process_frame(frame, face_mesh, focus_score, last_look_centered_time, not_looking_start_time, blink_start_time, blink_detected, last_focus_increase_time, last_focus_decrease_time):
    frame = cv.flip(frame, 1)
    rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    eye_direction_text = "Not Detected"
    face_position = "Not Detected"

    current_time = time.time()

    if results.multi_face_landmarks:
        mesh_points = landmarks_detection(frame, results)
        
        # Face position monitoring
        face_3d = []
        face_2d = []
        for idx, lm in enumerate(results.multi_face_landmarks[0].landmark):
            if idx in [1, 33, 61, 199, 263, 291]:
                x, y = int(lm.x * frame.shape[1]), int(lm.y * frame.shape[0])
                face_2d.append([x, y])
                face_3d.append([x, y, lm.z])
        
        face_2d = np.array(face_2d, dtype=np.float64)
        face_3d = np.array(face_3d, dtype=np.float64)

        focal_length = 1 * frame.shape[1]
        cam_matrix = np.array([[focal_length, 0, frame.shape[1] / 2],
                               [0, focal_length, frame.shape[0] / 2],
                               [0, 0, 1]])
        dist_matrix = np.zeros((4, 1), dtype=np.float64)
        success, rot_vec, trans_vec = cv.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)
        rmat, jac = cv.Rodrigues(rot_vec)
        angles, mtxR, mtxQ, Qx, Qy, Qz = cv.RQDecomp3x3(rmat)

        x = angles[0] * 360
        y = angles[1] * 360

        if y < -10:
            face_position = "Looking Left"
        elif y > 10:
            face_position = "Looking Right"
        elif x < -10:
            face_position = "Looking Down"
        elif x > 20:
            face_position = "Looking Up"
        else:
            face_position = "Forward"

            
       # Eye direction and blink detection
        ratio = blink_ratio(mesh_points, RIGHT_EYE, LEFT_EYE)
        left_iris_points = np.array([mesh_points[i] for i in LEFT_IRIS], dtype=np.int32)
        right_iris_points = np.array([mesh_points[i] for i in RIGHT_IRIS], dtype=np.int32)
        (l_cx, l_cy), l_radius = cv.minEnclosingCircle(left_iris_points)
        (r_cx, r_cy), r_radius = cv.minEnclosingCircle(right_iris_points)
        center_left = np.array([l_cx, l_cy], dtype=np.int32)
        center_right = np.array([r_cx, r_cy], dtype=np.int32)
        left_eye_direction = eye_direction(np.array([mesh_points[p] for p in LEFT_EYE]), center_left, ratio)
        right_eye_direction = eye_direction(np.array([mesh_points[p] for p in RIGHT_EYE]), center_right, ratio)

        if left_eye_direction == right_eye_direction:
            eye_direction_text = left_eye_direction
        else:
            eye_direction_text = left_eye_direction if left_eye_direction in ["Left", "Right"] else right_eye_direction

        # Focus scoring algorithm
        if face_position == "Forward" and eye_direction_text == "Center":
            if last_look_centered_time is None:
                last_look_centered_time = current_time
            not_looking_start_time = None
            if current_time - last_look_centered_time >= config.CENTER_THRESHOLD:
                # Increase focus score by 5% every 1 second when increasing
                if last_focus_increase_time is None or current_time - last_focus_increase_time >= 0.1:
                    focus_score = min(100, focus_score + 0.3)
                    last_focus_increase_time = current_time
        else:
            last_look_centered_time = None
            if not not_looking_start_time:
                not_looking_start_time = current_time
            elif current_time - not_looking_start_time >= config.SIDE_THRESHOLD:
                # Decrease focus score by 5% every 1 second when decreasing
                if last_focus_decrease_time is None or current_time - last_focus_decrease_time >= 0.1:
                    focus_score = max(0, focus_score - config.DISCOUNT_SIDE)
                    last_focus_decrease_time = current_time

        if ratio > 5.5:
            if not blink_detected:
                blink_start_time = current_time
                blink_detected = True
            elif current_time - blink_start_time >= config.BLINK_THRESHOLD:
                # Decrease focus score by 20% if eyes are closed for 5 seconds
                if last_focus_decrease_time is None or current_time - last_focus_decrease_time >= 0.1:
                    focus_score = max(0, focus_score - config.DISCOUNT_EYES)
                    blink_start_time = current_time
        else:
            if blink_detected:
                blink_detected = False

        # Display information on frame
        cv.putText(frame, f"Face: {face_position}", (50, 50), FONTS, 1, (255, 0, 0), 2, cv.LINE_AA)
        cv.putText(frame, f"Eyes: {eye_direction_text}", (50, 100), FONTS, 1, (0, 255, 0), 2, cv.LINE_AA)
        cv.putText(frame, f"Focus Score: {int(focus_score)}%", (50, 150), FONTS, 1, (0, 0, 255), 2, cv.LINE_AA)

    else:
        # If no face is detected, decrease focus score by 1% every 1 second
        if last_focus_decrease_time is None or current_time - last_focus_decrease_time >= 0.1:
            focus_score = max(0, focus_score - 0.5)
            last_focus_decrease_time = current_time

    return (frame, focus_score, last_look_centered_time, not_looking_start_time, blink_start_time, blink_detected, eye_direction_text, face_position, last_focus_increase_time, last_focus_decrease_time)

def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
    img = frame.to_ndarray(format="bgr24")
    global focus_score, last_look_centered_time, not_looking_start_time, blink_start_time, blink_detected
    global last_focus_increase_time, last_focus_decrease_time

    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    ) as face_mesh:
        (img, focus_score, last_look_centered_time, not_looking_start_time, 
         blink_start_time, blink_detected, _, _, last_focus_increase_time, last_focus_decrease_time) = process_frame(
            img, face_mesh, focus_score, last_look_centered_time, not_looking_start_time, 
            blink_start_time, blink_detected, last_focus_increase_time, last_focus_decrease_time
        )

    return av.VideoFrame.from_ndarray(img, format="bgr24")

def process_uploaded_video(video_file):
    tfile = tempfile.NamedTemporaryFile(delete=False) 
    tfile.write(video_file.read())
    
    cap = cv.VideoCapture(tfile.name)
    
    global focus_score, last_look_centered_time, not_looking_start_time, blink_start_time, blink_detected
    # Initialize the new variables
    last_focus_increase_time = None
    last_focus_decrease_time = None

    focus_score = 50  # Initialized start focus from 50
    last_look_centered_time = None
    not_looking_start_time = None
    blink_start_time = None
    blink_detected = False
    
    data = []
    start_time = None
    
    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    ) as face_mesh:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            (frame, focus_score, last_look_centered_time, not_looking_start_time, 
             blink_start_time, blink_detected, eye_direction, face_position, last_focus_increase_time, last_focus_decrease_time) = process_frame(
                frame, face_mesh, focus_score, last_look_centered_time, not_looking_start_time, 
                blink_start_time, blink_detected, last_focus_increase_time, last_focus_decrease_time
            )
            
            timestamp = cap.get(cv.CAP_PROP_POS_MSEC) / 1000  # Convert to seconds
            
            if start_time is None:
                start_time = timestamp

            data.append({
                'timestamp': timestamp,
                'focus_score': focus_score,
                'eye_direction': eye_direction,
                'face_position': face_position,
                'is_front_camera': face_position != "Not Detected",
                'delta_time': 1/30  # Assuming 30 FPS for delta_time
            })
    
    cap.release()
    df = pd.DataFrame(data)
    df['timestamp_min'] = (df['timestamp'] - start_time) / 60  # Convert to minutes

    # Calculate delta_time
    df['delta_time'] = df['timestamp'].diff().fillna(0)

    # Calculate Front Camera and Not Front Camera Time
    total_front_time = df[df['is_front_camera']]['delta_time'].sum()
    total_not_front_time = df[~df['is_front_camera']]['delta_time'].sum()
    total_time = total_front_time + total_not_front_time

    df.attrs['front_camera_percentage'] = (total_front_time / total_time) * 100 if total_time > 0 else 0
    df.attrs['not_front_camera_percentage'] = (total_not_front_time / total_time) * 100 if total_time > 0 else 0

    return df