# Control de acceso facial con IA
Sistema de control de acceso usando visión por computador y modelos de reconocimiento facial. Incluye interfaz gráfica (Tkinter), captura de cámara, registro de usuarios y comunicación serie con un controlador de puerta.

## ¿Cómo funciona?

- Captura de cámara: OpenCV abre la webcam y entrega frames a la app.
- Detección y landmarks: MediaPipe detecta rostros y malla facial para validar pose/alineación.

- Recorte y base de datos: Se recorta el rostro y se guarda como imagen por código de usuario en `process/database/faces`.
- Matching: Compara el rostro actual con la base usando DeepFace (por defecto modelo SFace) y autoriza si hay coincidencia.
- Registro de accesos: Guarda un log con fecha/hora en `process/database/users/<usuario>.txt`.

- Control de puerta: Se envía por serie el comando `A` (abrir) o `C` (cerrar) hacia un microcontrolador (ej. VEX V5, Arduino, etc.).

Estructura clave:

- `process/main.py`: GUI principal (login y registro).
- `process/face_processing/*`: Utilidades de rostro (detección, mesh, matching) y flujo de login/signup.
- `process/database/*`: Rutas y almacenamiento de rostros/usuarios.

- `process/com_interface/serial_com.py`: Comunicación serie.
- `door_control/src/main.py`: Firmware de ejemplo para el controlador de la puerta (VEX V5) que recibe `A/C`.

## Mejoras recientes

- Robustez de cámara: índice configurable por variable `CAMERA_INDEX` y cierre ordenado.
- Colores consistentes: el pipeline trabaja en BGR y sólo convierte a RGB al mostrar.

- Recorte y guardado seguros: límites dentro de la imagen y creación automática de carpetas.
- Modelo de matching seleccionable con `FACE_MODEL` (SFace por defecto).
- Comunicación serie configurable (`SERIAL_PORT`, `SERIAL_BAUD`) y tolerante a ausencia de dispositivo.

- GUI tolerante a recursos: si faltan imágenes, usa colores/botones de texto.

## Requisitos e instalación

- Python 3.10 (recomendado)
- Sistema operativo: Windows, Linux o macOS
- Dependencias principales: OpenCV, NumPy, Pillow, MediaPipe, DeepFace, face-recognition, dlib, pyserial, etc.

Instala dependencias:

```bash
# en Windows, con Python 3.10 activo
pip install -r requirements.txt
```

Notas Windows:
- Este proyecto NO requiere dlib/CMake si usas modelos de DeepFace (SFace/ArcFace/etc.).
- `deepface` descarga modelos la primera vez; requiere conexión.
 
Nota adicional: si al ejecutar la app ves un error como "Missing optional dependency 'openpyxl'" (pandas al leer/guardar Excel), instala `openpyxl`:

```bash
pip install openpyxl
```

## Guía paso a paso (Windows - Git Bash)

Sigue estos pasos para tener todo funcionando de principio a fin. Los comandos están pensados para Windows usando Git Bash (bash.exe). Si usas PowerShell o CMD, adapta la sintaxis de variables.

1) Clonar el repo y entrar a la carpeta del proyecto

```bash
git clone <tu-fork-o-este-repo>
cd computervision
```

2) Crear un entorno virtual y activarlo

```bash
python -m venv .venv
source .venv/Scripts/activate
```

3) Instalar dependencias del proyecto

- Opción A (desde terminal):

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

- Opción B (desde VS Code): ejecuta la Tarea "install-reqs" incluida en el workspace (hace lo mismo que A).

4) Variables de entorno recomendadas (puedes exportarlas antes de ejecutar)

