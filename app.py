from datetime import date

import streamlit as st

from calculo import CAUSALES, UF_REFERENCIA, calcular
from pdf_report import generar_pdf


st.set_page_config(page_title="FiniquitoCL", page_icon="⚖️", layout="wide")

st.markdown(
    """
<style>
.block-container {padding-top: 1.4rem; max-width: 1100px;}
.total-box {
  background: #0f3d2e; color: #f4fff8; border-radius: 16px;
  padding: 1.2rem 1.4rem; margin-top: .4rem;
}
.total-box h2 {margin: 0; font-size: 2rem;}
.total-box p {margin: .2rem 0 0; opacity: .85;}
.stAlert {border-radius: 12px;}
</style>
""",
    unsafe_allow_html=True,
)

st.title("FiniquitoCL")
st.caption("Estimación de finiquito laboral en Chile · Arts. 67, 161, 162, 163 y 172 CT")

with st.sidebar:
    st.subheader("Indicadores")
    valor_uf = st.number_input(
        "Valor UF a usar (CLP)",
        min_value=1.0,
        value=float(UF_REFERENCIA),
        step=1.0,
        help="Por defecto: UF del 22-09-2026. Ajústala al día del pago.",
    )
    st.caption(f"Tope 90 UF ≈ ${int(round(90 * valor_uf)):,}".replace(",", "."))
    st.markdown("---")
    st.markdown(
        "**Monetización sugerida**  \n"
        "Cálculo en pantalla: gratis  \n"
        "PDF con desglose: $2.990"
    )

col1, col2 = st.columns(2)
with col1:
    nombre = st.text_input("Nombre del trabajador (opcional)", placeholder="Ej. Ana Soto")
    ingreso = st.date_input("Fecha de ingreso", value=date(2021, 3, 1))
    termino = st.date_input("Fecha de término", value=date.today())
    causal = st.selectbox(
        "Causal de término",
        options=list(CAUSALES.keys()),
        format_func=lambda k: CAUSALES[k],
    )
with col2:
    remuneracion = st.number_input(
        "Última remuneración mensual (CLP)",
        min_value=0,
        value=800_000,
        step=10_000,
        help="Sueldo + haberes que integran la base del Art. 172.",
    )
    aviso = st.radio(
        "¿Hubo aviso escrito de 30 días? (solo Art. 161)",
        options=[False, True],
        format_func=lambda x: "Sí, hubo aviso" if x else "No hubo aviso",
        horizontal=True,
    )
    vac_pend = st.number_input(
        "Días hábiles de vacaciones pendientes (años anteriores)",
        min_value=0.0,
        value=0.0,
        step=0.5,
    )
    dias_mes = st.number_input(
        "Días trabajados en el mes de término",
        min_value=0,
        max_value=31,
        value=15,
    )

calcular_btn = st.button("Calcular finiquito", type="primary", use_container_width=True)

if calcular_btn or "resultado" in st.session_state:
    try:
        res = calcular(
            ingreso=ingreso,
            termino=termino,
            remuneracion=int(remuneracion),
            causal=causal,
            aviso_30_dias=bool(aviso),
            vacaciones_pendientes=float(vac_pend),
            dias_trabajados_mes=int(dias_mes),
            valor_uf=float(valor_uf),
        )
        st.session_state["resultado"] = res
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    res = st.session_state["resultado"]

    st.markdown(
        f"""
        <div class="total-box">
          <p>Total estimado</p>
          <h2>${res.total:,.0f}</h2>
          <p>Antigüedad {res.anos_exactos} años y {res.meses_fraccion} meses</p>
        </div>
        """.replace(",", "."),
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sueldo del mes", f"${res.sueldo_proporcional:,.0f}".replace(",", "."))
    m2.metric("Feriado", f"${res.feriado:,.0f}".replace(",", "."), f"{res.feriado_total_dias:.2f} días")
    m3.metric("Años de servicio", f"${res.ias:,.0f}".replace(",", "."), f"{res.anos_indemnizables} año(s)")
    m4.metric("Aviso previo", f"${res.aviso:,.0f}".replace(",", "."))

    st.dataframe(
        {
            "Concepto": [
                "Sueldo proporcional",
                "Feriado proporcional + pendiente",
                "Indemnización años de servicio",
                "Aviso previo sustitutivo",
                "Total",
            ],
            "Monto CLP": [
                res.sueldo_proporcional,
                res.feriado,
                res.ias,
                res.aviso,
                res.total,
            ],
        },
        hide_index=True,
        use_container_width=True,
    )

    pdf_bytes = generar_pdf(
        resultado=res,
        nombre=nombre,
        causal=causal,
        ingreso=ingreso,
        termino=termino,
        valor_uf=float(valor_uf),
    )
    st.download_button(
        "Descargar PDF (versión premium del MVP)",
        data=pdf_bytes,
        file_name="finiquitoCL_estimacion.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    with st.expander("Cómo se calculó"):
        for n in res.notas:
            st.write("•", n)

st.info(
    "Esto es una estimación. No es un finiquito legal ni asesoría jurídica. "
    "Contrasta el resultado con la Dirección del Trabajo antes de firmar."
)
