# MiPomodoroApp

## Introducción

MiPomodoroApp es una aplicación de gestión de tiempo basada en la técnica Pomodoro, diseñada para mejorar la productividad mediante ciclos de trabajo y descanso. La aplicación muestra una discreta barra de progreso en la parte superior de la pantalla que indica visualmente el tiempo restante del ciclo actual.

## Características Principales

- **Ciclos Pomodoro Automáticos**: Alterna automáticamente entre períodos de trabajo (50 minutos) y descanso (10 minutos).
- **Barra de Progreso Minimalista**: Una barra delgada en la parte superior de la pantalla que cambia de color según el modo:
  - Naranja durante el tiempo de trabajo
  - Verde claro durante los descansos
  - Gris claro cuando está inactiva
- **Horario Configurable**: 
  - Inicia automáticamente a las 7:00 AM
  - Finaliza a las 5:00 PM
  - Pausa para almuerzo entre las 11:00 AM y 1:00 PM
- **Notificaciones Sonoras**:
  - Alarma al finalizar cada ciclo
  - Aviso 5 minutos antes de que termine el tiempo de trabajo
- **Siempre Visible**: La barra permanece siempre en primer plano, sin interferir con otras aplicaciones.

## Requisitos

- Sistema operativo Windows
- Python 3.6 o superior
- Dependencias:
  - PyQt6
  - schedule

## Instalación

1. Clona o descarga este repositorio.
2. Instala las dependencias necesarias:

```bash
pip install PyQt6 schedule
```

3. Asegúrate de que la carpeta `sounds` con los archivos de sonido (`alarm.wav` y `soon.wav`) esté en el mismo directorio que el script.

## Uso

Para iniciar la aplicación, simplemente ejecuta:

```bash
python pomodoro_app.py
```

La aplicación iniciará automáticamente y mostrará una barra delgada en la parte superior de la pantalla. No es necesario realizar ninguna acción adicional, ya que la aplicación gestionará automáticamente los ciclos de trabajo y descanso según el horario configurado.

## Configuración Personalizada

Puedes personalizar varios aspectos de la aplicación modificando las constantes al inicio del archivo `pomodoro_app.py`:

### Tiempos y Horarios

```python
WORK_MINUTES = 50  # Duración del trabajo en minutos
BREAK_MINUTES = 10  # Duración del descanso en minutos
START_TIME_STR = "07:00"  # Hora de inicio HH:MM (24h)
END_HOUR = 17  # Hora (24h) después de la cual ya no se inician más ciclos (5 PM)
SOON_ALARM_THRESHOLD_MINUTES = 5  # Minutos antes de que suene la alarma "soon"
LUNCH_BREAK_START_HOUR = 11  # Hora de inicio del almuerzo (24h)
LUNCH_BREAK_END_HOUR = 13  # Hora de fin del almuerzo (24h)
```

### Apariencia de la Barra

```python
BAR_HEIGHT = 2  # Altura de la barra en píxeles
WORK_COLOR = "orange"  # Color de la barra en trabajo
BREAK_COLOR = "lightgreen"  # Color de la barra en descanso
IDLE_COLOR = "lightgray"  # Color cuando no está en ciclo Pomodoro
```

### Sonidos

```python
ALARM_SOUND_PATH = "sounds/alarm.wav"  # Ruta al archivo de sonido de fin de ciclo
SOON_ALARM_PATH = "sounds/soon.wav"  # Ruta al archivo de sonido de aviso de fin de ciclo
BEEP_FREQUENCY = 1500  # Hz (para el pitido de respaldo)
BEEP_DURATION = 500  # ms (duración del pitido de respaldo)
```

## Funcionamiento Interno

La aplicación utiliza PyQt6 para crear una interfaz gráfica minimalista y la biblioteca `schedule` para gestionar los horarios. El flujo de funcionamiento es el siguiente:

1. Al iniciar, la aplicación programa el inicio del primer ciclo Pomodoro a la hora especificada (por defecto 7:00 AM).
2. Verifica periódicamente si debe iniciar, pausar o reanudar los ciclos según la hora actual.
3. Durante un ciclo activo, la barra de progreso se actualiza continuamente para mostrar el tiempo restante.
4. Al finalizar cada ciclo, suena una alarma y se cambia automáticamente al siguiente modo (trabajo o descanso).
5. Durante el horario de almuerzo, la aplicación pausa los ciclos y muestra la barra en modo inactivo.
6. Después de la hora de finalización (por defecto 5:00 PM), no se inician nuevos ciclos.

## Solución de Problemas

### No se reproducen los sonidos

- Verifica que los archivos de sonido (`alarm.wav` y `soon.wav`) estén en la carpeta `sounds` en el mismo directorio que el script.
- Asegúrate de que tu sistema tenga habilitado el sonido y que los altavoces estén funcionando correctamente.

### La barra no aparece

- Asegúrate de que no haya otro programa que esté ocupando la parte superior de la pantalla.
- Verifica que PyQt6 esté instalado correctamente.

### La aplicación no inicia los ciclos automáticamente

- Comprueba que la hora del sistema sea correcta.
- Verifica que las constantes de tiempo (`START_TIME_STR`, `END_HOUR`, etc.) estén configuradas según tus necesidades.

## Licencia

Este proyecto está disponible como software de código abierto.
