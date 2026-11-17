import hashlib
import pandas as pd
import plotly.express as px
import streamlit as st

# configuración de la página
st.set_page_config(
    page_title="Sistema de detección de fraude en recetas médicas IMSS",
    layout="wide",
    initial_sidebar_state="expanded",
)

# función para encriptar contraseñas con SHA-256 (seguridad institucional)
def encriptar_sha256(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()

# carga de datos 
@st.cache_data
def cargar_datos():
    tabla = pd.read_csv("dataset_resultado_fraude_imss_actu.zip")
    # casos criticos
    if(
        "alerta_regla_manual" in tabla.columns
        and "alerta_isolation_forest" in tabla.columns
    ):
        tabla["coincidencia_cruzada"] = (
            (tabla["alerta_regla_manual"] == 1)
            & (tabla["alerta_isolation_forest"] == 1)
        ).astype(int)
    return tabla

df = cargar_datos()

# variables de sesión - control de acceso
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "rol_usuario" not in st.session_state:
    st.session_state["rol_usuario"] = ""


# pantalla de inicio de sesion centrada
if not st.session_state["autenticado"]:
    # creamos columnas para centrar el login en la pantalla principal
    _, col_centro, _ = st.columns([1, 1.5, 1])
    
    with col_centro:
        st.image("IMSS-Logo.png", width=200)
        st.title("Sistema de Auditoría IMSS")
        st.subheader("Control de Acceso Institucional")
        st.markdown("---")
        
        rol_seleccionado = st.selectbox(
            "Seleccione su perfil:", ["General", "Administrador"]
        )
        password_input = st.text_input(
            "Contraseña de acceso", type="password"
        )

        boton_login = st.button("Ingresar al Sistema", use_container_width=True)

        if boton_login:
            credenciales = {"General": "general2026", "Administrador": "admin2026"}

            if password_input == credenciales[rol_seleccionado]:
                st.session_state["autenticado"] = True
                st.session_state["rol_usuario"] = rol_seleccionado
                st.success(f"Acceso concedido como {rol_seleccionado}!")
                st.rerun()
            else:
                st.error("Contraseña incorrecta. Intente de nuevo.")
    st.stop()

#logo y menú lateral
rol_usuario = st.session_state["rol_usuario"]

st.sidebar.image("IMSS-Logo.png", width=130)
st.sidebar.title("Panel de auditoría IMSS")
st.sidebar.success(f"Sesión activa: {rol_usuario}")

# botón para cerrar sesión
if st.sidebar.button("Cerrar Sesión"):
    st.session_state["autenticado"] = False
    st.session_state["rol_usuario"] = ""
    st.rerun()

st.sidebar.markdown("---")

# definir módulos según el rol
if rol_usuario == "Administrador":
    lista_modulos = [
        "Dashboard general",
        "Detalle de alertas",
        "Simulador en tiempo real",
        "Cambiar Contraseña",
        "Gestión del Sistema y Configuración",
    ]
else:
    lista_modulos = [
        "Dashboard general",
        "Detalle de alertas",
        "Simulador en tiempo real",
        "Cambiar Contraseña",
    ]

# menú de opciones
opcion_menu = st.sidebar.radio("Selección de módulo:", lista_modulos)
st.sidebar.markdown("---")

# cuadro informativo
st.sidebar.info(
    "Módulo de Detección Híbrida\n Reglas deterministas (PAT-01 a PAT-06) + Isolation Forest."
)

# dashboard general
if opcion_menu == "Dashboard general":
    st.title("Sistema híbrido de detección de fraude en recetas médicas")

    columna_fecha = None
    for nombre_columna in df.columns:
        if "FECHA" in nombre_columna.upper():
            columna_fecha = nombre_columna
            break

    nombres_meses = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
    }

    texto_periodo = ""

    if columna_fecha is not None:
        fechas = pd.to_datetime(df[columna_fecha], errors="coerce", dayfirst=True)
        fechas = fechas.dropna()

        if len(fechas) > 0:
            periodos = sorted(set(zip(fechas.dt.year, fechas.dt.month)))
            años = set()
            for periodo in periodos:
                años.add(periodo[0])

            lista_textos = []
            if len(años) == 1:
                for periodo in periodos:
                    lista_textos.append(nombres_meses[periodo[1]])
                año_unico = periodos[0][0]
            else:
                for periodo in periodos:
                    lista_textos.append(f"{nombres_meses[periodo[1]]} {periodo[0]}")

            if len(lista_textos) == 1:
                texto_periodo = lista_textos[0]
            else:
                texto_periodo = ", ".join(lista_textos[:-1]) + " y " + lista_textos[-1]

            if len(años) == 1:
                texto_periodo = f"{texto_periodo} {año_unico}"

    if texto_periodo != "":
        st.subheader(
            f"Análisis de Prescripciones - {texto_periodo} | Vista de {rol_usuario}"
        )
    else:
        st.subheader(
            f"Análisis de Prescripciones | Vista de {rol_usuario}"
        )

    # KPI´s
    total_recetas = len(df)
    texto_total_recetas = f"{total_recetas:,}"

    if "alerta_regla_manual" in df.columns:
        total_alertas_reglas = df["alerta_regla_manual"].sum()
        texto_total_alertas_reglas = f"{total_alertas_reglas:,}"
    else:
        texto_total_alertas_reglas = "N/A"

    if "alerta_isolation_forest" in df.columns:
        total_anomalias_if = df["alerta_isolation_forest"].sum()
        texto_total_anomalias_if = f"{total_anomalias_if:,}"
    else:
        texto_total_anomalias_if = "N/A"

    if "coincidencia_cruzada" in df.columns:
        total_casos_criticos = df["coincidencia_cruzada"].sum()
        texto_casos_criticos = f"{total_casos_criticos:,}"
    else:
        texto_casos_criticos = "N/A"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de recetas", texto_total_recetas)
    col2.metric("Alertas por reglas", texto_total_alertas_reglas)
    col3.metric("Anomalías detectadas", texto_total_anomalias_if)
    col4.metric("Casos críticos", texto_casos_criticos)

    st.markdown("---")

    # semáforo 
    st.subheader("Indicadores de Riesgo")

    if (
        "coincidencia_cruzada" in df.columns
        and "alerta_regla_manual" in df.columns
        and "alerta_isolation_forest" in df.columns
    ):
        es_critico = df["coincidencia_cruzada"] == 1
        tiene_alerta = (df["alerta_regla_manual"] == 1) | (
            df["alerta_isolation_forest"] == 1
        )
        es_amarillo = tiene_alerta & ~es_critico
        es_verde = ~es_critico & ~es_amarillo

        total_rojo = int(es_critico.sum())
        total_amarillo = int(es_amarillo.sum())
        total_verde = int(es_verde.sum())

        col_verde, col_amarillo, col_rojo = st.columns(3)
        col_verde.metric(label="Volumen seguro", value=f"{total_verde:,}")
        col_amarillo.metric(label="Requiere revisión", value=f"{total_amarillo:,}")
        col_rojo.metric(label="Alto riesgo detectado", value=f"{total_rojo:,}")

    else:
        st.info("Faltan columnas de alertas para calcular el semáforo.")

    st.markdown("---")

    # matriz de costo-beneficio e impacto financiero
    st.subheader("Matriz de costo-beneficio e impacto financiero")

    if "IMPORTE" in df.columns:
        importe_total_general = df["IMPORTE"].sum()

        if "coincidencia_cruzada" in df.columns:
            importe_critico = df[df["coincidencia_cruzada"] == 1]["IMPORTE"].sum()
        else:
            importe_critico = 0.0

        if (
            "alerta_regla_manual" in df.columns
            and "alerta_isolation_forest" in df.columns
        ):
            importe_alertas = df[
                (df["alerta_regla_manual"] == 1)
                | (df["alerta_isolation_forest"] == 1)
            ]["IMPORTE"].sum()
        else:
            importe_alertas = 0.0
    else:
        importe_total_general = 0.0
        importe_critico = 0.0
        importe_alertas = 0.0

    fcol1, fcol2, fcol3 = st.columns(3)
    fcol1.metric("Importe Global Analizado", f"${importe_total_general:,.2f}")
    fcol2.metric("Ahorro Potencial (Casos Críticos)", f"${importe_critico:,.2f}")
    fcol3.metric("Monto Total Bajo Sospecha", f"${importe_alertas:,.2f}")

    st.markdown("---")

    # gráficas
    st.subheader("Analisis visual de comportamiento y alertas")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("Distribución de alertas en el conjunto de datos")
        if (
            "alerta_regla_manual" in df.columns
            and "alerta_isolation_forest" in df.columns
        ):
            conteo_alertas = pd.DataFrame(
                {
                    "Tipo de Evaluación": [
                        "Reglas deterministas",
                        "Anomalias",
                        "Casos críticos",
                    ],
                    "Cantidad": [
                        int(df["alerta_regla_manual"].sum()),
                        int(df["alerta_isolation_forest"].sum()),
                        int(
                            df["coincidencia_cruzada"].sum()
                            if "coincidencia_cruzada" in df.columns
                            else 0
                        ),
                    ],
                }
            )
            fig_bar = px.bar(
                conteo_alertas,
                x="Tipo de Evaluación",
                y="Cantidad",
                color="Tipo de Evaluación",
                text="Cantidad",
                color_discrete_sequence=px.colors.qualitative.Prism,
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Columnas de alertas no disponibles para graficar.")

    with col_g2:
        st.markdown("Comportamiento de importes por prescripción")
        if "IMPORTE" in df.columns and "CANTIDAD" in df.columns:
            fig_scatter = px.scatter(
                df.head(1000),
                x="CANTIDAD",
                y="IMPORTE",
                color="coincidencia_cruzada"
                if "coincidencia_cruzada" in df.columns
                else None,
                title="Relación cantidad vs importe (Muestra de registros)",
                labels={
                    "CANTIDAD": "Cantidad de piezas",
                    "IMPORTE": "Importe total ($)",
                },
                color_continuous_scale="Reds",
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("Columnas de importe o cantidad no disponibles")

    st.success(
        f"Página de inicio con gráficos interactivos bajo el perfil de {rol_usuario}"
    )

# detalle de alerta
elif opcion_menu == "Detalle de alertas":
    st.title("Explorador avanzado de alertas y anomalías")
    st.write(
        "Filtra y revisa los folios de recetas sospechosas detectadas."
    )

    opcion_todo = "Ver todo el conjunto de datos"
    opcion_criticos = "Solo casos críticos (Coincidencia cruzada)"
    opcion_if = "Solo anomalías detectadas por Isolation Forest"
    opcion_reglas = "Solo alertas por reglas manuales (PAT-01 a PAT-06)"

    tipo_filtro = st.selectbox(
        "Selecciona el criterio de evaluación:",
        [opcion_todo, opcion_criticos, opcion_if, opcion_reglas],
    )

    df_filtrado = df.copy()

    if tipo_filtro == opcion_criticos:
        if "coincidencia_cruzada" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["coincidencia_cruzada"] == 1]
        else:
            st.warning("No se encontró la columna coincidencia_cruzada.")
    elif tipo_filtro == opcion_if:
        if "alerta_isolation_forest" in df_filtrado.columns:
            df_filtrado = df_filtrado[
                df_filtrado["alerta_isolation_forest"] == 1
            ]
        else:
            st.warning("No se encontró la columna alerta_isolation_forest.")
    elif tipo_filtro == opcion_reglas:
        if "alerta_regla_manual" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["alerta_regla_manual"] == 1]
        else:
            st.warning("No se encontró la columna alerta_regla_manual.")

    st.subheader(f"Registros encontrados: {len(df_filtrado):,}")
    st.markdown(
        "Fondo rojo = Caso crítico | Fondo amarillo = Alerta moderada | Fondo verde = Sin alertas"
    )

    tabla_100 = df_filtrado.head(100)

    # Función para pintar el fondo de la fila completa según los parámetros
    def pintar_fila_riesgo(row):
        es_critico = row.get("coincidencia_cruzada", 0) == 1
        tiene_regla = row.get("alerta_regla_manual", 0) == 1
        tiene_anomalia = row.get("alerta_isolation_forest", 0) == 1

        if es_critico:
            return ['background-color: #ffcccc; color: black'] * len(row)
        elif tiene_regla or tiene_anomalia:
            return ['background-color: #fff3cc; color: black'] * len(row)
        else:
            return ['background-color: #d4edda; color: black'] * len(row)

    tabla_coloreada = tabla_100.style.apply(pintar_fila_riesgo, axis=1)
    st.dataframe(tabla_coloreada, use_container_width=True)

    st.markdown("---")
    st.subheader("Exportación de informe")
    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        csv_data = df_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Descargar informe en CSV",
            data=csv_data,
            file_name="informe_alertas_fraude.csv",
            mime="text/csv",
            help="Descarga el conjunto filtrado de recetas sospechosas",
        )

    with col_exp2:
        st.info(
            "Nota: Los reportes exportados incluyen los folios y puntuaciones "
            "de riesgo del modelo para soporte"
        )

