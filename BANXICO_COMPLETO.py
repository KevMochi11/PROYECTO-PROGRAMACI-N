
'''
Autor: Kevin Uziel Martínez Corral
Objetivo:
Consultar Banxico en tiempo real y calcular interés simple usando
la tasa de CETES a 28 días. También genera un reporte y puede
enviarlo por correo electrónico.
'''

import os
import requests
import time as t
from smtplib import SMTP
from email.message import EmailMessage
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

TOKEN = os.getenv('TOKEN')
HOSTMAIL = os.getenv('HOSTMAIL')
USERMAIL = os.getenv('USERMAIL')
PASSWORD = os.getenv('PASSWORD')
PORTMAIL = os.getenv('PORTMAIL')


def consultar_serie(serie):
    '''Consulta el último dato disponible de una serie de Banxico.'''

    try:

        if not TOKEN:
            print('No se encontró el TOKEN de Banxico en el archivo .env')
            return None

        enlace = f'https://www.banxico.org.mx/SieAPIRest/service/v1/series/{serie}/datos/oportuno'

        headers = {'Bmx-Token': TOKEN}

        response = requests.get(enlace, headers=headers, timeout=10)

        print('Status de Banxico:', response.status_code)
        response.raise_for_status()

        datos = response.json()
        serie_datos = datos['bmx']['series'][0]
        titulo = serie_datos.get('titulo', serie)
        dato = serie_datos['datos'][0]
        fecha = dato['fecha']
        valor = dato['dato'].replace(',', '')

        return titulo, fecha, float(valor)

    except requests.exceptions.RequestException as error:
        print('Error de conexión con Banxico:', error)
        return None

    except (KeyError, ValueError, IndexError) as error:
        print('No se pudo leer la respuesta de Banxico:', error)
        return None


def BanxicoDollar():

    serie = 'SP74665'
    resultado = consultar_serie(serie)

    if resultado is not None:
        titulo, fecha, valor = resultado

        print('\n--- CONSULTA BANXICO ---')
        print('Serie:', serie)
        print('Descripción:', titulo)
        print('Fecha:', fecha)
        print('Valor:', valor)


def obtener_cetes_28():

    serie = 'SF43936'
    resultado = consultar_serie(serie)

    if resultado is None:
        return None

    titulo, fecha, tasa = resultado

    print('\nTasa CETES 28 días:', tasa, '%')
    print('Fecha de la tasa:', fecha)

    return titulo, fecha, tasa


def calcular_interes_simple(capital, tasa, dias):

    interes = capital * (tasa / 100) * (dias / 360)
    monto = capital + interes

    return interes, monto


def generar_reporte(capital, tasa, dias, interes, monto, fecha_tasa):

    nombre = 'reporte_interes_simple.txt'

    reporte = (
        'REPORTE DE INTERÉS SIMPLE CON CETES A 28 DÍAS\n'
        '------------------------------------------------\n'
        f'Fecha del reporte: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\n'
        f'Fecha de la tasa Banxico: {fecha_tasa}\n'
        f'Capital: ${capital:,.2f}\n'
        f'Tasa CETES 28 días: {tasa:.4f}% anual\n'
        f'Tiempo: {dias} días\n'
        f'Interés simple: ${interes:,.2f}\n'
        f'Monto final: ${monto:,.2f}\n'
        '\nFórmula: I = C * i * t\n'
        'Donde la tasa se convierte a decimal y el tiempo a días/360.\n'
    )

    with open(nombre, 'w', encoding='utf-8') as archivo:
        archivo.write(reporte)

    print('\nReporte generado:', nombre)

    return nombre


def enviar_email(archivo):

    try:

        if not HOSTMAIL or not USERMAIL or not PASSWORD or not PORTMAIL:
            print('Correo no enviado.')
            print('Faltan datos en el archivo .env')
            return

        destino = input('\nIngresa el correo al que deseas enviar el reporte: ').strip()

        if destino == '':
            print('No escribiste ningún correo.')
            return

        mensaje = EmailMessage()

        mensaje['Subject'] = 'Reporte de interés simple con CETES'
        mensaje['From'] = USERMAIL
        mensaje['To'] = destino

        mensaje.set_content(
            'Se adjunta el reporte del cálculo de interés simple.'
        )

        with open(archivo, 'rb') as adjunto:

            mensaje.add_attachment(
                adjunto.read(),
                maintype='text',
                subtype='plain',
                filename=archivo
            )

        puerto = int(PORTMAIL)

        with SMTP(HOSTMAIL, puerto) as servidor:

            servidor.starttls()
            servidor.login(USERMAIL, PASSWORD)
            servidor.send_message(mensaje)

        print('\nCorreo enviado correctamente.')
        print('Reporte enviado a:', destino)

    except Exception as error:

        print('No se pudo enviar el correo.')
        print('Error:', error)


def resolver_interes_simple():

    resultado = obtener_cetes_28()

    if resultado is None:
        return

    titulo, fecha_tasa, tasa = resultado

    try:

        capital = float(input('Ingresa el capital a invertir: $'))
        dias = int(input('Ingresa el tiempo en días: '))

        if capital <= 0 or dias <= 0:

            print('El capital y los días deben ser mayores que cero.')
            return

        interes, monto = calcular_interes_simple(capital, tasa, dias)

        print('\n--- RESULTADO ---')
        print('Capital:', f'${capital:,.2f}')
        print('Tasa anual:', f'{tasa:.4f}%')
        print('Tiempo:', dias, 'días')
        print('Interés:', f'${interes:,.2f}')
        print('Monto final:', f'${monto:,.2f}')

        archivo = generar_reporte(
            capital,
            tasa,
            dias,
            interes,
            monto,
            fecha_tasa
        )

        enviar_email(archivo)

    except ValueError:
        print('Error: escribe solamente números para capital y días.')


def menu():

    while True:

        print('\n===============================')
        print('        PROGRAMA BANXICO')
        print('===============================')
        print('1. Consultar Banxico en tiempo real')
        print('2. Calcular interés simple con CETES 28 días')
        print('3. Salir')

        opcion = input('Selecciona una opción: ')

        if opcion == '1':
            BanxicoDollar()

        elif opcion == '2':
            resolver_interes_simple()

        elif opcion == '3':
            print('Saliendo del programa en 5 segundos...')
            t.sleep(5)
            print('Programa finalizado.')
            break

        else:
            print('Opción no válida. Intenta de nuevo.')


if __name__ == '__main__':

    menu()