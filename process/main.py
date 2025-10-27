import pandas as pd
from datetime import datetime
import threading
import time
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
        # Intentar leer Excel; si falta dependencia (openpyxl) o hay error, usar CSV o crear nuevo DataFrame
        try:
            df = pd.read_excel(excel_path)
        except Exception as e:
            # Puede ser FileNotFoundError o ImportError por openpyxl faltante u otro problema.
            try:
                # Intentar leer CSV equivalente como fallback
                df = pd.read_csv(excel_path)
            except Exception:
                # Crear DataFrame vacío con las columnas esperadas
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
            try:
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
            except Exception:
                # En caso de estructura inesperada, simplemente agregar la fila
                new_row = {
                    "Nombre": nombre,
                    "Apellido": apellido,
                    "Hora de entrada": "",
                    "Hora de salida": hora_salida,
                    "Fecha": fecha
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        # Intentar guardar en Excel; si falla (p.e. falta openpyxl), guardar en CSV como fallback
        try:
            df.to_excel(excel_path, index=False)
        except Exception as e:
            try:
                csv_path = os.path.splitext(excel_path)[0] + '.csv'
                df.to_csv(csv_path, index=False)
                print(f"Warning: no fue posible guardar como Excel ({e}). Se guardó como CSV: {csv_path}")
            except Exception as e2:
                print(f"Error guardando attendance: {e2}")
    def _resolve_fullname_from_code(self, code: str):
        """Dado un código de usuario, intenta leer el nombre completo desde process/database/users/<code>.txt
        Retorna (nombre, apellido). Si no existe, retorna (code, '')."""
        try:
            from process.database.config import DataBasePaths
            db = DataBasePaths()
            user_file = os.path.join(db.users, f"{code}.txt")
            if os.path.exists(user_file):
                with open(user_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    # formato esperado: "Nombre Apellido,code,"
                    parts = [p for p in content.split(',') if p]
                    if parts:
                        full = parts[0].strip()
                        if ' ' in full:
                            nombre, apellido = full.split(' ', 1)
                            return nombre, apellido
                        return full, ''
        except Exception:
            pass
        return code, ''

    def _slugify_name(self, name: str) -> str:
        import re
        s = name.strip().lower()
        s = re.sub(r"[^a-z0-9\s_-]", "", s)
        s = re.sub(r"[\s_-]+", "_", s).strip("_")
        return s or "usuario"

    def _ensure_unique_code(self, base: str) -> str:
        # Evita colisión de archivo en faces y users
        b = base
        i = 2
        faces_dir = self.database.faces
        users_dir = self.database.users
        while True:
            face_path = os.path.join(faces_dir, f"{b}.png")
            user_path = os.path.join(users_dir, f"{b}.txt")
            if not os.path.exists(face_path) and not os.path.exists(user_path):
                return b
            b = f"{base}-{i}"
            i += 1
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

        # performance/tuning
        self.display_interval_ms = int(os.getenv("DISPLAY_INTERVAL_MS", "33"))  # ~30 FPS
        self.proc_width = int(os.getenv("PROC_WIDTH", "640"))  # downscale for processing
        self.downscale_enabled = os.getenv("DOWNSCALE", "1") not in ("0", "false", "False")
        self.use_segmentation = os.getenv("PERSON_SEGMENT", "1") not in ("0", "false", "False")

        # async capture (latest-frame buffer)
        self._frame_lock = threading.Lock()
        self._latest_frame = None
        self._capture_running = True
        self._capture_thread = threading.Thread(target=self._capture_loop, name="CaptureLoop", daemon=True)
        self._capture_thread.start()

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
            self._capture_running = False
        except Exception:
            pass
        try:
            if hasattr(self, '_capture_thread') and self._capture_thread and self._capture_thread.is_alive():
                self._capture_thread.join(timeout=1.0)
        except Exception:
            pass
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
        frame_bgr = self._get_latest_frame()
        if frame_bgr is None:
            if self.login_video:
                self.login_video.after(10, self.facial_login)
            return

        # optional downscale for processing
        proc_frame = self._resize_to_width(frame_bgr, self.proc_width) if self.downscale_enabled else frame_bgr

        # process in BGR
        frame_processed, matcher, info = self.face_login.process(proc_frame)

        # apply person segmentation
        if self.use_segmentation:
            seg_frame = self.segmenter.apply(frame_processed)
        else:
            seg_frame = frame_processed

        # display (convert to RGB only for Tk)
        frame_show = self._resize_to_width(seg_frame, 1280)
        frame_show = cv2.cvtColor(frame_show, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(frame_show)
        img = ImageTk.PhotoImage(image=im)

        self.login_video.configure(image=img)
        self.login_video.image = img
        self.login_video.after(self.display_interval_ms, self.facial_login)

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
        # Preferir el nombre reconocido por el login si está disponible
        recognized = None
        try:
            recognized = getattr(self.face_login, 'last_user_name', None)
        except Exception:
            recognized = None
        if recognized:
            # recognized generalmente es el código (basename del PNG). Intentar resolver a nombre completo.
            nombre, apellido = self._resolve_fullname_from_code(recognized.strip())
        elif hasattr(self, 'name') and self.name:
            # fallback al nombre almacenado durante el registro
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
        frame_bgr = self._get_latest_frame()
        if frame_bgr is not None:
            # optional downscale for processing
            proc_frame = self._resize_to_width(frame_bgr, self.proc_width) if self.downscale_enabled else frame_bgr
            # process en BGR
            frame_processed, save_image, info = self.face_sign_up.process(proc_frame, self.user_code)

            # aplicar segmentación de persona sobre el fondo
            if self.use_segmentation:
                seg_frame = self.segmenter.apply(frame_processed)
            else:
                seg_frame = frame_processed
            # config video (convertir a RGB solo para mostrar)
            frame_show = self._resize_to_width(seg_frame, 1280)
            frame_show = cv2.cvtColor(frame_show, cv2.COLOR_BGR2RGB)
            im = Image.fromarray(frame_show)
            img = ImageTk.PhotoImage(image=im)

            # show frames
            self.signup_video.configure(image=img)
            self.signup_video.image = img
            self.signup_video.after(self.display_interval_ms, self.facial_sign_up)

            if save_image:
                self.signup_video.after(3000, self.close_signup)
        else:
            # try again shortly
            if self.signup_video:
                self.signup_video.after(10, self.facial_sign_up)

    def data_sign_up(self):
        # extraer solo el nombre
        self.name = self.input_name.get()
        if self.name in ("Enter your name", None):
            self.name = ""
        if len(self.name) == 0:
            print('¡Formulary incomplete!')
            return

        # generar código desde el nombre y asegurar unicidad
        base_code = self._slugify_name(self.name)
        self.user_code = self._ensure_unique_code(base_code)

        # guardar datos mínimos del usuario
        self.data.append(self.name)
        self.data.append(self.user_code)

        try:
            os.makedirs(self.database.users, exist_ok=True)
            with open(f"{self.database.users}/{self.user_code}.txt", 'w', encoding='utf-8') as file:
                file.writelines(self.name + ',')
                file.writelines(self.user_code + ',')
        except Exception as e:
            print(f'Error saving user data: {e}')

        # limpiar entrada
        try:
            self.input_name.delete(0, Tk.END)
        except Exception:
            pass

        # abrir ventana de captura facial
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

        # Card parameters (sin campo de código)
        card_w, card_h = 500, 260
        card_x, card_y = (1280 - card_w) // 2, (720 - card_h) // 2
        card_radius = 40
        self.signup_card = Canvas(self.signup_window, width=card_w, height=card_h, bg='#e0e0e0', highlightthickness=0)
        self.signup_card.place(x=card_x, y=card_y)
        # Draw rounded card
        self.signup_card.create_oval(0, 0, card_radius*2, card_radius*2, fill='#e0e0e0', outline='')
        self.signup_card.create_oval(card_w-card_radius*2, 0, card_w, card_radius*2, fill='#e0e0e0', outline='')
        self.signup_card.create_oval(0, card_h-card_radius*2, card_radius*2, card_h, fill='#e0e0e0', outline='')
        self.signup_card.create_oval(card_w-card_radius*2, card_h-card_radius*2, card_w, card_h, fill='#e0e0e0', outline='')
        self.signup_card.create_rectangle(card_radius, 0, card_w-card_radius, card_h, fill='#e0e0e0', outline='')
        self.signup_card.create_rectangle(0, card_radius, card_w, card_h-card_radius, fill='#e0e0e0', outline='')

        # Title REGISTER
        self.signup_card.create_text(card_w//2, 40, text="REGISTER", font=("Segoe UI", 28, "bold"), fill="#222")

        # NAME label
        label_x = card_w//2 - 50
        input_x = card_w//2 - 10
        self.signup_card.create_text(label_x, 95, text="NAME:", font=("Segoe UI", 14, "bold"), fill="#222", anchor='e')
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
        self.input_name.place(x=card_x+input_x, y=card_y+80, anchor='w', width=260, height=32)
        _add_placeholder(self.input_name, "Enter your name")

        # Botón FACE CAPTURE
        btn_w, btn_h, btn_r = 220, 48, 24
        btn_x, btn_y = card_w//2 - btn_w//2, 170
        def draw_signup_btn(canvas, x, y, w, h, r, color, text, tag):
            canvas.create_oval(x, y, x+2*r, y+2*r, fill=color, outline=color, tags=tag)
            canvas.create_oval(x+w-2*r, y, x+w, y+2*r, fill=color, outline=color, tags=tag)
            canvas.create_oval(x, y+h-2*r, x+2*r, y+h, fill=color, outline=color, tags=tag)
            canvas.create_oval(x+w-2*r, y+h-2*r, x+w, y+h, fill=color, outline=color, tags=tag)
            canvas.create_rectangle(x+r, y, x+w-r, y+h, fill=color, outline=color, tags=tag)
            canvas.create_rectangle(x, y+r, x+w, y+h-r, fill=color, outline=color, tags=tag)
            canvas.create_text(x+w//2, y+h//2, text=text, font=("Segoe UI", 16, "bold"), fill="#ff9800", tags=tag)
        draw_signup_btn(self.signup_card, btn_x, btn_y, btn_w, btn_h, btn_r, "#222", "FACE CAPTURE", "signup_btn")
        def on_signup_btn_click(event):
            self.data_sign_up()
        self.signup_card.tag_bind("signup_btn", "<Button-1>", on_signup_btn_click)

        # Submit with Enter key
        self.signup_window.bind('<Return>', lambda _e: self.data_sign_up())

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

        # ===== Centered Card with Buttons and Title ===== #
        card_w, card_h = 500, 320
        card_x, card_y = (1280 - card_w) // 2, (720 - card_h) // 2
        self.main_card = Canvas(self.frame, width=card_w, height=card_h, bg='#e0e0e0', highlightthickness=0)
        self.main_card.place(x=card_x, y=card_y)
        # Draw fully rounded card background
        card_radius = 60
        self.main_card.create_oval(0, 0, card_radius*2, card_radius*2, fill='#e0e0e0', outline='#e0e0e0')
        self.main_card.create_oval(card_w-card_radius*2, 0, card_w, card_radius*2, fill='#e0e0e0', outline='#e0e0e0')
        self.main_card.create_oval(0, card_h-card_radius*2, card_radius*2, card_h, fill='#e0e0e0', outline='#e0e0e0')
        self.main_card.create_oval(card_w-card_radius*2, card_h-card_radius*2, card_w, card_h, fill='#e0e0e0', outline='#e0e0e0')
        self.main_card.create_rectangle(card_radius, 0, card_w-card_radius, card_h, fill='#e0e0e0', outline='#e0e0e0')
        self.main_card.create_rectangle(0, card_radius, card_w, card_h-card_radius, fill='#e0e0e0', outline='#e0e0e0')

        # Title WELCOME
        self.main_card.create_text(card_w//2, 48, text="WELCOME", font=("Segoe UI", 28, "bold"), fill="#222")

        # Custom rounded buttons
        btn_w, btn_h, btn_r = 340, 56, 28
        btn_y1 = 90
        btn_y2 = 170
        # Draw rounded rectangles for buttons
        def draw_button(canvas, x, y, w, h, r, color, text, tag):
            canvas.create_oval(x, y, x+2*r, y+2*r, fill=color, outline=color, tags=tag)
            canvas.create_oval(x+w-2*r, y, x+w, y+2*r, fill=color, outline=color, tags=tag)
            canvas.create_oval(x, y+h-2*r, x+2*r, y+h, fill=color, outline=color, tags=tag)
            canvas.create_oval(x+w-2*r, y+h-2*r, x+w, y+h, fill=color, outline=color, tags=tag)
            canvas.create_rectangle(x+r, y, x+w-r, y+h, fill=color, outline=color, tags=tag)
            canvas.create_rectangle(x, y+r, x+w, y+h-r, fill=color, outline=color, tags=tag)
            canvas.create_text(x+w//2, y+h//2, text=text, font=("Segoe UI", 16, "bold"), fill="#c62828", tags=tag)

        draw_button(self.main_card, (card_w-btn_w)//2, btn_y1, btn_w, btn_h, btn_r, "#ffe5e5", "Facial Access - Entry", "login_btn")
        draw_button(self.main_card, (card_w-btn_w)//2, btn_y2, btn_w, btn_h, btn_r, "#ffe5e5", "Facial Sign Up - Register", "signup_btn")

        # Bind click events to canvas buttons
        def on_login_click(event):
            self.gui_login()
        def on_signup_click(event):
            self.gui_signup()
        self.main_card.tag_bind("login_btn", "<Button-1>", on_login_click)
        self.main_card.tag_bind("signup_btn", "<Button-1>", on_signup_click)

    # ================= Helper methods: responsive backgrounds ================= #
    def _capture_loop(self):
        # Read frames as fast as possible; keep only the latest frame
        while self._capture_running and self.cap:
            ret, frame = self.cap.read()
            if ret:
                with self._frame_lock:
                    self._latest_frame = frame
            else:
                time.sleep(0.01)
        # end loop

    def _get_latest_frame(self):
        try:
            with self._frame_lock:
                if self._latest_frame is None:
                    return None
                return self._latest_frame.copy()
        except Exception:
            return None

    def _resize_main_bg(self):
        if self.bg_image_orig is None or self.bg_label is None:
            return
        w = max(1, self.frame.winfo_width())
        h = max(1, self.frame.winfo_height())
        try:
            img_resized = self.bg_image_orig.resize((w, h), Image.BICUBIC)
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
            img_resized = self.signup_bg_image_orig.resize((w, h), Image.BICUBIC)
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



