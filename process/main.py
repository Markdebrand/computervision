import pandas as pd
from datetime import datetime
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
    def save_attendance_to_excel(self, nombre, apellido, hora_entrada, hora_salida, fecha, excel_path="attendance.xlsx"):
        try:
            df = pd.read_excel(excel_path)
        except FileNotFoundError:
            df = pd.DataFrame(columns=["Nombre", "Apellido", "Hora de entrada", "Hora de salida", "Fecha"])

        if hora_entrada and not hora_salida:
            # Registrar entrada: agrega nueva fila
            new_row = {
                "Nombre": nombre,
                "Apellido": apellido,
                "Hora de entrada": hora_entrada,
                "Hora de salida": "",
                "Fecha": fecha
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        elif hora_salida and not hora_entrada:
            # Registrar salida: busca última fila sin salida y la actualiza
            mask = (
                (df["Nombre"] == nombre) &
                (df["Apellido"] == apellido) &
                (df["Fecha"] == fecha) &
                (df["Hora de salida"] == "")
            )
            idx = df[mask].last_valid_index()
            if idx is not None:
                df.at[idx, "Hora de salida"] = hora_salida
            else:
                # Si no hay entrada previa, agrega fila solo con salida
                new_row = {
                    "Nombre": nombre,
                    "Apellido": apellido,
                    "Hora de entrada": "",
                    "Hora de salida": hora_salida,
                    "Fecha": fecha
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_excel(excel_path, index=False)
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
        # ...existing code...
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

        # Save to Excel (login = salida)
        nombre = ""
        apellido = ""
        if hasattr(self, 'name') and self.name:
            nombre = self.name.strip()
            if " " in nombre:
                nombre, apellido = nombre.split(" ", 1)
        hora_entrada = ""
        hora_salida = datetime.now().strftime("%H:%M:%S")
        fecha = datetime.now().strftime("%d/%m/%Y")
        self.save_attendance_to_excel(nombre, apellido, hora_entrada, hora_salida, fecha)

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
        # treat placeholders as empty
        if self.name in ("Enter your name", None):
            self.name = ""
        if self.user_code in ("Enter your user code", None):
            self.user_code = ""
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

        # ===== Card background for form ===== #
        card_w, card_h = 500, 320
        card_x, card_y = (1280 - card_w) // 2, (720 - card_h) // 2
        self.signup_card = Canvas(self.signup_window, width=card_w, height=card_h, bg='#e0e0e0', highlightthickness=0)
        self.signup_card.place(x=card_x, y=card_y)
        # Draw rounded rectangle (simulate with polygons/arcs)
        def draw_rounded_rect(canvas, x, y, w, h, r, color, alpha=0.85):
            # Tkinter doesn't support alpha, so use a solid color
            # For true alpha, use PIL to generate an image and place it, but here we use a light gray
            canvas.create_rectangle(x+r, y, x+w-r, y+h, fill=color, outline=color)
            canvas.create_rectangle(x, y+r, x+w, y+h-r, fill=color, outline=color)
            # Guardar hora de entrada en Excel justo después del registro
            nombre = ""
            apellido = ""
            if self.name:
                nombre = self.name.strip()
                if " " in nombre:
                    nombre, apellido = nombre.split(" ", 1)
            hora_entrada = datetime.now().strftime("%H:%M:%S")
            hora_salida = ""
            fecha = datetime.now().strftime("%d/%m/%Y")
            self.save_attendance_to_excel(nombre, apellido, hora_entrada, hora_salida, fecha)
            canvas.create_oval(x, y, x+2*r, y+2*r, fill=color, outline=color)
            canvas.create_oval(x+w-2*r, y, x+w, y+2*r, fill=color, outline=color)
            canvas.create_oval(x, y+h-2*r, x+2*r, y+h, fill=color, outline=color)
            canvas.create_oval(x+w-2*r, y+h-2*r, x+w, y+h, fill=color, outline=color)

        draw_rounded_rect(self.signup_card, 0, 0, card_w, card_h, 32, '#e0e0e0')

        # ===== Place widgets inside card ===== #
        # Helper: placeholder behavior
        def _add_placeholder(entry: Entry, text: str):
            entry.insert(0, text)
            entry.config(fg="#7a7a7a")
            def on_focus_in(_):
                if entry.get() == text:
                    entry.delete(0, END)
                    entry.config(fg="#111111")
            def on_focus_out(_):
                if entry.get() == "":
                    entry.insert(0, text)
                    entry.config(fg="#7a7a7a")
            entry.bind("<FocusIn>", on_focus_in)
            entry.bind("<FocusOut>", on_focus_out)

        # Title LOGIN
        self.signup_title_lbl = Label(
            self.signup_window,
            text="LOGIN",
            font=("Segoe UI", 28, "bold"),
            fg="#222",
            bg="#e0e0e0"
        )
        self.signup_title_lbl.place(x=card_x+card_w//2, y=card_y+38, anchor='center')

        # NAME label
        self.name_label = Label(
            self.signup_window,
            text="NAME:",
            font=("Segoe UI", 14, "bold"),
            fg="#222",
            bg="#e0e0e0"
        )
        self.name_label.place(x=card_x+60, y=card_y+90, anchor='w')

        # Name input
        self.input_name = Entry(
            self.signup_window,
            width=28,
            font=("Segoe UI", 12),
            relief="flat",
            bd=2,
            bg="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#c7c7c7",
            highlightcolor="#4a90e2",
            justify='left'
        )
        self.input_name.place(x=card_x+160, y=card_y+90, anchor='w', width=260, height=32)
        _add_placeholder(self.input_name, "Enter your name")

        # USER CODE label
        self.user_code_label = Label(
            self.signup_window,
            text="USER CODE:",
            font=("Segoe UI", 14, "bold"),
            fg="#222",
            bg="#e0e0e0"
        )
        self.user_code_label.place(x=card_x+60, y=card_y+150, anchor='w')

        # User code input
        self.input_user_code = Entry(
            self.signup_window,
            width=28,
            font=("Segoe UI", 12),
            relief="flat",
            bd=2,
            bg="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#c7c7c7",
            highlightcolor="#4a90e2",
            justify='left'
        )
        self.input_user_code.place(x=card_x+160, y=card_y+150, anchor='w', width=260, height=32)
        _add_placeholder(self.input_user_code, "Enter your user code")

        # Register button
        try:
            register_button_img = PhotoImage(file=self.images.register_img)
            register_button = Button(self.signup_window, image=register_button_img, height="40", width="200",
                                     command=self.data_sign_up)
            register_button.image = register_button_img
        except Exception:
            register_button = Button(self.signup_window, text="Registrar", height=2, width=24,
                                     command=self.data_sign_up)
        register_button.place(x=card_x+card_w//2, y=card_y+230, anchor='center')

        # Submit with Enter key from either input
        self.signup_window.bind('<Return>', lambda _e: self.data_sign_up())

        # ...existing code...

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



