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

## Ejecutar la app

```bash
python -m examples.example
```

Variables de entorno útiles:
- `CAMERA_INDEX`: índice de cámara (por defecto 0).
- `FACE_MODEL`: `SFace` (default), `ArcFace`, `VGG-Face`, `Facenet`, `Facenet512`, `OpenFace`, `DeepFace`, `DeepID`, `Dlib`, `GhostFaceNet`.

- `SERIAL_PORT`: puerto serie (por defecto `COM6` en Windows).
- `SERIAL_BAUD`: baudrate serie (por defecto `115200`).

Ejemplo Windows PowerShell:

```bash
$env:CAMERA_INDEX=0; $env:SERIAL_PORT="COM6"; python -m examples.example
```

## Registrar un usuario
1) Botón "Registrar rostro".
2) Introduce nombre y código de usuario (único).

3) Coloca el rostro al centro; la app recorta y guarda `process/database/faces/<codigo>.png`.

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
