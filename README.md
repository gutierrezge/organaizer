# OrganAIzer
Proyecto final de la maestria en Inteligenia Artificial en UNIR Mexico.
Este proyecto busca identificar las cajas y sus volumenes basado en una imagen y generar un plan de organizacion en un contenedor.

# Integrantes
- Gabriel Ernesto Gutiérrez Añez
- Alicia Hernández Gutiérrez
- Guillermo Daniel González
- Lucia Alejandra Moreno Canuto

# Prerequisitos
Se requiere de al menos python 3.9.20 o superior y docker compose.
Instalar las dependencies de python en un ambiente de python

```
python3 -m venv venv
source venv/bin/activate
pip install pip -U
pip install -r requirements.txt
```

# Entrenamiento
Para realizar el entrenamiento ejecute el archiv `run.jupyter.sh`
Una vez iniciado jupyter, abra el notebook `02 YOLO Model Training.ipyn` y siga los pasos.

# Ejecutar la aplicacion.
Para levantar la aplicacion, se debe ejecutar el archivo `./run.sh`
Se levantara una base de datos de postgres y un navegador de la base de datos (pgAdmin), esto se hace mediante docker.

# URLs
- Entrenamiento: http://localhost:8888?tree