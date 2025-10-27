import os
import threading
from typing import Optional, Tuple
import numpy as np

from process.face_processing.face_utils import FaceUtils
from process.database.config import DataBasePaths
from process.services.ia_client import verify_with_ref_image, health_check


class FaceLogIn:
    def __init__(self):
        self.face_utilities = FaceUtils()
        self.database = DataBasePaths()

        self.matcher = None
        self.comparison = False
        self.cont_frame = 0
        # resultado y control de hilo
        self._inference_running: bool = False
        self._result_ready: bool = False
        self.last_user_name: str = ''
        # integration config
        # Microservicio obligatorio por defecto; puede desactivarse solo si explícito
        self.use_ia_service = os.getenv('USE_IA_SERVICE') not in ('0', 'false', 'False')
        # Si se requiere estrictamente, NUNCA hacer fallback local
        self.require_ia_service = os.getenv('REQUIRE_IA_SERVICE', '1') not in ('0', 'false', 'False')
        self.ia_base_url = os.getenv('IA_SERVICE_URL') or 'http://localhost:8000'
        self._service_healthy_checked = False
        self._service_healthy = False

    def _run_matching(self, face_crop: np.ndarray, faces_database, names_database) -> None:
        try:
            user_name = ''
            # Comparación solo con microservicio (obligatorio)
            if self.use_ia_service or self.require_ia_service:
                # Verificar salud una vez
                if not self._service_healthy_checked:
                    self._service_healthy = health_check(self.ia_base_url, timeout=1.5)
                    self._service_healthy_checked = True
                if not self._service_healthy:
                    self.matcher = False
                else:
                    for idx, db_img in enumerate(faces_database):
                        result = verify_with_ref_image(face_crop, db_img, base_url=self.ia_base_url, timeout=3.5)
                        if result.get('match'):
                            self.matcher = True
                            user_name = names_database[idx]
                            break
                    if not self.matcher:
                        self.matcher = False
                        user_name = ''
            else:
                # Si no es obligatorio y USE_IA_SERVICE=0, opción local (caso de desarrollo)
                self.matcher, user_name = self.face_utilities.face_matching(face_crop, faces_database, names_database)

            if self.matcher:
                # guardar check-in y nombre
                self.face_utilities.user_check_in(user_name, self.database.users)
                self.last_user_name = user_name
            else:
                self.last_user_name = ''
        finally:
            self._inference_running = False
            self._result_ready = True

    def process(self, face_image: np.ndarray) -> Tuple[np.ndarray, Optional[bool], str]:
        # step 1: check face detection
        check_face_detect, face_info, face_save = self.face_utilities.check_face(face_image)
        if check_face_detect is False:
            return face_image, self.matcher, '¡No face detected!'

        # step 2: face mesh
        check_face_mesh, face_mesh_info = self.face_utilities.face_mesh(face_image)
        if check_face_mesh is False:
            return face_image, self.matcher, '¡No face mesh detected!'

        # step 3: extract face mesh
        face_mesh_points_list = self.face_utilities.extract_face_mesh(face_image, face_mesh_info)

        # step 4: check face center
        check_face_center = self.face_utilities.check_face_center(face_mesh_points_list)

        # step 5: show state
        self.face_utilities.show_state_login(face_image, state=self.matcher)

        if check_face_center:
            # step 6: extract face info
            # bbox & key_points
            self.cont_frame = self.cont_frame + 1
            if self.cont_frame >= 48:
                face_bbox = self.face_utilities.extract_face_bbox(face_image, face_info)
                # puntos faciales no usados directamente en la comparación; se omiten para evitar costos

                # step 7: face crop
                face_crop = self.face_utilities.face_crop(face_save, face_bbox)

                # step 8: read database
                faces_database, names_database, info = self.face_utilities.read_face_database(self.database.faces)

                if len(faces_database) != 0:
                    # Lanzar comparación en background si no hay una en curso y no hay resultado previo
                    if not self._inference_running and not self._result_ready and self.matcher is None:
                        self.comparison = True
                        self._inference_running = True
                        th = threading.Thread(target=self._run_matching, args=(face_crop, faces_database, names_database), daemon=True)
                        th.start()
                        # Mostrar estado de comparación
                        return face_image, None, 'wait frames'
                    # Si ya hay un resultado disponible
                    if self._result_ready:
                        msg = 'Approved user access!' if self.matcher else 'User no approved'
                        # limpiar flags para una siguiente sesión
                        self._result_ready = False
                        self.comparison = False
                        return face_image, self.matcher, msg
                    # Sin resultado aún, seguir esperando
                    return face_image, None, 'wait frames'
                else:
                    return face_image, self.matcher, 'Empty database'
            else:
                return face_image, self.matcher, 'wait frames'
        else:
            return face_image, self.matcher, 'No center face'

