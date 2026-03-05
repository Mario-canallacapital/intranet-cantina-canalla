# --- VERSIÓN v42.0 (CORPORATE SIDEBAR EDITION) ---
# Actualizado: 05/03/2026 
# Novedades: Retorno al menú lateral robusto, botón hamburguesa destacado, botón de recarga interna.

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import uuid
import re
import requests
import base64
from io import BytesIO
from PIL import Image
import smtplib
import random
import traceback
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Intranet Cantina Canalla", layout="wide", page_icon="🌮")

# --- CONFIGURACIÓN CORREO ---
EMAIL_GENERICO = "avisosapp.cantinacanalla@gmail.com" 
PASS_GENERICA = "pvyglchitjtupzoz" 

# --- LÓGICA AUTOMÁTICA DEL MES (QUIZ) ---
meses_espanol = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
hoy = datetime.now()
MES_ACTUAL_QUIZ = f"{meses_espanol[hoy.month - 1]} {hoy.year}"

# --- GRAN BANCO DE PREGUNTAS: SALA ---
POOL_SALA = {
    "1. ¿De qué color debe ser el calzado de trabajo en Sala?": (["Blanco o negro completo", "Marrón o gris", "Libre elección mientras sea cerrado"], 0),
    "2. ¿Se puede circular por el local con ropa de calle?": (["Sí, siempre", "No, excepto en el trayecto al vestuario", "Solo si no hay clientes"], 1),
    "3. ¿Está permitido salir a la calle con la ropa de trabajo?": (["Sí, a zonas cercanas", "No, en ningún caso", "Solo en descansos"], 1),
    "4. ¿Cómo deben mantenerse las taquillas personales?": (["En perfecto estado de higiene y sin acumular ropa sucia", "Se pueden compartir", "Pueden tener ropa sucia temporalmente"], 0),
    "5. ¿Cómo se debe lavar la indumentaria de trabajo?": (["Con agua fría", "Con agua caliente asegurando higienización", "A mano siempre"], 1),
    "6. ¿Qué indica la norma sobre la barba y el pelo corporal?": (["Prohibida barba larga o pelo corporal que ocasione mala imagen", "Se permite cualquier estilo", "Solo se permite perilla"], 0),
    "7. ¿Cómo deben llevarse las uñas durante el servicio?": (["Largas y pintadas", "Cortas, sin lacas o barniz y limpias", "Solo con esmalte transparente"], 1),
    "8. ¿Está permitido el uso excesivo de joyas?": (["Sí, no hay problema", "No, si interfieren con el servicio", "Solo pulseras"], 1),
    "9. Sobre el uso de perfumes en sala, la norma dice:": (["Hay que usar perfumes fuertes", "Evitar perfumes fuertes que molesten a clientes", "No está regulado"], 1),
    "10. ¿A qué distancia mínima del local se puede fumar?": (["10 metros", "30 metros", "50 metros"], 1),
    "11. Es obligatorio lavarse las manos frecuentemente, especialmente...": (["Solo al entrar", "Solo tras ir al baño", "Tras usar el aseo, fumar, comer o tocarse la nariz"], 2),
    "12. ¿Cuál es la norma sobre el uso de motes o apelativos entre compañeros?": (["Están prohibidos, se usa el nombre", "Se permiten si hay confianza", "Solo en descansos"], 0),
    "13. Discriminar a alguien por raza, sexo o religión es...": (["Motivo de denuncia personándose la empresa como acusación", "Falta leve", "Una advertencia verbal"], 0),
    "14. Si un compañero incumple una norma, ¿qué se debe hacer?": (["Ignorarlo", "Ponerlo en conocimiento del superior para no ser cómplice", "Reírle la gracia"], 1),
    "15. ¿Dónde debe guardarse el teléfono móvil personal?": (["En el bolsillo del delantal", "En las taquillas, prohibido en horario laboral", "En la barra"], 1),
    "16. ¿Qué marca la hora de entrada al trabajo?": (["Cruzar la puerta del local", "Estar uniformado y preparado en el puesto", "Fichar en el sistema"], 1),
    "17. ¿Computa el tiempo de cambio de uniforme como horario laboral?": (["Sí, siempre", "No se computa", "Solo la salida"], 1),
    "18. ¿Por qué es obligatorio conocer el menú y sus ingredientes?": (["Para evitar alergias únicamente", "Para brindar mejor atención, información y sugerencias", "No es obligatorio"], 1),
    "19. Si hay vasos o botellas vacías en la mesa, ¿qué se debe hacer?": (["Esperar a que el cliente avise", "Nunca tenerlos vacíos, retirarlos y ofrecer bebida", "Retirarlos al final de la cena"], 1),
    "20. Al llevar un plato a la mesa es obligatorio...": (["Dejarlo en silencio", "Anunciarlo y decir sus características generales", "Preguntar quién lo pidió"], 1),
    "21. En la recepción de clientes, ¿qué es lo primero que se pregunta tras saludar?": (["¿Tienen reserva?", "¿Van a comer o cenar?", "¿Quieren terraza?"], 0),
    "22. En el procedimiento del aperitivo, si toman alcohol se les ofrece...": (["Chupito de tequila", "Margarita Frozen", "Cerveza"], 1),
    "23. El aperitivo sin alcohol consiste en una mezcla tipo San Francisco con...": (["Zumo de piña y melocotón", "Naranja, limón y granadina", "Agua con gas"], 1),
    "24. ¿Qué botón se usa en el TPV para registrar el aperitivo y a qué precio?": (["Chupito Aperitivo, 0€", "Invitación, 0€", "Margarita Mini, 1€"], 0),
    "25. Al retirar los segundos platos, ¿qué se debe ofrecer?": (["La cuenta", "Postres caseros, margaritas o tequila", "Cafés únicamente"], 1),
    "26. ¿Qué se entrega al cliente junto a la cuenta para que deje una valoración?": (["Una tarjeta", "El totem", "El datáfono"], 1),
    "27. Al salir el cliente del local, ¿qué procedimiento se sigue?": (["Decir adiós desde la barra", "Acompañarlos a la puerta y abrirla", "Ignorar la salida"], 1),
    "28. En la apertura de turno, ¿cuál es el primer paso?": (["Encender cafetera", "Encender el cuadro de luces de barra y sala", "Purgar barriles"], 1),
    "29. Antes de iniciar el servicio de bebidas en apertura, hay que...": (["Lavar vasos", "Purgar inicialmente los barriles de cerveza", "Cambiar barriles"], 1),
    "30. En la receta de la Margarita para granizar, ¿cuánto zumo de limón lleva?": (["1 litro", "1,500 litros", "2 litros"], 1),
    "31. En la receta de la Margarita para granizar, ¿cuánto tequila se añade?": (["1 botella", "2 botellas de 70cl de José Cuervo", "3 botellas"], 1),
    "32. Si al revisar la sala hay una bombilla fundida, se debe...": (["Dejarla así", "Reponerla", "Avisar al día siguiente"], 1),
    "33. En el traspaso de turno, se debe comprobar el funcionamiento de...": (["La TPV únicamente", "Máquina de café, hielo y grifo de cerveza", "Las luces de la calle"], 1),
    "34. Durante el traspaso, ¿qué comunicación debe existir con el siguiente compañero?": (["Ninguna", "Comunicar temas y puntos relevantes del día", "Solo la caja"], 1),
    "35. En el cierre de turno, ¿qué se debe hacer con las plataformas de delivery?": (["Dejarlas encendidas", "Asegurarse de que quedan apagadas", "Reiniciarlas"], 1),
    "36. Es obligatorio realizar los ___ proporcionados por la empresa para controlar tareas.": (["Tickets de caja", "Checklist operativos", "Inventarios diarios"], 1),
    "37. ¿A qué temperatura se recepcionan los productos refrigerados?": (["0-6 ºC", "2-8 ºC", "-2 a 4 ºC"], 0),
    "38. ¿Cómo se mide la temperatura en la recepción de mercancías?": (["Con láser", "Colocando el termómetro entre dos envases", "A ojo"], 1),
    "39. El almacenamiento de materias primas sigue el sistema...": (["LIFO", "Alfabético", "FIFO (lo más antiguo primero)"], 2),
    "40. ¿Sobre qué elementos se deben almacenar los productos para aislarlos del suelo?": (["Cajas de cartón", "Pallets o estanterías", "Mantas"], 1),
    "41. La temperatura de las cámaras de refrigeración debe ser inferior a...": (["4 ºC", "8 ºC", "0 ºC"], 0),
    "42. La temperatura de las cámaras de congelación debe estar en torno a...": (["-10 ºC", "-18 ºC", "-24 ºC"], 1),
    "43. El tiempo correcto de descongelación en cámara de refrigeración es...": (["12-24 horas", "24-48 horas", "48-72 horas"], 1),
    "44. Para descongelar en microondas se debe hacer...": (["De una vez a máxima potencia", "En 2 o 3 fases, y consumir o cocinar inmediatamente", "Con la función grill"], 1),
    "45. Si se descongela bajo inmersión en agua fría, el alimento debe...": (["Estar en un envoltorio o bolsa estanca", "Estar en contacto directo con el agua", "Hervirse antes"], 0),
    "46. ¿Se puede recongelar un producto descongelado?": (["Sí, si no huele mal", "Bajo ningún concepto", "Solo si es carne"], 1),
    "47. Para desinfectar hortalizas de consumo en crudo se utiliza...": (["Jabón", "Vinagre", "Lejía de uso alimentario"], 2),
    "48. Si una lata de conserva tiene el fondo convexo (hacia fuera), se debe...": (["Desechar de inmediato", "Hervir", "Abrir con cuidado"], 0),
    "49. Si el envase original abierto no es adecuado, el producto se trasvasa a...": (["Plástico o acero inoxidable con tapa", "Cristal", "Cartón"], 0),
    "50. La caducidad secundaria máxima de los fiambres es de...": (["3 días", "5 días", "7 días"], 1),
    "51. La caducidad secundaria máxima de los embutidos curados es de...": (["5 días", "10 días", "15 días"], 2),
    "52. Los productos frescos que congelamos caducan al...": (["Mes desde su congelación", "3 meses", "1 semana"], 0),
    "53. Los productos de limpieza se deben almacenar...": (["En el suelo", "En su armario correspondiente, nunca en el suelo", "En las cámaras frías"], 1),
    "54. Es obligatorio que todos los cubos de basura tengan...": (["Bolsa doble", "Tapa y pedal", "Ruedas"], 1),
    "55. ¿Cómo deben almacenarse las tazas, jarras y vasos limpios?": (["Boca arriba", "Apilados de 3 en 3", "Boca abajo"], 2),
    "56. ¿Cómo deben guardarse los biberones no utilizados?": (["Abiertos", "Con su tapón o film de plástico", "Volcados"], 1),
    "57. ¿A partir de qué peso se considera manipulación manual de cargas?": (["1 Kg", "3 Kg", "5 Kg"], 1),
    "58. Al transportar una bandeja, el peso debe apoyarse en...": (["La muñeca", "Los dedos", "La mano y el antebrazo"], 2),
    "59. Al llevar platos, los codos deben estar...": (["Estirados", "Cerca del cuerpo para disminuir tensión", "A la altura de los hombros"], 1),
    "60. Al manipular cargas bajas (desde el suelo) se deben...": (["Mantener piernas rectas", "Doblar las rodillas en lugar de usar la espalda", "Girar la cadera"], 1)
}

