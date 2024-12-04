# Utpl.RestApi
Proyecto para trabajar con Api en REST utilizando fastapi


## Descripción del Proyecto

**Este proyecto es una aplicación web construida utilizando FastAPI.** FastAPI es un framework de Python moderno, rápido y fácil de usar para crear APIs. Es ideal para construir aplicaciones web backend que necesitan ser eficientes y escalables.

**Caso de Estudio: API de Gestión para Come en Casa**

**Objetivos:**
Gestionar Catálogo de Almuerzos. Come en Casa busca modernizar su sistema de gestión, pasando de un proceso manual a un API eficiente para manejar clientes y pedidos. Este proyecto tiene como objetivo construir un API que permita gestionar un catálogo de almuerzos y manejar pedidos, con la posibilidad de futuras integraciones con sistemas de pago o notificaciones automáticas.

**Mas Información:** https://gamma.app/docs/Caso-de-Estudio-API-de-Gestion-para-Come-en-Casa-326k6uflo3hrek4

## Requisitos

* **Python:** Asegúrate de tener Python 3.6 o superior instalado.
* **FastAPI:** Instala FastAPI usando pip:
  ```bash
  pip install fastapi uvicorn

## Documentación 

## Ejecucion
Ejecute el siguiente comando para inicar la aplicacion
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