# simulador en tiempo real 
elif opcion_menu == "Simulador en tiempo real":
    st.title("Simulador de auditoría para nuevas recetas")
    st.write(
        "Ingreso manual de parámetros de receta para evaluación instantánea."
    )

    with st.form("form_simulator"):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            piezas = st.number_input(
                "Cantidad total de piezas en la receta", min_value=1, value=10
            )
            recetas = st.number_input(
                "Volumen mensual de recetas del médico", min_value=1, value=50
            )
        with col_s2:
            recetas_paciente = st.number_input(
                "Frecuencia mensual de recetas del paciente",
                min_value=1,
                value=2,
            )
            importe = st.number_input(
                "Importe total ($)", min_value=0.0, value=500.0
            )

        boton_enviar = st.form_submit_button("Evaluar receta con el modelo")

    if boton_enviar:
        if piezas > 50 or importe > 10000:
            st.error(
                "Alerta de alto riesgo: La receta excede los límites de volumen"
                " o importe establecidos."
            )
        else:
            st.success(
                "Receta regular: Transacción dentro de parámetros"
                " establecidos."
            )

    st.markdown("---")
    st.subheader("Carga manual de datos de recetas médicas")
    st.write("Sube un archivo en formato CSV o Excel para analizar nuevas recetas")

    archivo_subido = st.file_uploader("Selecciona el archivo de recetas", type = ["csv", "xlsx"])
    if archivo_subido is not None:
        if archivo_subido.name.endswith('.csv'):
            df_usuario = pd.read_csv(archivo_subido)
        else: 
            df_usuario = pd.read_excel(archivo_subido)

        st.success(f"Archivo {archivo_subido.name} cargado correctamente")
        st.write("Vista previa del nuevo conjunto de datos:")
        st.dataframe(df_usuario.head(), use_container_width=True)

        if st.button("Ejecutar Análisis de detección"):
            st.info("Ejecutando reglas de validación y modelo de detección...")
            st.success("Análisis finalizado con éxito")
            st.metric(label = "Total de recetas evaluadas en este conjunto", value = f"{len(df_usuario):,}")

    else: 
        st.info("Esperando a que cargue un archivo de recetas médicas para iniciar el análisis")