# --- GRAN BANCO DE PREGUNTAS: COCINA ---
POOL_COCINA = {
    "1. La indumentaria obligatoria de cocina consta de camiseta/casaca de color...": (["Blanca", "Negra", "Gris"], 1),
    "2. En cocina, ¿qué tipo de guantes son obligatorios?": (["Látex", "Vinilo", "Nitrilo"], 2),
    "3. ¿Se puede circular por las instalaciones con la ropa de calle?": (["Sí", "Solo hasta el vestuario", "Solo fuera de servicio"], 1),
    "4. ¿Cómo deben lavarse los uniformes para asegurar su higienización?": (["Con agua fría", "Con agua caliente", "Solo limpieza en seco"], 1),
    "5. Las uñas en cocina deben estar...": (["Largas y limpias", "Cortas, limpias y sin laca", "Pintadas de transparente"], 1),
    "6. La distancia mínima permitida para fumar respecto al local es de...": (["10 metros", "20 metros", "30 metros"], 2),
    "7. ¿Cuándo es obligatorio lavarse las manos en cocina?": (["Solo al entrar", "Antes del servicio, tras ir al aseo, comer, fumar o tocar residuos", "Al final del turno"], 1),
    "8. El trato vejatorio u ofensivo a un compañero es...": (["Prohibido bajo cualquier justificación", "Falta leve", "Tolerado en estrés"], 0),
    "9. ¿Dónde debe permanecer el teléfono móvil durante el horario laboral?": (["En la mesa de trabajo", "En las taquillas (prohibido su uso)", "En el bolsillo"], 1),
    "10. La hora de salida se establece estando...": (["Ya vestido de calle", "Trabajando uniformado hasta la hora exacta estipulada", "Al limpiar la plancha"], 1),
    "11. ¿Computa el tiempo de cambio de uniforme como horario laboral?": (["Sí", "No", "Depende del turno"], 1),
    "12. Una competencia primordial en cocina es aplicar las normas para prevenir...": (["Accidentes por corte", "La contaminación cruzada", "Quemaduras graves"], 1),
    "13. Es vital entender las fichas técnicas de los platos, que son...": (["Los horarios", "Las recetas", "Los manuales de limpieza"], 1),
    "14. Tareas de apertura: ¿Cuáles son las tres primeras cosas en encenderse?": (["Gas, Campana, Baño María", "Plancha, Freidora, Microondas", "Fogones, Lavavajillas, Luces"], 0),
    "15. En apertura, ¿cuánto arroz suele prepararse?": (["500 g", "1 Kg", "2 Kg"], 1),
    "16. ¿Qué ingredientes se deben reponer en la vitrina fría?": (["Solo salsas", "Lechuga y tomate", "Guacamole, pico, cebolla morada, queso, jalapeño, mix de verduras"], 2),
    "17. ¿Cuántas bolsas de sopa se preparan para el menú de lunes a viernes en planchas?": (["1-2 bolsas", "3-4 bolsas", "5-6 bolsas"], 1),
    "18. En apertura, ¿cuántos paquetes de tortillas de 13 se preparan?": (["5", "10", "16 paquetes (Nevera de plancha)"], 2),
    "19. En apertura, ¿cuántas cajas de nachos deben prepararse en zona fría?": (["1 caja", "2 cajas", "4 cajas"], 2),
    "20. En reservas de cámara, siempre debe haber descongelando X kilos de ternera...": (["2 Kg", "4 Kg", "6 Kg"], 1),
    "21. En reservas de cámara, ¿cuántos bloques de bacon debe haber descongelando?": (["1 bloque", "2 bloques", "3 bloques"], 2),
    "22. En reservas, debe haber un túper preparado y picado de...": (["Tomate y lechuga", "Piña, bacón y carnitas", "Cebolla y cilantro"], 1),
    "23. En el turno de guardia, lo primero en apagarse es...": (["El gas y los fogones", "El baño maría, plancha y fogones", "La freidora"], 1),
    "24. En el turno de guardia se repone el arroz con la cantidad de...": (["500 g", "1 Kg", "2 Kg"], 1),
    "25. En el cierre, ¿qué se hace con los biberones utilizados?": (["Se tiran", "Se quitan tapas, se lavan y se vuelven a tapar", "Se guardan abiertos"], 1),
    "26. En el cierre de cocina, ¿cada cuántos días se cambia el agua del baño maría?": (["Diario", "Cada dos días", "Semanal"], 1),
    "27. ¿Con qué frecuencia se realiza la limpieza de la campana en el cierre?": (["Diaria", "De manera semanal", "Mensual"], 1),
    "28. Los vehículos de proveedores refrigerados deben transportar la mercancía a...": (["-2 a 2 ºC", "0 a 6 ºC", "4 a 10 ºC"], 1),
    "29. Al descargar materias primas para evitar la rotura de cadena de frío se debe...": (["Esperar a finalizar el servicio", "Trasladarlas inmediatamente a sus cámaras", "Dejarlas en el suelo"], 1),
    "30. En recepción de mercancía, el termómetro para la medición se coloca...": (["Dentro del producto siempre", "Entre dos envases", "Sobre la caja"], 1),
    "31. El almacenamiento de materias primas usa el sistema FIFO, que significa...": (["First in, first out (lo más antiguo se usa primero)", "Ordenar por alfabeto", "Ordenar por proveedor"], 0),
    "32. ¿Sobre qué elemento NO se pueden almacenar productos?": (["Estanterías", "Directamente sobre el suelo", "Pallets"], 1),
    "33. La temperatura de las cámaras de refrigeración debe ser inferior a...": (["0 ºC", "4 ºC", "8 ºC"], 1),
    "34. La temperatura de las cámaras de congelación debe ser entorno a...": (["-10 ºC", "-18 ºC", "-24 ºC"], 1),
    "35. El tiempo correcto de descongelación en cámara de refrigeración es...": (["12-24 horas", "24-48 horas", "48-72 horas"], 1),
    "36. Descongelación en microondas: se debe hacer en fases y después...": (["Consumir o cocinar inmediatamente", "Volver a guardar en nevera", "Dejar reposar 1h"], 0),
    "37. Para la descongelación por inmersión (chorro de agua fría), el producto debe...": (["Estar en contacto con el agua", "Tener un envoltorio o bolsa de plástico estanca", "Ser carne cruda"], 1),
    "38. ¿Qué práctica de descongelación está totalmente prohibida?": (["En microondas", "A temperatura ambiente o inmersión en agua caliente", "En cámara a 4ºC"], 1),
    "39. Para desinfectar frutas y hortalizas de consumo en crudo se utiliza...": (["Agua caliente", "Vinagre", "Lejía de uso alimentario"], 2),
    "40. Si el fondo de una lata de conserva tiene forma convexa (hacia fuera)...": (["Se desecha", "Se perfora para sacar el aire", "Se usa primero"], 0),
    "41. Si el recipiente original no es válido tras abrirlo, se trasvasa a...": (["Caja de cartón", "Material apto plástico o acero inoxidable con tapa", "Cristal"], 1),
    "42. La caducidad secundaria de fiambres es máximo...": (["3 días", "5 días", "7 días"], 1),
    "43. La caducidad secundaria de embutidos curados es máximo...": (["10 días", "15 días", "20 días"], 1),
    "44. Para las materias primas que congelamos nosotros, la caducidad máxima es de...": (["1 semana", "1 mes", "3 meses"], 1),
    "45. Los utensilios y productos de limpieza deben almacenarse...": (["Bajo la pica sin importar si tocan suelo", "En su armario, nunca en el suelo", "Junto a basuras"], 1),
    "46. ¿Se pueden mantener tuppers sin tapa temporalmente en cocina?": (["Sí", "No, está prohibido proteger mal el interior", "Solo en servicio"], 1),
    "47. Los cubos de basura deben tener obligatoriamente...": (["Doble bolsa", "Tapa y pedal", "Ruedas"], 1),
    "48. Todo el material fresco cortado o abierto tiene que estar tapado e identificado con...": (["Nombre del cocinero", "Fecha de apertura/tratamiento y fecha de caducidad", "Alérgenos"], 1),
    "49. Si se detecta que una temperatura de nevera no está en rango, es obligatorio...": (["Abrir incidencia y avisar a superiores", "Apagarla", "Tirar la comida"], 0),
    "50. Los palos de fregona y escobas en cocina deben estar...": (["Apoyados en la pared", "Colgados de forma correcta con colgadores", "Tumbados"], 1),
    "51. ¿Qué se debe hacer si detectamos bandejas de madera astilladas o quemadas?": (["Usarlas igual", "Avisar a los supervisores porque está prohibido", "Forrarlas con film"], 1),
    "52. Almacenar productos alimenticios sobre neveras o congeladores está...": (["Permitido por espacio", "Totalmente prohibido", "Solo permitido al cierre"], 1),
    "53. Cualquier carga transportada o empujada en cocina se considera manipulación manual a partir de...": (["1 Kg", "3 Kg", "5 Kg"], 1),
    "54. Las principales consecuencias de una mala manipulación manual de cargas en cocina son...": (["Cortes", "Lumbalgias", "Quemaduras"], 1),
    "55. El manejo de cargas superior a ___ Kg entraña riesgo y debe pedirse ayuda.": (["15 Kg", "20 Kg", "25 Kg"], 2),
    "56. Se aconseja colocar las ollas de mayor peso en...": (["Fogones lejanos", "Los fogones más cercanos al trabajador para evitar alcances", "El suelo"], 1),
    "57. En los estantes medios (altura caderas/pecho) del almacén se deben colocar...": (["Alimentos pesados de uso frecuente", "Alimentos ligeros", "Alimentos pesados infrecuentes"], 0),
    "58. En los estantes de menor altura (suelo) del almacén se deben colocar...": (["Lo más usado", "Alimentos pesados de uso infrecuente", "Latas ligeras"], 1),
    "59. Acumular más de tres faltas injustificadas de puntualidad en un mes es...": (["Falta leve", "Falta grave", "Falta muy grave"], 1),
    "60. Faltar uno o dos días al trabajo en treinta días sin justificación es...": (["Falta leve", "Falta grave", "Falta muy grave"], 1)
}

