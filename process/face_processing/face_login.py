import os
import numpy as np

from process.face_processing.face_utils import FaceUtils
from process.database.config import DataBasePaths
from process.services.ia_client import verify_with_ref_image


class FaceLogIn:
    def __init__(self):
        self.face_utilities = FaceUtils()
        self.database = DataBasePaths()

        self.matcher = None
        self.comparison = False
        self.cont_frame = 0
        # integration config
        # Por defecto, usa el microservicio a menos que USE_IA_SERVICE esté en '0', 'false' o 'False'
        env_val = os.getenv('USE_IA_SERVICE')
        if env_val is None:
            self.use_ia_service = True  # default: usar microservicio
        else:
            self.use_ia_service = env_val not in ('0', 'false', 'False')
        self.ia_base_url = os.getenv('IA_SERVICE_URL') or 'http://localhost:8000'

    def process(self, face_image: np.ndarray):
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
                face_points = self.face_utilities.extract_face_points(face_image, face_info)

                # step 7: face crop
                face_crop = self.face_utilities.face_crop(face_save, face_bbox)

                # step 8: read database
                faces_database, names_database, info = self.face_utilities.read_face_database(self.database.faces)

                if len(faces_database) != 0 and not self.comparison and self.matcher is None:
                    self.comparison = True
                    user_name = ''
                    # step 9: compare faces (API if enabled, else local)
                    if self.use_ia_service:
                        # Try API comparison against each DB image until one matches
                        for idx, db_img in enumerate(faces_database):
                            result = verify_with_ref_image(face_crop, db_img, base_url=self.ia_base_url, timeout=3.5)
                            if result.get('match'):
                                self.matcher = True
                                user_name = names_database[idx]
                                break
                        # If API failed entirely (network/error), fallback to local matching
                        if self.matcher is None or self.matcher is False:
                            # optional fallback only if error suggests failure to call
                            self.matcher, user_name = self.face_utilities.face_matching(face_crop, faces_database, names_database)
                    else:
                        self.matcher, user_name = self.face_utilities.face_matching(face_crop, faces_database, names_database)

                    if self.matcher:
                        # step 10: save data & time
                        self.face_utilities.user_check_in(user_name, self.database.users)
                        return face_image, self.matcher, 'Approved user access!'
                    else:
                        return face_image, self.matcher, 'User no approved'
                else:
                    return face_image, self.matcher, 'Empty database'
            else:
                return face_image, self.matcher, 'wait frames'
        else:
            return face_image, self.matcher, 'No center face'

