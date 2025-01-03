# OrganAIzer
Proyecto final de la maestria en Inteligenia Artificial en UNIR Mexico.
Este proyecto busca identificar las cajas y sus volumenes basado en una imagen y generar un plan de organizacion en un contenedor.

# Integrantes
- Gabriel Ernesto Gutiérrez Añez
- Alicia Hernández Gutiérrez
- Guillermo Daniel González
- Lucia Alejandra Moreno Canuto

# Entrenamiento
Para realizar el entrenamiento se puee ejecutr el archivo `./training.sh` el cual creara un contenedor con Jupyter y Ultralytics.

# Ejecutar el proyecto.
Para levantar la aplicacion, se debe ejecutar el archivo `./run.sh`
Cualquier cambio generado en los archivos se vera reflejado automaticamente.

# Detener el proyecto o el entrenamiento.
Si NO se ejecuto en modo `deamon` se puede detener la apliacion utilizando `ctrl+c`
Si se ejecuto en modo `deamon` se puede deterner ejecutando `./stop.sh`

# URLs de los Servicios
- Interfaz de usuario: http://localhost:4200/
- API: http://localhost:5000/health-check
- Entrenamiento: http://localhost:8888?token=huAUCRkXiqW3JJW2QuyWjoJPCHY6lTWvkW5c5SbcXdx2hZEeFdQShrVOBK67QXP2