import sys
import schedule
import time
import datetime
import winsound  # Seguimos usando winsound para la alarma simple
from PyQt6.QtWidgets import QApplication, QWidget, QProgressBar
from PyQt6.QtCore import Qt, QTimer, QRect, QTime
from PyQt6.QtGui import QScreen, QColor
import os  # Importa el módulo os para manipulación de rutas

# --- Constantes ---
WORK_MINUTES = 50 # Duración del trabajo en minutos
BREAK_MINUTES = 10  # Duración del descanso en minutos
WORK_SECONDS = WORK_MINUTES * 60
BREAK_SECONDS = BREAK_MINUTES * 60
START_TIME_STR = "07:00" # Hora de inicio HH:MM (24h)
END_HOUR = 17 # Hora (24h) después de la cual ya no se inician más ciclos (e.g., 5 PM)
SOON_ALARM_THRESHOLD_MINUTES = 5 # Minutos antes de que suene la alarma "soon"

LUNCH_BREAK_START_HOUR = 11 # Hora de inicio del almuerzo (24h)
LUNCH_BREAK_END_HOUR = 13 # Hora de fin del almuerzo (24h)

# --- Configuración de la barra ---

BAR_HEIGHT = 2  # Altura de la barra en píxeles (ajústala a tu gusto)
WORK_COLOR = "orange" # Color de la barra en trabajo
BREAK_COLOR = "lightgreen" # Color de la barra en descanso
IDLE_COLOR = "lightgray" # Color cuando no está en ciclo Pomodoro

UPDATE_INTERVAL_MS = 100 # Milisegundos. Con qué frecuencia actualizar la barra (más bajo = más suave)
SCHEDULE_CHECK_INTERVAL_MS = 30000 # Cada cuántos ms revisar si es hora de iniciar (30 seg)

# --- Configuración para el sonido de alarma ---
ALARM_SOUND_PATH = "sounds/alarm.wav" # Ruta al archivo de sonido de fin de ciclo
SOON_ALARM_PATH = "sounds/soon.wav" # Ruta al archivo de sonido de aviso de fin de ciclo
BEEP_FREQUENCY = 1500  # Hz
BEEP_DURATION = 500   # ms