# --- GENERADOR AUTOMÁTICO DE PREGUNTAS ---
random.seed(MES_ACTUAL_QUIZ)
if len(POOL_SALA) >= 20:
    QUIZ_SALA = {k: POOL_SALA[k] for k in random.sample(list(POOL_SALA.keys()), 20)}
else:
    QUIZ_SALA = POOL_SALA

if len(POOL_COCINA) >= 20:
    QUIZ_COCINA = {k: POOL_COCINA[k] for k in random.sample(list(POOL_COCINA.keys()), 20)}
else:
    QUIZ_COCINA = POOL_COCINA
random.seed()

# --- FUNCIONES BASE ---
def cargar_logo_base64():
    try:
        with open("armband-PhotoRoom.png-PhotoRoom.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: return None

def comprimir_foto(upload_file):
    img = Image.open(upload_file)
    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
    img.thumbnail((400, 400))
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=30)
    return f"data:image/jpeg;base64,{base64.b64encode(buffer.getvalue()).decode()}"

def comparten_sede(s1, s2):
    if pd.isna(s1) or pd.isna(s2): return False
    l1 = set(x.strip() for x in str(s1).split(',') if x.strip())
    l2 = set(x.strip() for x in str(s2).split(',') if x.strip())
    return not l1.isdisjoint(l2)

