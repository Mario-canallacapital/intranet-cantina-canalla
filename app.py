# --- VERSIÓN v34.0 (ROLE MASTER & LOGOUT FIX) ---
# Actualizado: 12/02/2026 
# 1. Selector de Roles dinámico en Sidebar
# 2. Filtro Categorías Docs para Admin
# 3. Hard Reset en Logout

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
st.set_page_config(page_title="Intranet Cantina Canalla", layout="wide", page_icon="🍴")

# --- CONFIGURACIÓN CORREO ---
EMAIL_GENERICO = "avisosapp.cantinacanalla@gmail.com" 
PASS_GENERICA = "pvyglchitjtupzoz" 

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
    cuerpo = f"🚨 ERROR v34.0 🚨\n\nFecha: {ahora}\nUsuario: {user}\n\nTraceback:\n{error_detallado}"
    enviar_aviso_email("mario@canallacapital.com", "🚨 ERROR APP CANTINA", cuerpo)

# --- BLOQUE DE SEGURIDAD ---
try:
    # --- CSS ---
    st.markdown("""
        <style>
        .stApp { background-color: #000000 !important; color: #ffffff !important; }
        [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 1px solid #333; }
        
        .logo-container { display: flex; justify-content: center; padding: 10px 0; flex-direction: column; align-items: center; }
        .circular-logo { width: 110px; height: 110px; border-radius: 50%; object-fit: cover; border: 2px solid #8a3ab9; margin-bottom: 10px; }
        
        .insta-card { background-color: #121212 !important; border-radius: 12px; border: 1px solid #333; margin-bottom: 30px; max-width: 500px; margin-left: auto; margin-right: auto; overflow: hidden; }
        .insta-header { padding: 12px; border-bottom: 1px solid #333; font-weight: 700; color: white !important; }
        .bubble { padding: 10px 15px; border-radius: 20px; margin-bottom: 10px; max-width: 75%; font-size: 14px; }
        .bubble-user { background-color: #8a3ab9 !important; color: white !important; margin-left: auto; border-bottom-right-radius: 4px; }
        .bubble-admin { background-color: #262626 !important; color: white !important; margin-right: auto; border-bottom-left-radius: 4px; }
        h1, h2, h3, p, span, label, .stMarkdown, .stExpander, .stSubheader { color: #ffffff !important; }
        .stExpander { background-color: #121212 !important; border: 1px solid #333 !important; }
        .status-expired { color: #ff4b4b !important; font-weight: bold; }
        .status-ok { color: #00ff00 !important; }
        </style>
    """, unsafe_allow_html=True)

    # --- FUNCIONES ---
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

    @st.cache_data(ttl=600)
    def procesar_img_drive(url):
        fid = extraer_id_drive(url)
        if not fid: return None
        try:
            res = requests.get(f"https://drive.google.com/uc?export=download&id={fid}", timeout=10)
            return f"data:image/jpeg;base64,{base64.b64encode(res.content).decode()}"
        except: return None

    # --- CONEXIÓN ---
    conn = st.connection("gsheets", type=GSheetsConnection)
    def load(p, ttl=5):
        max_retries = 3
        for i in range(max_retries):
            try: return conn.read(worksheet=p, ttl=ttl)
            except Exception as e:
                if i == max_retries - 1: raise e
                time.sleep(2)

    # --- SESIÓN ---
    if 'auth' not in st.session_state: st.session_state.auth = False
    if 'page' not in st.session_state: st.session_state.page = "login"

    # --- 1. LOGIN ---
    if not st.session_state.auth:
        col1, col2, col3 = st.columns([1,1.5,1])
        with col2:
            logo = cargar_logo_base64()
            st.markdown('<div class="logo-container">', unsafe_allow_html=True)
            if logo: st.markdown(f'<img src="data:image/png;base64,{logo}" class="circular-logo">', unsafe_allow_html=True)
            st.markdown('<h2 style="text-align: center;">Intranet Cantina Canalla</h2></div>', unsafe_allow_html=True)
            
            if st.session_state.page == "login":
                with st.form("login_form"):
                    e, n, p = st.text_input("Email"), st.text_input("NIF"), st.text_input("Contraseña", type="password")
                    if st.form_submit_button("Entrar", use_container_width=True):
                        df_u = load("Usuarios", 0)
                        v = df_u[(df_u['Email'].str.strip() == e.strip()) & (df_u['NIF_NIE'].astype(str).str.strip() == n.strip()) & (df_u['Contraseña'].astype(str).str.strip() == p.strip())]
                        if not v.empty:
                            ud = v.iloc[0].to_dict()
                            if str(ud.get('Estado')).strip().capitalize() != "Activo": st.error("⛔ Usuario Inactivo.")
                            else:
                                st.session_state.user = ud; st.session_state.auth = True
                                st.session_state.page = "change_password" if str(ud.get('Primer_Acceso')).strip().upper() == "SÍ" else "notifications"
                                st.rerun()
                        else: st.error("❌ Credenciales incorrectas.")
                if st.button("Olvidé mi contraseña"): st.session_state.page = "forgot_step1"; st.rerun()

            elif "forgot" in st.session_state.page:
                if st.session_state.page == "forgot_step1":
                    em = st.text_input("Tu Email")
                    if st.button("Enviar Código"):
                        df_u = load("Usuarios", 0)
                        if em in df_u['Email'].values:
                            c = str(random.randint(100000, 999999))
                            st.session_state.recovery_code, st.session_state.recovery_email = c, em
                            enviar_aviso_email(em, "Código Recuperación", f"Tu código: {c}")
                            st.session_state.page = "forgot_step2"; st.rerun()
                        else: st.error("No existe.")
                    if st.button("Volver"): st.session_state.page = "login"; st.rerun()
                elif st.session_state.page == "forgot_step2":
                    uc = st.text_input("Código")
                    if st.button("Validar"):
                        if uc == st.session_state.recovery_code: st.session_state.page = "forgot_step3"; st.rerun()
                elif st.session_state.page == "forgot_step3":
                    with st.form("np"):
                        new_p = st.text_input("Nueva pass", type="password")
                        if st.form_submit_button("Actualizar"):
                            df = load("Usuarios", 0); idx = df[df['Email'] == st.session_state.recovery_email].index[0]
                            df.at[idx, 'Contraseña'] = new_p; conn.update(worksheet="Usuarios", data=df)
                            st.session_state.page = "login"; st.rerun()

    # --- 2. CAMBIO CLAVE ---
    elif st.session_state.page == "change_password":
        st.title("🔑 Cambio de Clave Obligatorio")
        with st.form("cp"):
            p1, p2 = st.text_input("Nueva clave", type="password"), st.text_input("Repite", type="password")
            if st.form_submit_button("Guardar"):
                if p1 == p2 and len(p1) > 4:
                    df = load("Usuarios", 0); idx = df[df['Email'] == st.session_state.user['Email']].index[0]
                    df.at[idx, 'Contraseña'], df.at[idx, 'Primer_Acceso'] = p1, "NO"
                    conn.update(worksheet="Usuarios", data=df)
                    st.session_state.page = "notifications"; st.rerun()

    # --- 3. NOTIFICACIONES ---
    elif st.session_state.page == "notifications":
        st.title(f"👋 Hola, {st.session_state.user['Nombre_Apellidos']}")
        u = st.session_state.user
        try: last_log = pd.to_datetime(u.get('Ultima_Conexion'), format="%Y-%m-%d %H:%M:%S")
        except: last_log = datetime(2000,1,1)
        alertas = []
        df_av = load("Avisos", 30)
        if not df_av.empty:
            fechas_av = pd.to_datetime(df_av['Fecha_Publicacion'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
            if fechas_av.max() > last_log: alertas.append("📱 Nuevos avisos en el Tablón")
        if alertas:
            st.subheader("🔔 Novedades:"); 
            for a in alertas: st.info(a)
            if st.button("Entrar"):
                df = load("Usuarios", 0); idx = df[df['Email'] == u['Email']].index[0]
                df.at[idx, 'Ultima_Conexion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.update(worksheet="Usuarios", data=df); st.session_state.page = "main"; st.rerun()
        else:
            df = load("Usuarios", 0); idx = df[df['Email'] == u['Email']].index[0]
            df.at[idx, 'Ultima_Conexion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.update(worksheet="Usuarios", data=df); st.session_state.page = "main"; st.rerun()

    # --- 4. APP PRINCIPAL ---
    elif st.session_state.page == "main":
        u = st.session_state.user
        
        # --- SELECTOR DE ROLES DINÁMICO (v34.0) ---
        # Parseamos los roles del string CSV a una lista limpia
        roles_disponibles = [r.strip() for r in str(u.get('Roles', '')).split(',') if r.strip()]
        
        # Sidebar con Logo y Selector
        with st.sidebar:
            logo_data = cargar_logo_base64()
            if logo_data: st.markdown(f'<div class="sidebar-logo-container"><img src="data:image/png;base64,{logo_data}" class="circular-logo"></div>', unsafe_allow_html=True)
            st.subheader(f"{u['Nombre_Apellidos']}")
            
            # Selector de Rol Activo
            rol_activo = st.selectbox("Rol Activo:", roles_disponibles, index=0)
            st.caption(f"📍 {u['Sede']}")
            st.divider()

            # Definimos los permisos basados en el ROL SELECCIONADO (No el string completo)
            is_admin = rol_activo == "Admin"
            is_encargado = rol_activo == "Encargado"

            # Dot Chat
            df_c_check = load("Chat_Directo", 5)
            dot = ""
            try:
                lc = pd.to_datetime(u.get('Ultima_Conexion'), format="%Y-%m-%d %H:%M:%S")
                if not is_admin:
                    ha = df_c_check[(df_c_check['Usuario_Email']==u['Email']) & (df_c_check['Autor']=='Admin')]
                    if not ha.empty and pd.to_datetime(ha['Fecha_Hora'], format="%Y-%m-%d %H:%M:%S", errors='coerce').max() > lc: dot = " 🔴"
            except: pass

            menu = st.radio("NAVEGACIÓN", ["📱 Tablón de Novedades", "📄 Mis Documentos", "📚 Manuales", "✅ Tareas", "❓ FAQs", f"💬 Chat{dot}"])
            
            st.write("")
            # --- LOGOUT FIX (Hard Reset) ---
            if st.button("Salir"):
                st.session_state.clear() # Borra toda la memoria
                st.rerun() # Recarga la app desde cero

        # --- SECCIONES ---
        if "Tablón" in menu:
            df = load("Avisos", 300)
            for _, r in df.sort_values(by=df.columns[0], ascending=False).iterrows():
                img = procesar_img_drive(r.get('Enlace_Imagen'))
                autor = str(r.get('Nombre_Apellidos')) if not pd.isna(r.get('Nombre_Apellidos')) else "Admin"
                sede = str(r.get('Sede_Destino')) if not pd.isna(r.get('Sede_Destino')) else "Todas"
                st.markdown(f'<div class="insta-card"><div class="insta-header">📍 {sede} • {autor}</div>', unsafe_allow_html=True)
                if img: st.image(img, use_container_width=True)
                st.markdown(f'<div class="insta-footer"><b>{r.get("Titulo")}</b>: {r.get("Contenido")}<div class="insta-date">{r.get("Fecha_Publicacion")}</div></div></div>', unsafe_allow_html=True)

        elif "Tareas" in menu:
            st.title("✅ Tareas")
            df_t, df_u, df_com = load("Tareas", 5), load("Usuarios", 300), load("Comentarios_Tareas", 5)
            tabs_t = st.tabs(["🆕 Pendientes", "🚧 En Proceso", "✅ Completadas"])
            with tabs_t[0]:
                with st.expander("➕ Crear Nueva Tarea"):
                    with st.form("nt", clear_on_submit=True):
                        tit = st.text_input("Título")
                        dsc = st.text_area("Descripción")
                        fl = st.date_input("Límite", min_value=date.today())
                        if is_admin: lp = df_u['Nombre_Apellidos'].tolist()
                        elif is_encargado:
                            pos = df_u[df_u.apply(lambda r: comparten_sede(u['Sede'], r['Sede']), axis=1)]
                            lp = pos[pos['Roles'].str.contains('Admin|Cocinero|Camarero', na=False, case=False)]['Nombre_Apellidos'].tolist()
                        else:
                            pos = df_u[df_u.apply(lambda r: comparten_sede(u['Sede'], r['Sede']), axis=1)]
                            lp = pos[pos['Roles'].str.contains('Encargado', na=False, case=False)]['Nombre_Apellidos'].tolist()
                        
                        nd = st.selectbox("Asignar:", lp if lp else ["Sin usuarios"])
                        if st.form_submit_button("Crear"):
                            if not tit.strip() or not dsc.strip() or nd == "Sin usuarios" or not nd:
                                st.error("⛔ Rellena Título, Descripción y Asignado.")
                            else:
                                em_d = df_u[df_u['Nombre_Apellidos']==nd]['Email'].values[0]
                                n_r = pd.DataFrame([{"ID_Tarea": str(uuid.uuid4())[:8], "Titulo_Tarea": tit, "Descripción": dsc, "Asignado_A": em_d, "Creado_Por": u['Nombre_Apellidos'], "Sede": u['Sede'], "Estado": "Pendiente", "Fecha_Limite": str(fl)}])
                                conn.update(worksheet="Tareas", data=pd.concat([df_t, n_r], ignore_index=True))
                                enviar_aviso_email(em_d, f"Tarea: {tit}", f"De: {u['Nombre_Apellidos']}\n\n{dsc}"); st.rerun()

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
                                else: status_icon, limite_str = "🟢", f"(📅 {dias_rest} días)"
                            except: pass
                        header_txt = f"{status_icon} **{r['Titulo_Tarea']}** | De: {r['Creado_Por']} ➔ Para: {r.get('Asignado_A', 'N/A')} {limite_str}"
                        with st.expander(header_txt):
                            st.write(f"**Descripción:** {r.get('Descripción', 'Sin detalle')}")
                            st.divider()
                            c_l = df_com[df_com['ID_Tarea'] == r['ID_Tarea']]
                            for _, c in c_l.iterrows():
                                with st.chat_message("user"):
                                    st.write(f"**{c['Nombre_Apellidos']}**")
                                    if "data:image" in str(c['Texto']): st.image(c['Texto'], width=300)
                                    else: st.write(c['Texto'])
                            with st.form(key=f"c_{r['ID_Tarea']}", clear_on_submit=True):
                                mc, fc = st.text_input("Mensaje"), st.file_uploader("📸", type=['jpg','png'], key=f"f_{r['ID_Tarea']}")
                                if st.form_submit_button("Responder"):
                                    val = mc
                                    if fc: val = comprimir_foto(fc)
                                    n_c = pd.DataFrame([{"ID_Tarea": r['ID_Tarea'], "Nombre_Apellidos": u['Nombre_Apellidos'], "Texto": val, "Fecha_Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
                                    conn.update(worksheet="Comentarios_Tareas", data=pd.concat([df_com, n_c], ignore_index=True)); st.rerun()
                            ns = st.selectbox("Estado:", ["Pendiente", "En Proceso", "Completada"], index=["Pendiente", "En Proceso", "Completada"].index(r['Estado']), key=f"s_{r['ID_Tarea']}")
                            if ns != r['Estado']:
                                df_t.at[idx, 'Estado'] = ns; conn.update(worksheet="Tareas", data=df_t); st.rerun()
            draw("Pendiente", tabs_t[0]); draw("En Proceso", tabs_t[1]); draw("Completada", tabs_t[2])

        # --- CHAT ---
        elif "Chat" in menu:
            st.title("💬 Chat Soporte")
            df_chat = load("Chat_Directo", 5)
            df_u_chat = load("Usuarios", 300)
            tm = u['Email']
            if is_admin:
                lc = df_u_chat[~df_u_chat['Roles'].str.contains("Admin")]['Nombre_Apellidos'].tolist()
                tn = st.selectbox("Chat con:", lc)
                tm = df_u_chat[df_u_chat['Nombre_Apellidos']==tn]['Email'].values[0]
            for _, m in df_chat[df_chat['Usuario_Email']==tm].iterrows():
                im = (not is_admin and m['Autor'] == 'Usuario') or (is_admin and m['Autor'] == 'Admin')
                st.markdown(f'<div class="bubble {"bubble-user" if im else "bubble-admin"}">{m["Texto"]}</div>', unsafe_allow_html=True)
            if p := st.chat_input("Escribe..."):
                nm = pd.DataFrame([{"Usuario_Email": tm, "Texto": p, "Fecha_Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Autor": "Admin" if is_admin else "Usuario"}])
                conn.update(worksheet="Chat_Directo", data=pd.concat([df_chat, nm], ignore_index=True))
                enviar_aviso_email(tm, "Nuevo Mensaje Chat", f"Respuesta de Admin: {p}"); st.rerun()

        # --- DOCUMENTOS (MEJORA: CATEGORÍAS EN ADMIN Y USUARIO) ---
        elif "Documentos" in menu:
            st.title("📄 Documentos")
            df_d = load("Documentos", 600)
            
            # --- LÓGICA ADMIN MEJORADA (v34.0) ---
            if is_admin:
                df_u_docs = load("Usuarios", 600)
                # Smart Link
                df_d['NIF_NIE'] = df_d['NIF_NIE'].astype(str).str.strip()
                df_u_docs['NIF_NIE'] = df_u_docs['NIF_NIE'].astype(str).str.strip()
                mapa = dict(zip(df_u_docs['NIF_NIE'], df_u_docs['Nombre_Apellidos']))
                df_d['Nombre_Asignado'] = df_d['NIF_NIE'].map(mapa).fillna("Desconocido")
                df_d['Busqueda_Comb'] = df_d['Nombre_Asignado'] + " (" + df_d['NIF_NIE'] + ")"
                
                lista_opc = sorted(df_d['Busqueda_Comb'].unique().tolist())
                sel_emp = st.selectbox("🔍 Buscar Empleado:", lista_opc, index=None, placeholder="Escribe para buscar...")
                
                dv = df_d[df_d['Busqueda_Comb'] == sel_emp] if sel_emp else df_d
                
                # AÑADIDO: FILTRO DE CATEGORÍA PARA ADMIN
                if not dv.empty and 'Categoria' in dv.columns:
                    cats_d = dv['Categoria'].unique().tolist()
                    if cats_d:
                        sc = st.selectbox("📂 Filtrar Categoría:", ["Todas"] + cats_d)
                        if sc != "Todas": dv = dv[dv['Categoria'] == sc]

            # --- LÓGICA USUARIO NORMAL ---
            else:
                dv = df_d[df_d['NIF_NIE'].astype(str).str.strip() == str(u['NIF_NIE']).strip()]
                # Filtro Categoria
                if not dv.empty and 'Categoria' in dv.columns:
                    cats_d = dv['Categoria'].unique().tolist()
                    if cats_d:
                        sc = st.selectbox("📂 Tipo:", ["Todos"] + cats_d)
                        if sc != "Todos": dv = dv[dv['Categoria'] == sc]
            
            if not dv.empty:
                sel_d = st.selectbox("Elegir Documento:", dv['Nombre Documento'])
                st.components.v1.iframe(f"https://drive.google.com/file/d/{extraer_id_drive(dv[dv['Nombre Documento']==sel_d]['Enlace_Archivo'].values[0])}/preview", height=800)
            else:
                st.info("No hay documentos para mostrar.")

        # --- MANUALES ---
        elif "Manuales" in menu:
            st.title("📚 Manuales")
            df_m = load("Manuales", 600)
            cats = df_m['Categoria'].unique()
            for c in cats:
                with st.expander(f"📂 {c}"):
                    sub = df_m[df_m['Categoria'] == c]
                    for _, r in sub.iterrows():
                        st.write(f"**{r['Nombre_Manual']}**")
                        if st.button("Ver", key=f"m_{r['Nombre_Manual']}"):
                            st.components.v1.iframe(f"https://drive.google.com/file/d/{extraer_id_drive(r['Enlace Drive'])}/preview", height=800)

        # --- FAQs ---
        elif "FAQs" in menu:
            st.title("❓ FAQs")
            df_f = load("FAQ", 600)
            cats = df_f['Categoria'].unique()
            for c in cats:
                with st.expander(f"❓ {c}"):
                    sub = df_f[df_f['Categoria'] == c]
                    for _, r in sub.iterrows():
                        with st.expander(r['Pregunta']): st.write(r['Respuesta'])

except Exception as e:
    reportar_error_a_mario(e)
    st.error("⚠️ Error técnico reportado a Mario.")
    if st.button("Recargar"): st.rerun()