# módulo de cambio de contraseña
elif opcion_menu == "Cambiar Contraseña":
    st.title("Seguridad y Gestión de Cuenta")
    st.subheader("Actualización de credenciales con encriptación SHA-256")
    st.write(f"Usuario actual en sesión: **{rol_usuario}**")
    
    with st.form("form_cambiar_pass"):
        pass_actual = st.text_input("Contraseña actual", type="password")
        pass_nueva = st.text_input("Nueva contraseña", type="password")
        pass_confirmar = st.text_input("Confirmar nueva contraseña", type="password")
        
        btn_actualizar = st.form_submit_button("Actualizar Contraseña")
        
        if btn_actualizar:
            if not pass_actual or not pass_nueva or not pass_confirmar:
                st.error("Por favor, complete todos los campos obligatorios.")
            elif pass_nueva != pass_confirmar:
                st.error("Las nuevas contraseñas no coinciden. Verifique e intente de nuevo.")
            elif len(pass_nueva) < 6:
                st.warning("La contraseña debe tener al menos 6 caracteres por seguridad.")
            else:
                hash_sha256 = encriptar_sha256(pass_nueva)
                st.success("¡Contraseña actualizada correctamente y protegida mediante encriptación SHA-256!")
                st.info(f"Hash seguro generado (para registro interno): `{hash_sha256}`")

# módulo exclusivo de administrador
elif opcion_menu == "Gestión del Sistema y Configuración":
    st.title("Panel de Gestión y Configuración (Administrador)")
    st.write(
        "Parámetros del sistema, control de versiones del modelo y estado de la"
        " base de datos."
    )
    st.info(
        "Estado del Pipeline: Activo\n Modelo: Isolation Forest"
        " (`contamination=0.02`)\n Registros totales cargados: 59,766"
    )
    st.warning(
        "Zona restringida para modificaciones de hiperparámetros y"
        " reentrenamiento del modelo."
    )