```bash
# Cámara y procesamiento
export CAMERA_INDEX=0           # índice de cámara (0 por defecto)
export DOWNSCALE=1              # 1 para procesar escalado (más rápido)
export PROC_WIDTH=640           # ancho de procesamiento
export PERSON_SEGMENT=1         # 1 para segmentación de persona (MediaPipe)

# Fondo de la GUI (opcional)
export GUI_BACKGROUND="process/gui/setup/images/gui_init_image.png"

# Modelo de matching facial local (cuando USE_IA_SERVICE=0)
# Valores válidos: SFace (default), ArcFace, VGG-Face, Facenet, Facenet512, OpenFace,
#                   DeepFace, DeepID, Dlib, GhostFaceNet
export FACE_MODEL=SFace

# Puerto serie para abrir/cerrar puerta (opcional)
export SERIAL_PORT=COM6
export SERIAL_BAUD=115200

# Microservicio IA (opcional)
export USE_IA_SERVICE=1         # 1=usar API de verificación, 0=matching local
export IA_SERVICE_URL=http://localhost:8000
```

5) Ejecutar la aplicación de escritorio (GUI)

```bash
python -m examples.example
```

Esto abrirá la ventana principal con dos botones:
- Facial Access - Entry: inicia el flujo de verificación/acceso.
- Facial Sign Up - Register: abre el registro facial del usuario.

6) Registrar un usuario (necesario antes del login)

- Haz clic en "Facial Sign Up - Register".
- Escribe Nombre y Código de Usuario (único). Pulsa Enter o el botón "FACE CAPTURE".
- Mira a la cámara unos segundos. Se guardará la imagen en `process/database/faces/<codigo>.png`.
- Se crea/actualiza el archivo `process/database/users/<codigo>.txt` con el alta del usuario.

7) Iniciar sesión facial (acceso)

- Haz clic en "Facial Access - Entry".
- Mira a la cámara ~3 segundos para comparar contra la base de rostros.
- Si coincide: se envía `A` por serie para abrir y se registra acceso; a los 3s se envía `C` para cerrar.
- También se guarda/actualiza `attendance.xlsx` con hora de entrada/salida según corresponda.

8) Microservicio IA (obligatorio para Odoo)

La app verifica el rostro usando el microservicio IA vía API (`IA_SERVICE_URL`). Debes tenerlo corriendo antes de hacer login:

```bash
cd ia_service
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
uvicorn ia_service.main:app --reload --host 0.0.0.0 --port 8000
```

Notas:
- Este microservicio usa `face_recognition` (basado en dlib). En Windows puede requerir compilación.
- Endpoint salud: `GET /health`.
- Para integración con Odoo, apunta `mi_empresa_facial_checkin.ia_api_url` al endpoint del microservicio (ver sección Odoo).

9) Controlador de puerta (opcional)

- Por defecto, si el puerto serie no existe, la app continúa sin error.
- Conecta tu microcontrolador (VEX/Arduino/etc.) y ajusta `SERIAL_PORT`/`SERIAL_BAUD`.
- Firmware de ejemplo: `door_control/src/main.py`.

10) Dónde se guardan los datos

- Rostros registrados: `process/database/faces/`
- Usuarios y logs de acceso: `process/database/users/`
- Asistencias (Excel): `attendance.xlsx` en la raíz del proyecto

11) Problemas comunes y tips

- La cámara no abre: cambia `CAMERA_INDEX` o cierra otras apps que la usen.
- Lento al comparar: usa `FACE_MODEL=SFace` o `ArcFace`. Activa `DOWNSCALE=1` y ajusta `PROC_WIDTH`.
- MediaPipe Selfie Segmentation no disponible: la imagen se mostrará sin segmentación (la app sigue funcionando).
- Sin dispositivo serie: la app funciona; configura `SERIAL_PORT` cuando conectes el controlador.
- Modelos DeepFace: la primera vez descargan pesos (requiere Internet).

## Ejecutar la app

```bash
python -m examples.example
```