def extraer_id_drive(url):
    if not isinstance(url, str) or pd.isna(url): return None
    match = re.search(r'[-\w]{25,}', url)
    return match.group(0) if match else None

def procesar_img_drive(url):
    fid = extraer_id_drive(url)
    if not fid: return None
    return f"https://lh3.googleusercontent.com/d/{fid}"

def enviar_aviso_email(destinatario, asunto, cuerpo):
    try:
        msg = MIMEMultipart()
        msg['From'] = f"Intranet Cantina Canalla <{EMAIL_GENERICO}>"
        msg['To'] = destinatario
        msg['Subject'] = asunto
        msg.attach(MIMEText(cuerpo, 'plain'))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_GENERICO, PASS_GENERICA)
        server.sendmail(EMAIL_GENERICO, destinatario, msg.as_string())
        server.quit()
        return True
    except: return False

def reportar_error_a_mario(e):
    error_detallado = traceback.format_exc()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = st.session_state.get('user', {}).get('Nombre_Apellidos', 'N/A')
    cuerpo = f"🚨 ERROR v42.0 🚨\n\nFecha: {ahora}\nUsuario: {user}\n\nTraceback:\n{error_detallado}"
    enviar_aviso_email("mario@canallacapital.com", "🚨 ERROR APP CANTINA", cuerpo)

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)
def load(p, ttl=5):
    for i in range(3):
        try: return conn.read(worksheet=p, ttl=ttl)
        except Exception as e:
            if i == 2: raise e
            time.sleep(2)

# --- VARIABLES DE SESIÓN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'page' not in st.session_state: st.session_state.page = "login"

