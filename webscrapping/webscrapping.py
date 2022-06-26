import time
from datetime import date, datetime
import pandas as pd
import numpy as np
import requests
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from io import StringIO
import boto3
import mibian


def main():

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1420,1080')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
    driver.get("https://www.meff.es/esp/Derivados-Financieros/Ficha/FIEM_MiniIbex_35")

    datos, futuros = get_opciones_futuros_df(driver)

    tabla_df = creacion_tabla_datos(datos, futuros)

    driver.close()
    tabla_df["volatilidad"] = tabla_df.apply(calcular_vola_implicita, axis = 1)

    bucket_name = "volatility-miax-8-practica-4-nacho-amo"
    escribir_s3(tabla_df, bucket_name)    



def get_opciones_futuros_df(driver):
    elementos_tr = driver.find_elements(By.CSS_SELECTOR, "#tblOpciones tbody tr")

    strikes = {}

    for elemento in elementos_tr:
        tipo = elemento.get_attribute("data-tipo")
        if tipo is None:
            continue
        if tipo not in strikes:
            strikes[tipo] = {
                "strikes": [],
                "ant": []
            }
        elemento_strike = elemento.find_element(By.CSS_SELECTOR, "td:nth-child(1)")
        strikes[tipo]["strikes"].append(elemento_strike.get_attribute('innerHTML'))
        elemento_ant = elemento.find_element(By.CSS_SELECTOR, "td:nth-last-child(1)")
        strikes[tipo]["ant"].append(elemento_ant.get_attribute('innerHTML'))

    elementos_tr = driver.find_elements(By.CSS_SELECTOR, "#Contenido_Contenido_tblFuturos tbody tr:not(.Total)")
    futuros = []
    for elemento in elementos_tr:
        elemento_fecha = elemento.find_element(By.CSS_SELECTOR, "td:nth-child(1)")
        elemento_ant = elemento.find_element(By.CSS_SELECTOR, "td:nth-last-child(1)")
        dict = {}
        dict["fecha_original"] = elemento_fecha.text
        dict["ant"] = float(elemento_ant.text.replace(".", "").replace(",", "."))
        componentes_fecha = elemento_fecha.text.split(" ")
        if componentes_fecha[1] == "ene.":
            mes = "01"
        elif componentes_fecha[1] == "feb.":
            mes = "02"
        elif componentes_fecha[1] == "mar.":
            mes = "03"
        elif componentes_fecha[1] == "abr.":
            mes = "04"
        elif componentes_fecha[1] == "may.":
            mes = "05"
        elif componentes_fecha[1] == "jun.":
            mes = "06"
        elif componentes_fecha[1] == "jul.":
            mes = "07"
        elif componentes_fecha[1] == "ago.":
            mes = "08"
        elif componentes_fecha[1] == "sep.":
            mes = "09"
        elif componentes_fecha[1] == "oct.":
            mes = "10"
        elif componentes_fecha[1] == "nov.":
            mes = "11"
        elif componentes_fecha[1] == "dic.":
            mes = "12"
        dict["fecha"] = f"{componentes_fecha[2]}-{mes}-{componentes_fecha[0]}"
        futuros.append(dict)

    datos = []
    for clave, valor in strikes.items():
        valores_strikes = [float(x.replace(".", "").replace(",", ".")) for x in valor["strikes"]]
        valores_ant = [0 if x == '- &nbsp;' else float(x.replace(".", "").replace(",", "."))  for x in valor["ant"]]
        tipo = "put" if clave[1] == 'P' else "call"
        annio = clave[3:7]
        mes= clave[7:9]
        dia = clave[9:]
        operacion = {
            "strikes": valores_strikes,
            "ant": valores_ant,
            "tipo": tipo,
            "fecha": {
                "annio": annio,
                "mes": mes,
                "dia": dia
            }
        }
        datos.append(operacion)
    return datos, futuros

def creacion_tabla_datos(datos, futuros):
    tabla_final = []
    hoy = date.today()
    hoy_string = str(hoy)
    hoy_datetime = datetime.strptime(hoy_string, "%Y-%m-%d")
    for dato in  datos:
        for strike, ant in zip(dato["strikes"], dato["ant"]):
            fecha = dato["fecha"]
            annio = fecha["annio"]
            mes = fecha["mes"]
            dia = fecha["dia"]
            tipo = dato["tipo"]
            fecha_dato = f"{annio}-{mes}-{dia}"
            futuro_ganador = futuros[0]
            for futuro in futuros:
                if futuro_ganador["fecha"] < futuro["fecha"] and fecha_dato > futuro["fecha"]:
                    futuro_ganador = futuro
            fecha_vencimiento_opciones = datetime.strptime(fecha_dato, "%Y-%m-%d")
            dias_a_vencimiento = fecha_vencimiento_opciones - hoy_datetime
            tabla_final.append([strike, ant, fecha_dato , tipo, futuro_ganador["fecha"], futuro_ganador["ant"], hoy_string, dias_a_vencimiento.days])
    tabla =  pd.DataFrame(tabla_final, columns = ["Strike", "Ant", "Venc_Opciones","Tipo_Opcion", "Fecha_Futuro", "Precio_Futuro", "Fecha Actual", "Dias_a_Vencimiento"])
    tabla = tabla[tabla["Dias_a_Vencimiento"] != 0]
    return tabla

def calcular_vola_implicita(fila):
    if fila["Tipo_Opcion"] == "call":
        return mibian.BS([fila["Precio_Futuro"], fila["Strike"],0,fila["Dias_a_Vencimiento"]], callPrice=fila["Ant"]).impliedVolatility
    else:
        return mibian.BS([fila["Precio_Futuro"], fila["Strike"],0,fila["Dias_a_Vencimiento"]], putPrice=fila["Ant"]).impliedVolatility


def escribir_s3(dataframe, bucket_name):
    hoy = datetime.today().strftime('%Y-%m-%d')
    csv_buffer = StringIO()
    dataframe.to_csv(csv_buffer)
    s3_resource = boto3.resource('s3')
    s3_resource.Object(bucket_name, f'tabla.csv').put(Body=csv_buffer.getvalue())

main()