Variables de entorno útiles:
- `CAMERA_INDEX`: índice de cámara (por defecto 0).
- `FACE_MODEL`: `SFace` (default), `ArcFace`, `VGG-Face`, `Facenet`, `Facenet512`, `OpenFace`, `DeepFace`, `DeepID`, `Dlib`, `GhostFaceNet`.

- `SERIAL_PORT`: puerto serie (por defecto `COM6` en Windows).
- `SERIAL_BAUD`: baudrate serie (por defecto `115200`).

Extra:
- `USE_IA_SERVICE`: 1 (default) para usar el microservicio IA. Si trabajas con Odoo, deja 1.
- `REQUIRE_IA_SERVICE`: 1 (default) para exigir microservicio; si está caído, no se hará fallback local.
- `IA_SERVICE_URL`: URL base del microservicio IA (por defecto `http://localhost:8000`).
- `DOWNSCALE`, `PROC_WIDTH`, `PERSON_SEGMENT`: tuning de rendimiento/segmentación.
- `GUI_BACKGROUND`: ruta a imagen de fondo para la GUI.

Ejemplo Windows PowerShell:

```bash
$env:CAMERA_INDEX=0; $env:SERIAL_PORT="COM6"; python -m examples.example
```

## Registrar un usuario
1) Botón "Registrar rostro".
2) Introduce el nombre de la persona.

3) Coloca el rostro al centro; la app genera automáticamente un identificador a partir del nombre y guarda `process/database/faces/<id_generado>.png`.

## Iniciar sesión facial

1) Botón "Iniciar sesión facial".
2) Mira a la cámara ~3 segundos hasta comparar; si coincide, se envía `A` y se registra acceso.

## Integración con controlador de puerta
- En `door_control/src/main.py` se muestra un ejemplo para VEX V5 que abre/cierra al recibir `A/C`.
- Para Arduino/otros, ajusta `serial_com.py` (puerto/baud) y el firmware para escuchar un byte y accionar un motor/relé.

## Solución de problemas
- No abre la cámara: cambia `CAMERA_INDEX` o libera la cámara de otras apps.
- ImportError de OpenCV/Pillow/Imutils: verifica `pip install -r requirements.txt` en el mismo entorno de Python.

- Modelos DeepFace lentos: usa `FACE_MODEL=SFace` o `ArcFace` y asegura que no estás en CPU muy limitada.
- No hay dispositivo serie: la app sigue funcionando; configura `SERIAL_PORT` cuando conectes el controlador.