class PomodoroBar(QWidget):
    def __init__(self):
        super().__init__()
        self.current_mode = 'idle' # 'idle', 'work', 'break'
        self.seconds_elapsed = 0
        self.total_seconds_in_mode = 1 # Evitar división por cero al inicio
        self.soon_alarm_played = False # Flag para evitar que la alarma "soon" suene repetidamente

        self.initUI()
        self.initTimers()
        self.setupScheduler()

    def initUI(self):
        # Configurar la ventana: sin bordes, siempre encima, tipo "herramienta" (minimiza presencia en taskbar)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        # Opcional: Hacer el fondo de la ventana transparente (si la barra no la ocupa toda)
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Obtener dimensiones de la pantalla principal y posicionar la ventana arriba
        primary_screen = QApplication.primaryScreen()
        if not primary_screen:
            print("Error: No se pudo obtener la pantalla principal.")
            #Fallback a tamaño por defecto si falla la detección
            screen_geometry = QRect(0, 0, 1920, 1080)
        else:
            screen_geometry = primary_screen.geometry()

        self.bar_width = screen_geometry.width()
        self.setGeometry(0, 0, self.bar_width, BAR_HEIGHT)

        # Crear y configurar la barra de progreso
        self.progressBar = QProgressBar(self)
        self.progressBar.setGeometry(0, 0, self.bar_width, BAR_HEIGHT)
        self.progressBar.setTextVisible(False) # No mostrar texto (porcentaje)
        self.progressBar.setRange(0, 1000) # Rango 0-1000 para una apariencia más suave
        self.updateBarStyle() # Aplicar estilo inicial (idle)
        self.progressBar.setValue(0)

        self.show()

    def updateBarStyle(self):
        """Actualiza el color de la barra según el modo actual."""
        color = IDLE_COLOR
        if self.current_mode == 'work':
            color = WORK_COLOR
        elif self.current_mode == 'break':
            color = BREAK_COLOR

        # Usar Qt Style Sheets (similar a CSS) para dar estilo
        style_sheet = f"""
        QProgressBar {{
            border: none; /* Sin borde */
            background-color: transparent; /* Fondo transparente */
        }}
        QProgressBar::chunk {{
            background-color: {color}; /* Color del progreso */
        }}
        """
        self.progressBar.setStyleSheet(style_sheet)
        # Asegurarse que el tamaño es correcto tras cambiar estilo
        self.progressBar.setGeometry(0, 0, self.bar_width, BAR_HEIGHT)


    def initTimers(self):
        """Inicializa los QTimers para la lógica del Pomodoro y la revisión del schedule."""
        # Timer principal para la cuenta atrás y actualización de la GUI
        self.pomodoro_timer = QTimer(self)
        self.pomodoro_timer.timeout.connect(self.update_pomodoro)
        # Timer secundario para revisar la librería 'schedule' periódicamente
        self.schedule_timer = QTimer(self)
        self.schedule_timer.timeout.connect(self.check_schedule)
        self.schedule_timer.start(SCHEDULE_CHECK_INTERVAL_MS)

    def setupScheduler(self):
        """Configura la tarea en 'schedule' para iniciar a las 7 AM."""
        print(f"Programando inicio de Pomodoro para las {START_TIME_STR} cada día.")
        schedule.every().day.at(START_TIME_STR).do(self.start_pomodoro_flow)
        # También verificar al inicio si ya deberíamos estar en un ciclo
        self.check_if_should_be_running()

    def check_schedule(self):
        """Función llamada por schedule_timer para ejecutar tareas pendientes de 'schedule'."""
        # print("Checking schedule...") # Descomentar para depuración
        schedule.run_pending()

    def check_if_should_be_running(self):
        """Comprueba si la hora actual está dentro del rango activo (7 AM - END_HOUR)
            y si la barra está inactiva, para iniciar el ciclo. También gestiona la pausa del almuerzo."""
        now_time = datetime.datetime.now().time()
        now_hour = datetime.datetime.now().hour

        # Comprobar si estamos en la hora del almuerzo
        if LUNCH_BREAK_START_HOUR <= now_hour < LUNCH_BREAK_END_HOUR:
            if self.current_mode != 'idle':
                print(f"[{now_time.strftime('%H:%M:%S')}] Hora de almuerzo ({LUNCH_BREAK_START_HOUR}:00 - {LUNCH_BREAK_END_HOUR}:00). Pausando.")
                self.switch_mode('idle')
            return

        if self.current_mode != 'idle':
            return # Ya está corriendo

        try:
            start_time = datetime.datetime.strptime(START_TIME_STR, "%H:%M").time()
            end_time = datetime.time(END_HOUR, 0)

            if start_time <= now_time < end_time:
                print(f"[{now_time.strftime('%H:%M:%S')}] Hora actual dentro del rango activo. Iniciando flujo.")
                self.start_pomodoro_flow()
            else:
                print(f"[{now_time.strftime('%H:%M:%S')}] Hora actual fuera del rango activo ({START_TIME_STR} - {END_HOUR}:00).")

        except ValueError:
            print(f"Error: Formato de START_TIME_STR ('{START_TIME_STR}') inválido. Use HH:MM.")


    def start_pomodoro_flow(self):
        """Inicia la secuencia de Pomodoros para el día."""
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Recibida señal para iniciar Pomodoro Flow.")
        now_hour = datetime.datetime.now().hour
        # Prevenir re-inicio si ya está activo
        if self.pomodoro_timer.isActive() and self.current_mode != 'idle':
            print("Pomodoro ya está activo.")
            return
        # Verificar si es demasiado tarde para empezar hoy o si estamos en la hora del almuerzo
        if now_hour >= END_HOUR or (LUNCH_BREAK_START_HOUR <= now_hour < LUNCH_BREAK_END_HOUR):
            print(f"Son las {datetime.datetime.now().hour}h o más tarde, o es hora de almuerzo. No se iniciará ahora.")
            self.switch_mode('idle') # Asegurar estado idle
            return

        self.switch_mode('work') # Empezar con un ciclo de trabajo

    def switch_mode(self, new_mode):
        """Cambia entre los modos 'work', 'break', e 'idle'."""
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Cambiando modo a: {new_mode}")
        self.current_mode = new_mode
        self.seconds_elapsed = 0 # Reiniciar contador de tiempo transcurrido
        self.soon_alarm_played = False # Resetear el flag al cambiar de modo

        if new_mode == 'work':
            self.total_seconds_in_mode = WORK_SECONDS
        elif new_mode == 'break':
            self.total_seconds_in_mode = BREAK_SECONDS
        else: # 'idle'
            self.total_seconds_in_mode = 1 # Evitar división por cero
            self.pomodoro_timer.stop() # Detener el timer principal
            self.progressBar.setValue(0) # Reiniciar barra visualmente
            self.updateBarStyle() # Poner color 'idle'
            return # No iniciar el timer si es 'idle'

        # Configurar para el nuevo modo (work o break)
        self.updateBarStyle() # Aplicar el color correcto
        self.progressBar.setValue(0) # Reiniciar barra visualmente
        if not self.pomodoro_timer.isActive():
            # Iniciar el timer principal si no estaba activo
            self.pomodoro_timer.start(UPDATE_INTERVAL_MS)

    def update_pomodoro(self):
        """Función llamada por pomodoro_timer para actualizar el progreso."""
        if self.current_mode == 'idle':
            return # No hacer nada si estamos inactivos

        # Incrementar el tiempo transcurrido basado en el intervalo del timer
        self.seconds_elapsed += UPDATE_INTERVAL_MS / 1000.0

        # Calcular y actualizar el valor de la barra de progreso (0-1000)
        progress_value = min(1000, int((self.seconds_elapsed / self.total_seconds_in_mode) * 1000))
        self.progressBar.setValue(progress_value)

        # --- Lógica para la alarma "soon" ---
        if self.current_mode == 'work' and not self.soon_alarm_played:
            remaining_seconds = self.total_seconds_in_mode - self.seconds_elapsed
            if remaining_seconds <= SOON_ALARM_THRESHOLD_MINUTES * 60:
                self.play_soon_alarm()
                self.soon_alarm_played = True # Marcar como ya reproducida

        # Comprobar si el intervalo actual ha terminado
        if self.seconds_elapsed >= self.total_seconds_in_mode:
            self.play_alarm() # Sonar la alarma

            now_hour = datetime.datetime.now().hour
            # Comprobar si hemos alcanzado la hora de finalización del día o si es hora de almuerzo
            if now_hour >= END_HOUR or (LUNCH_BREAK_START_HOUR <= now_hour < LUNCH_BREAK_END_HOUR):
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Hora de finalización ({END_HOUR}:00) o almuerzo ({LUNCH_BREAK_START_HOUR}-{LUNCH_BREAK_END_HOUR}). Pasando a modo inactivo.")
                self.switch_mode('idle') # Cambiar a modo inactivo
            # Cambiar al siguiente modo del ciclo Pomodoro
            elif self.current_mode == 'work':
                self.switch_mode('break')
            elif self.current_mode == 'break':
                self.switch_mode('work')

    def get_sound_path(self, relative_path):
        """Devuelve la ruta absoluta al archivo de sonido, manejando el caso del ejecutable."""
        if getattr(sys, 'frozen', False):
            # Estamos en un ejecutable empaquetado
            base_path = sys._MEIPASS
        else:
            # Estamos ejecutando el script directamente
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def play_alarm(self):
        """Reproduce el sonido de la alarma de fin de ciclo."""
        print(f">>> [{datetime.datetime.now().strftime('%H:%M:%S')}] ¡Alarma!")
        try:
            sound_file = self.get_sound_path(ALARM_SOUND_PATH)
            if os.path.exists(sound_file):
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                print(f"Advertencia: No se encontró el archivo de sonido en: {sound_file}")
                winsound.Beep(BEEP_FREQUENCY, BEEP_DURATION) # Fallback a Beep
        except Exception as e:
            print(f"Error al reproducir sonido: {e}")
            try:
                winsound.Beep(1000, 500)
            except Exception as e_beep:
                print(f"Error con Beep: {e_beep}")

    def play_soon_alarm(self):
        """Reproduce el sonido de aviso de que el tiempo de trabajo está por terminar."""
        print(f">>> [{datetime.datetime.now().strftime('%H:%M:%S')}] ¡Alarma pronto!")
        try:
            sound_file = self.get_sound_path(SOON_ALARM_PATH)
            if os.path.exists(sound_file):
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                print(f"Advertencia: No se encontró el archivo de sonido 'soon' en: {sound_file}")
                winsound.Beep(BEEP_FREQUENCY // 2, BEEP_DURATION) # Fallback a un pitido diferente
        except Exception as e:
            print(f"Error al reproducir sonido 'soon': {e}")
            try:
                winsound.Beep(800, 300)
            except Exception as e_beep:
                print(f"Error con Beep para 'soon': {e_beep}")


# --- Punto de Entrada Principal ---
if __name__ == '__main__':
    app = QApplication(sys.argv) # Crear la aplicación Qt
    pomodoro_bar = PomodoroBar() # Crear e inicializar nuestra barra Pomodoro
    sys.exit(app.exec()) # Iniciar el bucle de eventos de la aplicación Qt