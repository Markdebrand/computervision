import os
from tkinter import *
import tkinter as Tk
from PIL import Image, ImageTk
import cv2

from process.gui.image_paths import ImagePaths
from process.database.config import DataBasePaths
from process.face_processing.face_signup import FaceSignUp
from process.face_processing.face_login import FaceLogIn
from process.com_interface.serial_com import SerialCommunication
from process.face_processing.background.person_segmentation import PersonSegmenter


class CustomFrame(Tk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(fill=Tk.BOTH, expand=True)


class GraphicalUserInterface:
    def __init__(self, root):
        self.main_window = root
        self.main_window.title('faces access control')
        self.main_window.geometry('1280x720')
        self.frame = CustomFrame(self.main_window)

        # responsive background placeholders (main window)
        self.bg_label = None
        self.bg_image_orig = None
        self._bg_photo = None

        # camera config
        cam_index = int(os.getenv("CAMERA_INDEX", "0"))
        self.cap = cv2.VideoCapture(cam_index)
        self.cap.set(3, 1280)
        self.cap.set(4, 720)

        # signup window state
        self.signup_window = None
        self.input_name = None
        self.input_user_code = None
        self.name = None
        self.user_code = None
        self.user_list = None
        self.face_signup_window = None
        self.signup_video = None
        self.user_codes = []
        self.data = []

        # login window state
        self.face_login_window = None
        self.login_video = None

        # modules
        self.images = ImagePaths()
        self.database = DataBasePaths()
        self.face_sign_up = FaceSignUp()
        self.face_login = FaceLogIn()
        self.com = SerialCommunication()
        self.segmenter = PersonSegmenter()

        # ensure db dirs
        try:
            os.makedirs(self.database.faces, exist_ok=True)
            os.makedirs(self.database.users, exist_ok=True)
        except Exception:
            pass

        # init main UI
        self.main()
        self.main_window.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        # release camera
        try:
            if hasattr(self, 'cap') and self.cap and self.cap.isOpened():
                self.cap.release()
        except Exception:
            pass
        # close serial
        try:
            if hasattr(self, 'com') and self.com:
                self.com.close()
        except Exception:
            pass
        # destroy windows
        try:
            if self.face_login_window:
                self.face_login_window.destroy()
        except Exception:
            pass
        try:
            if self.face_signup_window:
                self.face_signup_window.destroy()
        except Exception:
            pass
        try:
            if self.signup_window:
                self.signup_window.destroy()
        except Exception:
            pass
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        try:
            self.main_window.destroy()
        except Exception:
            pass

    def gui_login(self):
        # reset state
        self.face_login.__init__()
        # create window
        self.face_login_window = Toplevel(self.frame)
        self.face_login_window.title('facial access')
        self.face_login_window.geometry('1280x720')
        self.login_video = Label(self.face_login_window)
        self.login_video.place(x=0, y=0)
        self.facial_login()

    def facial_login(self):
        if not self.cap:
            return
        ret, frame_bgr = self.cap.read()
        if not ret:
            # try again shortly
            if self.login_video:
                self.login_video.after(50, self.facial_login)
            return

        # process in BGR
        frame_processed, matcher, info = self.face_login.process(frame_bgr)

        # apply person segmentation
        seg_frame = self.segmenter.apply(frame_processed)

        # display (convert to RGB only for Tk)
        frame_show = self._resize_to_width(seg_frame, 1280)
        frame_show = cv2.cvtColor(frame_show, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(frame_show)
        img = ImageTk.PhotoImage(image=im)

        self.login_video.configure(image=img)
        self.login_video.image = img
        self.login_video.after(10, self.facial_login)

        if matcher:
            # access granted -> open, then auto-close after a moment
            try:
                self.com.sending_data('A')
            except Exception:
                pass
            self.login_video.after(3000, self.close_login)

    def close_login(self):
        try:
            self.com.sending_data('C')
        except Exception:
            pass
        try:
            if self.face_login_window:
                self.face_login_window.destroy()
        except Exception:
            pass
        self.face_login_window = None
        self.login_video = None

    def close_signup(self):
        try:
            if self.face_signup_window:
                self.face_signup_window.destroy()
        except Exception:
            pass
        self.face_signup_window = None
        self.signup_video = None

    def facial_sign_up(self):
        if not self.cap:
            return
        ret, frame_bgr = self.cap.read()
        if ret:
            # process en BGR
            frame_processed, save_image, info = self.face_sign_up.process(frame_bgr, self.user_code)

            # aplicar segmentación de persona sobre el fondo
            seg_frame = self.segmenter.apply(frame_processed)
            # config video (convertir a RGB solo para mostrar)
            frame_show = self._resize_to_width(seg_frame, 1280)
            frame_show = cv2.cvtColor(frame_show, cv2.COLOR_BGR2RGB)
            im = Image.fromarray(frame_show)
            img = ImageTk.PhotoImage(image=im)

            # show frames
            self.signup_video.configure(image=img)
            self.signup_video.image = img
            self.signup_video.after(10, self.facial_sign_up)

            if save_image:
                self.signup_video.after(3000, self.close_signup)
        else:
            # try again shortly
            if self.signup_video:
                self.signup_video.after(50, self.facial_sign_up)

    def data_sign_up(self):
        # extract data
        self.name, self.user_code = self.input_name.get(), self.input_user_code.get()
        # check data
        if len(self.name) == 0 or len(self.user_code) == 0:
            print('¡Formulary incomplete!')
            return
        # check user
        self.user_list = os.listdir(self.database.check_users)
        for u_list in self.user_list:
            user = u_list
            user = user.split('.')
            self.user_codes.append(user[0])
        if self.user_code in self.user_codes:
            print('¡Previously registered user!')
            return

        # save data
        self.data.append(self.name)
        self.data.append(self.user_code)

        try:
            os.makedirs(self.database.users, exist_ok=True)
            with open(f"{self.database.users}/{self.user_code}.txt", 'w') as file:
                file.writelines(self.name + ',')
                file.writelines(self.user_code + ',')
        except Exception as e:
            print(f'Error saving user data: {e}')

        # clear
        self.input_name.delete(0, END)
        self.input_user_code.delete(0, END)

        # face register
        self.face_signup_window = Toplevel()
        self.face_signup_window.title('face capture')
        self.face_signup_window.geometry('1280x720')

        self.signup_video = Label(self.face_signup_window)
        self.signup_video.place(x=0, y=0)
        self.signup_window.destroy()
        self.facial_sign_up()

    def gui_signup(self):
        self.signup_window = Toplevel(self.frame)
        self.signup_window.title('facial sign up')
        self.signup_window.geometry("1280x720")

        # responsive background for signup window
        self.signup_bg_label = None
        self.signup_bg_image_orig = None
        self._signup_bg_photo = None
        try:
            if os.path.exists(self.images.gui_signup_img):
                self.signup_bg_image_orig = Image.open(self.images.gui_signup_img)
                self.signup_bg_label = Label(self.signup_window)
                self.signup_bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                self._resize_signup_bg()
                self.signup_window.bind('<Configure>', lambda e: self._resize_signup_bg())
            else:
                self.signup_window.configure(bg="#101318")
        except Exception:
            self.signup_window.configure(bg="#101318")

        # input data
        self.input_name = Entry(self.signup_window)
        # Aproximadamente donde estaban (585,320) en 1280x720 -> (~0.46, ~0.44)
        self.input_name.place(relx=0.46, rely=0.44, anchor='center')
        self.input_user_code = Entry(self.signup_window)
        # Aproximadamente (585,475) -> (~0.46, ~0.66)
        self.input_user_code.place(relx=0.46, rely=0.66, anchor='center')

        # input button
        try:
            register_button_img = PhotoImage(file=self.images.register_img)
            register_button = Button(self.signup_window, image=register_button_img, height="40", width="200",
                                     command=self.data_sign_up)
            register_button.image = register_button_img
        except Exception:
            register_button = Button(self.signup_window, text="Registrar", height=2, width=24,
                                     command=self.data_sign_up)
        # Aproximadamente (1005,565) -> (~0.785, ~0.785)
        register_button.place(relx=0.785, rely=0.785, anchor='center')

    def main(self):
        # responsive background for main window
        try:
            if os.path.exists(self.images.init_img):
                self.bg_image_orig = Image.open(self.images.init_img)
                self.bg_label = Label(self.frame)
                self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                self._resize_main_bg()
                self.frame.bind('<Configure>', lambda e: self._resize_main_bg())
            else:
                self.frame.configure(bg="#0b0f14")
        except Exception:
            self.frame.configure(bg="#0b0f14")

        # buttons
        self.login_button = Button(self.frame, text="Facial Access - Entry", height=2, width=24,
                                   font=("Segoe UI", 12, "bold"), bg="#ff9800", fg="#ffffff",
                                   activebackground="#ffa726", command=self.gui_login)
        # Aproximadamente (980,325) -> (~0.765, ~0.45)
        self.login_button.place(relx=0.765, rely=0.45, anchor='center')

        self.signup_button = Button(self.frame, text="Facial Sign Up - Register", height=2, width=24,
                                    font=("Segoe UI", 12, "bold"), bg="#00bcd4", fg="#ffffff",
                                    activebackground="#26c6da", command=self.gui_signup)
        # Aproximadamente (980,578) -> (~0.765, ~0.80)
        self.signup_button.place(relx=0.765, rely=0.80, anchor='center')

    # ================= Helper methods: responsive backgrounds ================= #
    def _resize_main_bg(self):
        if self.bg_image_orig is None or self.bg_label is None:
            return
        w = max(1, self.frame.winfo_width())
        h = max(1, self.frame.winfo_height())
        try:
            img_resized = self.bg_image_orig.resize((w, h), Image.LANCZOS)
        except Exception:
            img_resized = self.bg_image_orig
        self._bg_photo = ImageTk.PhotoImage(img_resized)
        self.bg_label.configure(image=self._bg_photo)
        self.bg_label.image = self._bg_photo

    def _resize_signup_bg(self):
        if self.signup_bg_image_orig is None or self.signup_bg_label is None:
            return
        w = max(1, self.signup_window.winfo_width())
        h = max(1, self.signup_window.winfo_height())
        try:
            img_resized = self.signup_bg_image_orig.resize((w, h), Image.LANCZOS)
        except Exception:
            img_resized = self.signup_bg_image_orig
        self._signup_bg_photo = ImageTk.PhotoImage(img_resized)
        self.signup_bg_label.configure(image=self._signup_bg_photo)
        self.signup_bg_label.image = self._signup_bg_photo

    def _resize_to_width(self, image_bgr, width):
        try:
            h, w = image_bgr.shape[:2]
            if w == 0:
                return image_bgr
            scale = float(width) / float(w)
            new_h = max(1, int(h * scale))
            return cv2.resize(image_bgr, (width, new_h), interpolation=cv2.INTER_AREA)
        except Exception:
            return image_bgr



