from typing import Tuple
import cv2
import numpy as np
from deepface import DeepFace

try:
    import face_recognition as fr  # opcional; evita CMake/dlib si no está
    HAS_FACE_RECOG = True
except Exception:
    fr = None
    HAS_FACE_RECOG = False


class FaceMatcherModels:
    def __init__(self):
        # Modelos soportados por DeepFace sin requerir dlib si usamos detector_backend='skip'
        self.models = [
            "VGG-Face",
            "Facenet",
            "Facenet512",
            "OpenFace",
            "DeepFace",
            "DeepID",
            "ArcFace",
            # "Dlib",  # evitar explícitamente dependencia
            "SFace",
            "GhostFaceNet",
        ]

    def face_matching_face_recognition_model(self, face_1: np.ndarray, face_2: np.ndarray) -> Tuple[bool, float]:
        if not HAS_FACE_RECOG:
            # face_recognition no disponible: evitar dependencia externa (dlib/CMake)
            return False, 1.0
        face_1_rgb = cv2.cvtColor(face_1, cv2.COLOR_BGR2RGB)
        face_2_rgb = cv2.cvtColor(face_2, cv2.COLOR_BGR2RGB)
        # usar toda la imagen como rostro (ya viene recortada)
        face_loc_1 = [(0, face_1_rgb.shape[1], face_1_rgb.shape[0], 0)]
        face_loc_2 = [(0, face_2_rgb.shape[1], face_2_rgb.shape[0], 0)]
        enc1_list = fr.face_encodings(face_1_rgb, known_face_locations=face_loc_1)
        enc2_list = fr.face_encodings(face_2_rgb, known_face_locations=face_loc_2)
        if len(enc1_list) == 0 or len(enc2_list) == 0:
            return False, 1.0
        enc1 = enc1_list[0]
        enc2 = enc2_list[0]
        distances = fr.face_distance([enc1], enc2)
        distance = float(distances[0]) if hasattr(distances, '__len__') else float(distances)
        matching = distance <= 0.55
        return matching, distance

    def face_matching_vgg_model(self, face_1: np.ndarray, face_2: np.ndarray) -> Tuple[bool, float]:
        try:
            result = DeepFace.verify(img1_path=face_1, img2_path=face_2, model_name=self.models[0],
                                     detector_backend='skip', enforce_detection=False)
            matching, distance = result['verified'], result['distance']
            return matching, distance
        except:
            return False, 0.0

    def face_matching_facenet_model(self, face_1: np.ndarray, face_2: np.ndarray) -> Tuple[bool, float]:
        try:
            result = DeepFace.verify(img1_path=face_1, img2_path=face_2, model_name=self.models[1],
                                     detector_backend='skip', enforce_detection=False)
            matching, distance = result['verified'], result['distance']
            return matching, distance
        except:
            return False, 0.0

    def face_matching_facenet512_model(self, face_1: np.ndarray, face_2: np.ndarray) -> Tuple[bool, float]:
        try:
            result = DeepFace.verify(img1_path=face_1, img2_path=face_2, model_name=self.models[2],
                                     detector_backend='skip', enforce_detection=False)
            matching, distance = result['verified'], result['distance']
            return matching, distance
        except:
            return False, 0.0

    def face_matching_openface_model(self, face_1: np.ndarray, face_2: np.ndarray) -> Tuple[bool, float]:
        try:
            result = DeepFace.verify(img1_path=face_1, img2_path=face_2, model_name=self.models[3],
                                     detector_backend='skip', enforce_detection=False)
            matching, distance = result['verified'], result['distance']
            return matching, distance
        except:
            return False, 0.0

    def face_matching_deepface_model(self, face_1: np.ndarray, face_2: np.ndarray) -> Tuple[bool, float]:
        try:
            result = DeepFace.verify(img1_path=face_1, img2_path=face_2, model_name=self.models[4],
                                     detector_backend='skip', enforce_detection=False)
            matching, distance = result['verified'], result['distance']
            return matching, distance
        except:
            return False, 0.0

    def face_matching_deepid_model(self, face_1: np.ndarray, face_2: np.ndarray) -> Tuple[bool, float]:
        try:
            result = DeepFace.verify(img1_path=face_1, img2_path=face_2, model_name=self.models[5],
                                     detector_backend='skip', enforce_detection=False)
            matching, distance = result['verified'], result['distance']
            return matching, distance
        except:
            return False, 0.0

    def face_matching_arcface_model(self, face_1: np.ndarray, face_2: np.ndarray) -> Tuple[bool, float]:
        try:
            result = DeepFace.verify(img1_path=face_1, img2_path=face_2, model_name=self.models[6],
                                     detector_backend='skip', enforce_detection=False)
            matching, distance = result['verified'], result['distance']
            return matching, distance
        except:
            return False, 0.0

    def face_matching_dlib_model(self, face_1: np.ndarray, face_2: np.ndarray) -> Tuple[bool, float]:
        # Dlib se omite para evitar dependencias externas
        return False, 0.0

    def face_matching_sface_model(self, face_1: np.ndarray, face_2: np.ndarray) -> Tuple[bool, float]:
        try:
            result = DeepFace.verify(img1_path=face_1, img2_path=face_2, model_name=self.models[7],
                                     detector_backend='skip', enforce_detection=False)
            matching, distance = result['verified'], result['distance']
            return matching, distance
        except:
            return False, 0.0

    def face_matching_ghostfacenet_model(self, face_1: np.ndarray, face_2: np.ndarray) -> Tuple[bool, float]:
        try:
            result = DeepFace.verify(img1_path=face_1, img2_path=face_2, model_name=self.models[8],
                                     detector_backend='skip', enforce_detection=False)
            matching, distance = result['verified'], result['distance']
            return matching, distance
        except:
            return False, 0.0