## Recursos
- Video introductorio: [YouTube](https://youtu.be/jxiCDufWop8?si=gtu70gDS1swRXZRB)
- Modelos: [Hugging Face](https://huggingface.co/AprendeIngenia/control_de_acceso_facial_con_ia/tree/main)

## Contacto
Si tiene preguntas o consultas relacionadas con este proyecto, no dude en contactarnos en nuestro canal de Youtube [Aprende e Ingenia](https://www.youtube.com/@AprendeIngenia/videos). ¡Gracias por visitar nuestro repositorio! :smile:

### Apoya el proyecto
- Suscríbete al canal de YouTube: [Canal YouTube](https://www.youtube.com/channel/UCzwHEOCbsZLjfELperJ6VeQ/videos)
- Sígueme: [Instagram](https://www.instagram.com/santiagsanchezr/) | [Twitter/X](https://twitter.com/SantiagSanchezR)
# control-de-acceso-facial-con-ia
Hola, chicos en este repositorio encontrarán la programación para que puedan crear su sistema de control de acceso con reconocimiento facial, utilizando inteligencia artificial.

### Conceptos introductorios:
- Este repositorio contiene el código fuente en Python para ejecutar y utilizar nuestro sistema de control de acceso inteligente, utilizando visión por computadora e inteligencia artificial.
- Para iniciar recomendamos ver algunos conceptos introductorios con el fin de entender un poco mejor todo el funcionamiento, por eso te dejamos la explicacion en este [video.](https://youtu.be/jxiCDufWop8?si=gtu70gDS1swRXZRB)
- Los modelos lo puedes encontrar [aqui.](https://huggingface.co/AprendeIngenia/control_de_acceso_facial_con_ia/tree/main)

![3D](https://github.com/AprendeIngenia/control-de-acceso-facial-con-ia/assets/85022752/6f8e7705-d33e-47b9-a6b4-29189b38496b)

### Instalacion:
Para utilizar este código, asegúrese de cumplir con los siguientes requisitos previos:

- Sistema operativo compatible: Windows, Linux o macOS
- Versión de Python: 3.10
- Paquetes adicionales: NumPy, OpenCV, TensorFlo, etc. Consulte el archivo [requirements.txt](https://github.com/AprendeIngenia/control-de-acceso-facial-con-ia/blob/main/requirements.txt) para ver la lista completa de dependencias.

### Contacto
Si tiene preguntas o consultas relacionadas con este proyecto, no dude en contactarnos en nuestro canal de Youtube [Aprende e Ingenia](https://www.youtube.com/@AprendeIngenia/videos). Le responderemos tan pronto como nos sea posible.
Gracias por visitar nuestro repositorio y esperamos que disfrute trabajando con nuestro codigo. :smile:

# Recuerda que puedes contribuir a que siga desarrollando:
Simplemente suscribiendote a mi canal de YouTube:
- [Canal YouTube](https://www.youtube.com/channel/UCzwHEOCbsZLjfELperJ6VeQ/videos)

### Siguiendome en mis redes sociales: 
- [Instagram](https://www.instagram.com/santiagsanchezr/)
- [Twitter](https://twitter.com/SantiagSanchezR)

## Integración con Odoo: Fichaje Facial + GPS

Este repositorio ahora incluye una arquitectura para integrar el sistema con Odoo (Asistencias) usando un módulo propio y un microservicio IA (FastAPI):

- Módulo Odoo: `odoo_addons/mi_empresa_facial_checkin`
	- Extiende `hr.employee` (campos: `x_face_encoding`, `x_face_reference_image`).
	- Extiende `hr.attendance` (campos: `x_checkin_*` y `x_checkout_*` para lat/long/foto).
	- Controlador JSON: `/hr/attendance/facial_check` (recibe imagen base64 + GPS y crea asistencia si el rostro coincide).
	- Widget JS: activa cámara, obtiene GPS y envía la captura al controlador.

- Microservicio IA: `ia_service/`
	- FastAPI con endpoint `POST /verify_face` que compara la captura con el encoding guardado.

### Cómo ejecutar el microservicio (desarrollo)

```bash
cd ia_service
python -m venv .venv
source .venv/bin/activate  # En Windows con Git Bash
python -m pip install -r requirements.txt
uvicorn ia_service.main:app --reload --host 0.0.0.0 --port 8000
```

Opcional: ajusta el umbral de distancia en `ia_service/main.py` (por defecto 0.6).

### Configurar Odoo

1) Copia o añade la ruta `odoo_addons` a la ruta de addons de tu servidor Odoo.
2) Actualiza la lista de apps y instala el módulo "Mi Empresa - Fichaje Facial".
3) En Ajustes > Parámetros del sistema, crea el parámetro:
	 - Clave: `mi_empresa_facial_checkin.ia_api_url`
	 - Valor: `http://<host_del_microservicio>:8000/verify_face`
4) En cada empleado, sube `Foto de Referencia` y pega `Codificación Facial` (formato `[0.1, 0.2, ...]`).
5) En Asistencias, usa el modo "kiosco facial". El botón abrirá cámara y GPS (requiere HTTPS en producción).

Notas:
- Para móviles/navegador, la cámara y geolocalización requieren contexto seguro (HTTPS) y permisos del usuario.
- Si necesitas comparación local en el servidor Odoo (sin microservicio), adapta el controlador para usar `face_recognition` directamente.