# --- BLOQUE PRINCIPAL DE LA APP ---
try:
    # --- 🎨 CSS: ESTILO CANALLA (DARK & RED) Y FIX DEL BOTÓN MÓVIL ---
    st.markdown("""
        <style>
        /* 1. Fondo oscuro corporativo */
        .stApp { background-color: #0A0A0A !important; color: #FFFFFF !important; }
        [data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #333; }
        
        /* 2. SUPER BOTÓN HAMBURGUESA FLOTANTE PARA MÓVIL */
        [data-testid="collapsedControl"] {
            background-color: #E63946 !important; /* Rojo vivo */
            color: #FFFFFF !important;
            border-radius: 8px !important;
            padding: 8px !important;
            box-shadow: 0px 4px 10px rgba(230, 57, 70, 0.4) !important;
            z-index: 999999 !important;
        }
        [data-testid="collapsedControl"] svg {
            fill: #FFFFFF !important;
            color: #FFFFFF !important;
            width: 28px !important;
            height: 28px !important;
        }
        
        /* 3. Colores de textos generales y botones */
        h1, h2, h3, p, span, label, .stMarkdown { color: #FFFFFF !important; }
        
        button[data-testid="stBaseButton-primary"] {
            background-color: #E63946 !important;
            color: #FFFFFF !important;
            font-weight: 800 !important;
            border: none !important;
            border-radius: 8px !important;
        }
        button[data-testid="stBaseButton-secondary"] {
            background-color: #1A1A1A !important;
            color: #FFFFFF !important; 
            border: 1px solid #E63946 !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }
        
        /* Inputs y Desplegables con contraste visible */
        div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, div[data-baseweb="select"] > div {
            background-color: #1A1A1A !important;
            border: 1px solid #444444 !important;
            border-radius: 8px !important;
            color: white !important;
        }
        div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea { color: #FFFFFF !important; }
        
        /* 4. Tarjetas y Cajas de diseño */
        .insta-card { background-color: #141414 !important; border-radius: 12px; border: 1px solid #333; margin-bottom: 30px; max-width: 500px; margin-left: auto; margin-right: auto; overflow: hidden; }
        .insta-header { padding: 12px; border-bottom: 1px solid #333; font-weight: 700; color: #E63946 !important; }
        .insta-footer { padding: 12px; }
        .insta-date { font-size: 11px; color: gray; margin-top: 5px;}
        
        .bubble { padding: 10px 15px; border-radius: 20px; margin-bottom: 10px; max-width: 75%; font-size: 14px; }
        .bubble-user { background-color: #E63946 !important; color: white !important; margin-left: auto; border-bottom-right-radius: 4px; font-weight: 500;}
        .bubble-admin { background-color: #222222 !important; color: white !important; margin-right: auto; border-bottom-left-radius: 4px; }
        
        .stExpander { background-color: #141414 !important; border: 1px solid #333 !important; border-radius: 8px !important; }
        .status-expired { color: #ff4b4b !important; font-weight: bold; }
        .status-ok { color: #00ff00 !important; }
        .req-foto { color: #111111 !important; font-size: 11px; font-weight: bold; background: #FFD166; padding: 4px 8px; border-radius: 6px;}
        
        .rank-card { background-color: #141414; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #E63946; display: flex; justify-content: space-between; align-items: center;}
        .rank-pos { font-size: 24px; font-weight: bold; color: #E63946; width: 40px;}
        .rank-name { font-size: 18px; font-weight: bold; flex-grow: 1; color: white;}
        .rank-score { font-size: 20px; font-weight: bold; color: #00ff00; }
        
        .logo-container { display: flex; justify-content: center; padding: 10px 0; flex-direction: column; align-items: center; }
        .circular-logo { width: 110px; height: 110px; border-radius: 50%; object-fit: cover; border: 2px solid #E63946; margin-bottom: 10px; }
        </style>
    """, unsafe_allow_html=True)

    # ==========================================
    # PANTALLA 1: LOGIN
    # ==========================================
    if not st.session_state.auth:
        col1, col2, col3 = st.columns([1,1.5,1])
        with col2:
            logo = cargar_logo_base64()
            st.markdown('<div class="logo-container">', unsafe_allow_html=True)
            if logo: st.markdown(f'<img src="data:image/png;base64,{logo}" class="circular-logo">', unsafe_allow_html=True)
            st.markdown('<h2 style="text-align: center; color: #E63946 !important; font-weight:800;">Intranet Cantina</h2></div>', unsafe_allow_html=True)
            
            if st.session_state.page == "login":
                with st.form("login_form"):
                    e = st.text_input("Email")
                    n = st.text_input("NIF")
                    p = st.text_input("Contraseña", type="password")
                    if st.form_submit_button("Entrar", type="primary", use_container_width=True):
                        df_u = load("Usuarios", 0)
                        v = df_u[(df_u['Email'].str.strip() == e.strip()) & (df_u['NIF_NIE'].astype(str).str.strip() == n.strip()) & (df_u['Contraseña'].astype(str).str.strip() == p.strip())]
                        if not v.empty:
                            ud = v.iloc[0].to_dict()
                            if str(ud.get('Estado')).strip().capitalize() != "Activo": 
                                st.error("⛔ Usuario Inactivo.")
                            else:
                                st.session_state.user = ud
                                st.session_state.auth = True
                                roles_list = [r.strip() for r in str(ud.get('Roles', '')).split(',') if r.strip()]
                                st.session_state.rol_activo = roles_list[0] if roles_list else "Empleado"
                                st.session_state.page = "change_password" if str(ud.get('Primer_Acceso')).strip().upper() == "SÍ" else "notifications"
                                st.rerun()
                        else: st.error("❌ Credenciales incorrectas.")
                if st.button("Olvidé mi contraseña", type="secondary"): st.session_state.page = "forgot_step1"; st.rerun()

            elif "forgot" in st.session_state.page:
                if st.session_state.page == "forgot_step1":
                    em = st.text_input("Tu Email")
                    if st.button("Enviar Código", type="primary", use_container_width=True):
                        df_u = load("Usuarios", 0)
                        if em in df_u['Email'].values:
                            c = str(random.randint(100000, 999999))
                            st.session_state.recovery_code, st.session_state.recovery_email = c, em
                            enviar_aviso_email(em, "Código Recuperación", f"Tu código: {c}")
                            st.session_state.page = "forgot_step2"; st.rerun()
                        else: st.error("No existe.")
                    if st.button("Volver", type="secondary"): st.session_state.page = "login"; st.rerun()
                elif st.session_state.page == "forgot_step2":
                    uc = st.text_input("Código")
                    if st.button("Validar", type="primary", use_container_width=True):
                        if uc == st.session_state.recovery_code: st.session_state.page = "forgot_step3"; st.rerun()
                elif st.session_state.page == "forgot_step3":
                    with st.form("np"):
                        new_p = st.text_input("Nueva pass", type="password")
                        if st.form_submit_button("Actualizar", type="primary", use_container_width=True):
                            df = load("Usuarios", 0); idx = df[df['Email'] == st.session_state.recovery_email].index[0]
                            df.at[idx, 'Contraseña'] = new_p; conn.update(worksheet="Usuarios", data=df)
                            st.session_state.page = "login"; st.rerun()

    # ==========================================
    # PANTALLA 2: CAMBIO DE CLAVE
    # ==========================================
    elif st.session_state.page == "change_password":
        st.title("🔑 Cambio de Clave")
        st.write("Al ser tu primer acceso, debes poner una contraseña nueva por seguridad.")
        with st.form("cp"):
            p1, p2 = st.text_input("Nueva clave", type="password"), st.text_input("Repite", type="password")
            if st.form_submit_button("Guardar", type="primary", use_container_width=True):
                if p1 == p2 and len(p1) > 4:
                    df = load("Usuarios", 0); idx = df[df['Email'] == st.session_state.user['Email']].index[0]
                    df.at[idx, 'Contraseña'], df.at[idx, 'Primer_Acceso'] = p1, "NO"
                    conn.update(worksheet="Usuarios", data=df)
                    st.session_state.page = "notifications"; st.rerun()

    # ==========================================
    # PANTALLA 3: NOTIFICACIONES
    # ==========================================
    elif st.session_state.page == "notifications":
        u = st.session_state.user
        st.markdown(f"<h1 style='color: #E63946 !important;'>👋 Hola, {u['Nombre_Apellidos']}</h1>", unsafe_allow_html=True)
        try: last_log = pd.to_datetime(u.get('Ultima_Conexion'), format="%Y-%m-%d %H:%M:%S")
        except: last_log = datetime(2000,1,1)
        alertas = []
        df_av = load("Avisos", 30)
        if not df_av.empty:
            fechas_av = pd.to_datetime(df_av['Fecha_Publicacion'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
            if fechas_av.max() > last_log: alertas.append("📱 Hay nuevos avisos en el Tablón de Novedades.")
        if alertas:
            st.subheader("🔔 Novedades:")
            for a in alertas: st.info(a)
            if st.button("Entrar a la Intranet", type="primary", use_container_width=True):
                df = load("Usuarios", 0); idx = df[df['Email'] == u['Email']].index[0]
                df.at[idx, 'Ultima_Conexion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.update(worksheet="Usuarios", data=df); st.session_state.page = "main"; st.rerun()
        else:
            df = load("Usuarios", 0); idx = df[df['Email'] == u['Email']].index[0]
            df.at[idx, 'Ultima_Conexion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.update(worksheet="Usuarios", data=df); st.session_state.page = "main"; st.rerun()

    # ==========================================
    # PANTALLA 4: APP PRINCIPAL (CON SIDEBAR RESTAURADO)
    # ==========================================
    elif st.session_state.page == "main":
        u = st.session_state.user
        roles_disponibles = [r.strip() for r in str(u.get('Roles', '')).split(',') if r.strip()]
        is_admin = st.session_state.rol_activo == "Admin"
        is_encargado = st.session_state.rol_activo == "Encargado"

        df_c_check = load("Chat_Directo", 5)
        hay_mensaje = False
        try:
            lc = pd.to_datetime(u.get('Ultima_Conexion'), format="%Y-%m-%d %H:%M:%S")
            if not is_admin:
                ha = df_c_check[(df_c_check['Usuario_Email']==u['Email']) & (df_c_check['Autor']=='Admin')]
                if not ha.empty and pd.to_datetime(ha['Fecha_Hora'], format="%Y-%m-%d %H:%M:%S", errors='coerce').max() > lc: 
                    hay_mensaje = True
        except: pass

        # --- MENÚ LATERAL (SIDEBAR) ---
        with st.sidebar:
            logo_data = cargar_logo_base64()
            if logo_data: st.markdown(f'<div style="text-align: center; margin-bottom:15px;"><img src="data:image/png;base64,{logo_data}" style="width:80px; height:80px; border-radius:50%; border: 2px solid #E63946; object-fit: cover;"></div>', unsafe_allow_html=True)
            
            st.markdown(f"<strong style='font-size:16px;'>{u['Nombre_Apellidos']}</strong>", unsafe_allow_html=True)
            if len(roles_disponibles) > 1:
                nuevo_rol = st.selectbox("Rol:", roles_disponibles, index=roles_disponibles.index(st.session_state.rol_activo), label_visibility="collapsed")
                if nuevo_rol != st.session_state.rol_activo:
                    st.session_state.rol_activo = nuevo_rol
                    st.rerun()
            else:
                st.markdown(f"<span style='color:#E63946; font-size:14px; font-weight:bold;'>{st.session_state.rol_activo}</span>", unsafe_allow_html=True)
            st.caption(f"📍 {u['Sede']}")
            st.divider()

            icono_chat = "🔴 Chat" if hay_mensaje else "💬 Chat"
            menu = st.radio("NAVEGACIÓN", [
                "📱 Inicio", 
                "✅ Tareas", 
                "📄 Mis Docs", 
                "📚 Manuales", 
                "❓ FAQs", 
                icono_chat, 
                "🏆 Quiz", 
                "ℹ️ Guía"
            ])
            
            st.divider()
            st.info("⚠️ NO arrastres la pantalla hacia abajo para recargar o se cerrará tu sesión.")
            if st.button("🔄 Actualizar Datos", type="primary", use_container_width=True):
                st.rerun()
                
            st.write("")
            if st.button("🚪 Salir", type="secondary", use_container_width=True): 
                st.session_state.clear()
                st.rerun()

        # --- VISTAS DEL MENÚ ---
        if "Inicio" in menu:
            st.markdown("<h3 style='color:#E63946; font-weight:800;'>📱 Tablón de Novedades</h3>", unsafe_allow_html=True)
            df = load("Avisos", 300)
            for _, r in df.sort_values(by=df.columns[0], ascending=False).iterrows():
                img_url = procesar_img_drive(r.get('Enlace_Imagen'))
                autor = str(r.get('Nombre_Apellidos')) if not pd.isna(r.get('Nombre_Apellidos')) else "Admin"
                sede = str(r.get('Sede_Destino')) if not pd.isna(r.get('Sede_Destino')) else "Todas"
                st.markdown(f'<div class="insta-card"><div class="insta-header">📍 {sede} • {autor}</div>', unsafe_allow_html=True)
                if img_url: st.image(img_url, use_container_width=True)
                st.markdown(f'<div class="insta-footer"><b>{r.get("Titulo")}</b>: {r.get("Contenido")}<div class="insta-date">{r.get("Fecha_Publicacion")}</div></div></div>', unsafe_allow_html=True)

        elif "Tareas" in menu:
            st.markdown("<h3 style='color:#E63946; font-weight:800;'>✅ Gestión de Tareas</h3>", unsafe_allow_html=True)
            df_t, df_u, df_com = load("Tareas", 5), load("Usuarios", 300), load("Comentarios_Tareas", 5)
            
            tabs_t = st.tabs(["📊 Dash", "⚡ Exprés", "🆕 Ptes", "🚧 Proc", "✅ Fin"])
            
            # Pestaña 1: DASHBOARD
            with tabs_t[0]:
                if 'Fecha_Creacion' not in df_t.columns: df_t['Fecha_Creacion'] = pd.NaT
                if 'Fecha_Completada' not in df_t.columns: df_t['Fecha_Completada'] = pd.NaT
                if not is_admin and not is_encargado: df_dash = df_t[(df_t['Asignado_A'] == u['Email']) | (df_t['Creado_Por'] == u['Nombre_Apellidos'])].copy()
                else: df_dash = df_t.copy()

                map_email_nombre = dict(zip(df_u['Email'], df_u['Nombre_Apellidos']))
                df_dash['Nombre_Empleado'] = df_dash['Asignado_A'].map(map_email_nombre).fillna(df_dash['Asignado_A'])

                lista_emps = ["Todos"] + sorted(df_dash['Nombre_Empleado'].dropna().unique().tolist())
                filtro_emp = st.selectbox("👤 Empleado", lista_emps)
                if filtro_emp != "Todos": df_dash = df_dash[df_dash['Nombre_Empleado'] == filtro_emp]
                
                st.divider()
                c1, c2, c3 = st.columns(3)
                tot = len(df_dash)
                comp = len(df_dash[df_dash['Estado'] == 'Completada'])
                pend = len(df_dash[df_dash['Estado'] == 'Pendiente'])
                
                c1.metric("📋 Total", tot)
                c2.metric("✅ Fin", comp)
                c3.metric("🆕 Ptes", pend)

                if tot > 0:
                    st.write("")
                    st.markdown("**Por Estado**")
                    st.bar_chart(df_dash['Estado'].value_counts(), color="#E63946")

            # Pestaña 2: PLANTILLAS RÁPIDAS
            with tabs_t[1]:
                st.write("Lanza rutinas de equipo.")
                def lanzar_tarea_masiva(titulo, desc, rol_destino):
                    usuarios_destino = df_u[df_u['Roles'].str.contains(rol_destino, na=False, case=False) & df_u.apply(lambda r: comparten_sede(u['Sede'], r['Sede']), axis=1)]
                    if usuarios_destino.empty:
                        st.warning(f"No hay usuarios con el rol {rol_destino} en tu sede.")
                        return
                    nuevas_tareas = []
                    desc_foto = desc + " [REQ_FOTO]"
                    hoy_str = str(date.today())
                    for _, empleado in usuarios_destino.iterrows():
                        nuevas_tareas.append({"ID_Tarea": str(uuid.uuid4())[:8], "Titulo_Tarea": titulo, "Descripción": desc_foto, "Asignado_A": empleado['Email'], "Creado_Por": u['Nombre_Apellidos'], "Sede": u['Sede'], "Estado": "Pendiente", "Fecha_Limite": hoy_str, "Fecha_Creacion": hoy_str, "Fecha_Completada": ""})
                    conn.update(worksheet="Tareas", data=pd.concat([df_t, pd.DataFrame(nuevas_tareas)], ignore_index=True))
                    st.success(f"🚀 Enviada a {len(nuevas_tareas)} empleados.")
                    time.sleep(1); st.rerun()

                with st.container(border=True):
                    st.subheader("🧹 Cierre de Cocina")
                    if st.button("Lanzar a Cocineros", key="t_cc", type="primary"): lanzar_tarea_masiva("Cierre de Cocina", "Realizar tareas de cierre según protocolo.", "Cocinero")
                with st.container(border=True):
                    st.subheader("☀️ Apertura de Sala")
                    if st.button("Lanzar a Camareros", key="t_as", type="primary"): lanzar_tarea_masiva("Apertura de Sala", "Apertura según protocolo.", "Camarero")

                with st.expander("➕ Crear Tarea Manual"):
                    with st.form("nt", clear_on_submit=True):
                        tit = st.text_input("Título")
                        dsc = st.text_area("Descripción")
                        fl = st.date_input("Límite", min_value=date.today())
                        pos_u = df_u[df_u.apply(lambda r: comparten_sede(u['Sede'], r['Sede']), axis=1)]
                        lp = pos_u['Nombre_Apellidos'].tolist()
                        nd = st.selectbox("Asignar:", ["Sin usuarios", "📣 Difusión Camareros", "📣 Difusión Cocineros"] + lp)
                        requiere_foto = st.checkbox("📸 Exigir foto al empleado")
                        
                        if st.form_submit_button("Crear Tarea", type="primary"):
                            if not tit.strip() or not dsc.strip() or nd == "Sin usuarios" or not nd:
                                st.error("⛔ Rellena Título, Descripción y Asignado.")
                            else:
                                final_desc = dsc + " [REQ_FOTO]" if requiere_foto else dsc
                                nuevas_t = []
                                hoy_str = str(date.today())
                                if "Difusión" in nd:
                                    rol_buscado = "Camarero" if "Camareros" in nd else "Cocinero"
                                    empleados_dif = pos_u[pos_u['Roles'].str.contains(rol_buscado, na=False, case=False)]
                                    for _, emp in empleados_dif.iterrows():
                                        nuevas_t.append({"ID_Tarea": str(uuid.uuid4())[:8], "Titulo_Tarea": tit, "Descripción": final_desc, "Asignado_A": emp['Email'], "Creado_Por": u['Nombre_Apellidos'], "Sede": u['Sede'], "Estado": "Pendiente", "Fecha_Limite": str(fl), "Fecha_Creacion": hoy_str, "Fecha_Completada": ""})
                                else:
                                    em_d = df_u[df_u['Nombre_Apellidos']==nd]['Email'].values[0]
                                    nuevas_t.append({"ID_Tarea": str(uuid.uuid4())[:8], "Titulo_Tarea": tit, "Descripción": final_desc, "Asignado_A": em_d, "Creado_Por": u['Nombre_Apellidos'], "Sede": u['Sede'], "Estado": "Pendiente", "Fecha_Limite": str(fl), "Fecha_Creacion": hoy_str, "Fecha_Completada": ""})
                                conn.update(worksheet="Tareas", data=pd.concat([df_t, pd.DataFrame(nuevas_t)], ignore_index=True))
                                st.success("Guardado."); time.sleep(1); st.rerun()

            # MOTOR DE RENDERIZADO DE TAREAS
            def draw(est_v, t_tab):
                with t_tab:
                    f = df_t[df_t['Estado'] == est_v]
                    if not is_admin: f = f[(f['Asignado_A'] == u['Email']) | (f['Creado_Por'] == u['Nombre_Apellidos'])]
                    
                    for idx, r in f.iterrows():
                        status_icon, limite_str = "🔵", ""
                        if r.get('Fecha_Limite'):
                            try:
                                d_lim = pd.to_datetime(r['Fecha_Limite']).date()
                                dias_rest = (d_lim - date.today()).days
                                if dias_rest < 0: status_icon, limite_str = "🔴", "(⚠️ CADUCADA)"
                                elif dias_rest == 0: status_icon, limite_str = "🟠", "(⏳ HOY)"
                                else: status_icon, limite_str = "🟢", f"(📅 {dias_rest} d)"
                            except: pass
                        
                        desc_limpia = str(r.get('Descripción', ''))
                        es_evidencia = "[REQ_FOTO]" in desc_limpia
                        desc_limpia = desc_limpia.replace("[REQ_FOTO]", "").strip()
                        req_badge = " 📸 FOTO" if es_evidencia else ""
                        
                        header_txt = f"{status_icon} **{r['Titulo_Tarea']}** | De: {r['Creado_Por']} {limite_str} {req_badge}"
                        with st.expander(header_txt):
                            st.write(f"**Para:** {r.get('Asignado_A', 'N/A')}")
                            st.write(f"**Desc:** {desc_limpia}")
                            if es_evidencia: st.markdown('<span class="req-foto">⚠️ Sube foto para completarla.</span>', unsafe_allow_html=True)
                            st.divider()
                            
                            c_l = df_com[df_com['ID_Tarea'] == r['ID_Tarea']]
                            for _, c in c_l.iterrows():
                                with st.chat_message("user"):
                                    st.write(f"**{c['Nombre_Apellidos']}**")
                                    if "data:image" in str(c['Texto']): st.image(c['Texto'], width=300)
                                    else: st.write(c['Texto'])
                            
                            with st.form(key=f"c_{r['ID_Tarea']}", clear_on_submit=True):
                                mc, fc = st.text_input("Mensaje"), st.file_uploader("📸 Foto/Evidencia", type=['jpg','png'], key=f"f_{r['ID_Tarea']}")
                                if st.form_submit_button("Enviar Comentario", type="secondary"):
                                    val = mc
                                    if fc: val = comprimir_foto(fc)
                                    n_c = pd.DataFrame([{"ID_Tarea": r['ID_Tarea'], "Nombre_Apellidos": u['Nombre_Apellidos'], "Texto": val, "Fecha_Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
                                    conn.update(worksheet="Comentarios_Tareas", data=pd.concat([df_com, n_c], ignore_index=True)); st.rerun()
                            
                            ns = st.selectbox("Estado:", ["Pendiente", "En Proceso", "Completada"], index=["Pendiente", "En Proceso", "Completada"].index(r['Estado']), key=f"s_{r['ID_Tarea']}")
                            if ns != r['Estado']:
                                if ns == "Completada" and es_evidencia:
                                    tiene_foto = c_l[c_l['Texto'].str.contains("data:image", na=False)].shape[0] > 0
                                    if not tiene_foto: st.error("⛔ Sube una foto para completarla.")
                                    else: df_t.at[idx, 'Estado'], df_t.at[idx, 'Fecha_Completada'] = ns, str(date.today()); conn.update(worksheet="Tareas", data=df_t); st.rerun()
                                else:
                                    df_t.at[idx, 'Estado'] = ns
                                    df_t.at[idx, 'Fecha_Completada'] = str(date.today()) if ns == "Completada" else ""
                                    conn.update(worksheet="Tareas", data=df_t); st.rerun()
                                    
            draw("Pendiente", tabs_t[2]); draw("En Proceso", tabs_t[3]); draw("Completada", tabs_t[4])

        elif "Docs" in menu:
            st.markdown("<h3 style='color:#E63946; font-weight:800;'>📄 Documentos</h3>", unsafe_allow_html=True)
            df_d = load("Documentos", 600)
            if is_admin:
                df_u_docs = load("Usuarios", 600)
                df_d['NIF_NIE'] = df_d['NIF_NIE'].astype(str).str.strip()
                df_u_docs['NIF_NIE'] = df_u_docs['NIF_NIE'].astype(str).str.strip()
                mapa = dict(zip(df_u_docs['NIF_NIE'], df_u_docs['Nombre_Apellidos']))
                df_d['Nombre_Asignado'] = df_d['NIF_NIE'].map(mapa).fillna("Desconocido")
                df_d['Busqueda_Comb'] = df_d['Nombre_Asignado'] + " (" + df_d['NIF_NIE'] + ")"
                lista_opc = sorted(df_d['Busqueda_Comb'].unique().tolist())
                sel = st.selectbox("🔍 Buscar Empleado:", lista_opc, index=None, placeholder="Escribe para buscar...")
                dv = df_d[df_d['Busqueda_Comb'] == sel] if sel else df_d
                if not dv.empty and 'Categoria' in dv.columns:
                    cats_d = dv['Categoria'].unique().tolist()
                    if cats_d:
                        sc = st.selectbox("📂 Filtrar Categoría:", ["Todas"] + cats_d)
                        if sc != "Todas": dv = dv[dv['Categoria'] == sc]
            else:
                dv = df_d[df_d['NIF_NIE'].astype(str).str.strip() == str(u['NIF_NIE']).strip()]
                if not dv.empty and 'Categoria' in dv.columns:
                    cats_d = dv['Categoria'].unique().tolist()
                    if cats_d:
                        sc = st.selectbox("📂 Tipo:", ["Todos"] + cats_d)
                        if sc != "Todas": dv = dv[dv['Categoria'] == sc]
            if not dv.empty:
                sel_d = st.selectbox("Elegir Documento:", dv['Nombre Documento'])
                st.components.v1.iframe(f"https://drive.google.com/file/d/{extraer_id_drive(dv[dv['Nombre Documento']==sel_d]['Enlace_Archivo'].values[0])}/preview", height=600)
            else:
                st.info("No hay documentos disponibles.")

        elif "Chat" in menu:
            st.markdown("<h3 style='color:#E63946; font-weight:800;'>💬 Soporte</h3>", unsafe_allow_html=True)
            df_chat = load("Chat_Directo", 5)
            df_u_chat = load("Usuarios", 300)
            tm = u['Email']
            if is_admin:
                lc = df_u_chat[~df_u_chat['Roles'].str.contains("Admin")]['Nombre_Apellidos'].tolist()
                tn = st.selectbox("Chat con:", lc)
                tm = df_u_chat[df_u_chat['Nombre_Apellidos']==tn]['Email'].values[0]
            
            st.divider()
            for _, m in df_chat[df_chat['Usuario_Email']==tm].iterrows():
                im = (not is_admin and m['Autor'] == 'Usuario') or (is_admin and m['Autor'] == 'Admin')
                st.markdown(f'<div class="bubble {"bubble-user" if im else "bubble-admin"}">{m["Texto"]}</div>', unsafe_allow_html=True)
            
            if p := st.chat_input("Escribe aquí tu mensaje..."):
                nm = pd.DataFrame([{"Usuario_Email": tm, "Texto": p, "Fecha_Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Autor": "Admin" if is_admin else "Usuario"}])
                conn.update(worksheet="Chat_Directo", data=pd.concat([df_chat, nm], ignore_index=True))
                enviar_aviso_email(tm, "Nuevo Mensaje Chat", f"Respuesta de Admin: {p}"); st.rerun()

        elif "Quiz" in menu:
            st.markdown(f"<h3 style='color:#E63946; font-weight:800;'>🏆 Quiz: {MES_ACTUAL_QUIZ}</h3>", unsafe_allow_html=True)
            st.write("Pon a prueba tus conocimientos sobre los Protocolos y Normas. Tienes **1 solo intento**. ¡Compite por el primer puesto en el ranking!")
            st.divider()

            try: df_ranking = load("Ranking_Quiz", 0)
            except Exception:
                df_ranking = pd.DataFrame(columns=["Mes", "Email", "Nombre", "Rol", "Puntuacion", "Fecha"])
                st.error("Ranking no creado en GSheets.")
                st.stop()

            ha_participado = not df_ranking[(df_ranking['Email'] == u['Email']) & (df_ranking['Mes'] == MES_ACTUAL_QUIZ)].empty

            if ha_participado:
                st.success("✅ Ya has participado este mes.")
                mi_nota = df_ranking[(df_ranking['Email'] == u['Email']) & (df_ranking['Mes'] == MES_ACTUAL_QUIZ)]['Puntuacion'].values[0]
                st.metric("Tu Puntuación", f"{mi_nota} / 20")
                st.divider()
                st.subheader("📊 Ranking del Mes")
                df_mes = df_ranking[df_ranking['Mes'] == MES_ACTUAL_QUIZ].copy()
                df_mes['Puntuacion'] = pd.to_numeric(df_mes['Puntuacion'])
                df_ordenado = df_mes.sort_values(by=['Puntuacion', 'Fecha'], ascending=[False, True]).reset_index(drop=True)
                for index, row in df_ordenado.iterrows():
                    pos = index + 1
                    medalla = "🥇" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else f"{pos}º"
                    st.markdown(f'<div class="rank-card"><div class="rank-pos">{medalla}</div><div class="rank-name">{row["Nombre"]} <span style="font-size:12px; color:gray;">({row["Rol"]})</span></div><div class="rank-score">{row["Puntuacion"]} pts</div></div>', unsafe_allow_html=True)
            else:
                diccionario_preguntas = QUIZ_COCINA if "Cocine" in st.session_state.rol_activo else QUIZ_SALA
                tipo_examen = "Cocina" if "Cocine" in st.session_state.rol_activo else "Sala"
                st.info(f"Examen de: **{tipo_examen}**.")
                with st.form("quiz_form"):
                    respuestas_usuario = {}
                    for i, (pregunta, (opciones, correcta_idx)) in enumerate(diccionario_preguntas.items()):
                        pregunta_limpia = re.sub(r'^\d+\.\s*', '', pregunta)
                        st.markdown(f"**{i+1}. {pregunta_limpia}**")
                        respuestas_usuario[i] = st.radio("Opciones", opciones, key=f"q_{i}", index=None, label_visibility="collapsed")
                        st.write("")
                    
                    if st.form_submit_button("Enviar Mis Respuestas", type="primary", use_container_width=True):
                        if None in respuestas_usuario.values(): st.error("⛔ Responde todas las preguntas.")
                        else:
                            puntuacion = 0
                            for i, (pregunta, (opciones, correcta_idx)) in enumerate(diccionario_preguntas.items()):
                                if respuestas_usuario[i] == opciones[correcta_idx]: puntuacion += 1
                            nuevo_registro = pd.DataFrame([{"Mes": MES_ACTUAL_QUIZ, "Email": u['Email'], "Nombre": u['Nombre_Apellidos'], "Rol": st.session_state.rol_activo, "Puntuacion": puntuacion, "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
                            conn.update(worksheet="Ranking_Quiz", data=pd.concat([df_ranking, nuevo_registro], ignore_index=True))
                            st.success("¡Enviado!"); time.sleep(1); st.rerun()
            
        elif "Manuales" in menu:
            st.markdown("<h3 style='color:#E63946; font-weight:800;'>📚 Manuales</h3>", unsafe_allow_html=True)
            df_m = load("Manuales", 600)
            cats = df_m['Categoria'].unique()
            for c in cats:
                with st.expander(f"📂 {c}"):
                    for _, r in df_m[df_m['Categoria'] == c].iterrows():
                        st.write(f"**{r['Nombre_Manual']}**")
                        if st.button("Ver", key=f"m_{r['Nombre_Manual']}", type="secondary"): st.components.v1.iframe(f"https://drive.google.com/file/d/{extraer_id_drive(r['Enlace Drive'])}/preview", height=500)
            
        elif "FAQs" in menu:
            st.markdown("<h3 style='color:#E63946; font-weight:800;'>❓ FAQs</h3>", unsafe_allow_html=True)
            df_f = load("FAQ", 600)
            cats = df_f['Categoria'].unique()
            for c in cats:
                with st.expander(f"❓ {c}"):
                    for _, r in df_f[df_f['Categoria'] == c].iterrows():
                        with st.expander(r['Pregunta']): st.write(r['Respuesta'])
                        
        elif "Guía" in menu:
            st.markdown("<h3 style='color:#E63946; font-weight:800;'>ℹ️ Guía de Uso</h3>", unsafe_allow_html=True)
            st.write("Esta herramienta es tu centro de mando.")
            with st.expander("📱 Tablón y 📄 Docs"): st.write("Noticias generales y acceso a tus nóminas.")
            with st.expander("✅ Tareas (Evidencia)"): st.write("🟢 Verde: En plazo | 🟠 Naranja: Hoy | 🔴 Rojo: Caducada. \n📸 **Foto Obligatoria:** Si la tarea tiene el aviso, sube foto al chat.")
            with st.expander("🔄 ¿Por qué se me cierra la sesión?"): st.write("Nunca arrastres la pantalla hacia abajo para recargar o la App se reiniciará. Usa el botón 'Actualizar Datos' del menú.")

except Exception as e:
    reportar_error_a_mario(e)
    st.error("⚠️ Error técnico reportado a Admin.")
    if st.button("Recargar", type="primary"): st.rerun()
