"""Reglas simplificadas del finiquito en Chile (estimación educativa)."""

from __future__ import annotations

from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
from datetime import date

UF_REFERENCIA = 40_991.75  # 22-sep-2026
TOPE_UF_MENSUAL = 90
TOPE_ANOS = 11
DIAS_FERIADO_ANUAL = 15
FACTOR_MES = DIAS_FERIADO_ANUAL / 12  # 1.25


CAUSALES = {
    "art161": "Despido Art. 161 — necesidades de la empresa / desahucio",
    "renuncia": "Renuncia voluntaria",
    "mutuo": "Mutuo acuerdo (Art. 159 N°1)",
    "plazo": "Vencimiento de plazo o obra (Art. 159)",
    "art160": "Despido Art. 160 — causal imputable al trabajador",
}


@dataclass
class Resultado:
    anos_exactos: int
    meses_fraccion: int
    anos_indemnizables: int
    remuneracion_base: int
    remuneracion_topeada: int
    tope_90_uf: int
    aplica_ias: bool
    aplica_aviso: bool
    ias: int
    aviso: int
    feriado_prop_dias: float
    feriado_pend_dias: float
    feriado_total_dias: float
    feriado: int
    dias_mes: int
    sueldo_proporcional: int
    total: int
    notas: list[str]


def _anos_servicio(ingreso: date, termino: date) -> tuple[int, int, int]:
    if termino < ingreso:
        raise ValueError("La fecha de término no puede ser anterior al ingreso.")
    delta = relativedelta(termino, ingreso)
    anos = delta.years
    meses = delta.months
    extra = 1 if meses > 6 or (meses == 6 and delta.days > 0) else 0
    indemnizables = min(anos + extra, TOPE_ANOS)
    return anos, meses, indemnizables


def _meses_desde_aniversario(ingreso: date, termino: date) -> float:
    """Meses (con fracción de 30 días) desde el último aniversario o ingreso."""
    aniv = date(termino.year, ingreso.month, min(ingreso.day, 28))
    if aniv > termino:
        aniv = date(termino.year - 1, ingreso.month, min(ingreso.day, 28))
    if aniv < ingreso:
        aniv = ingreso
    delta = relativedelta(termino, aniv)
    return delta.months + delta.days / 30.0


def calcular(
    ingreso: date,
    termino: date,
    remuneracion: int,
    causal: str,
    aviso_30_dias: bool,
    vacaciones_pendientes: float,
    dias_trabajados_mes: int,
    valor_uf: float = UF_REFERENCIA,
) -> Resultado:
    anos, meses, indemnizables = _anos_servicio(ingreso, termino)
    tope_pesos = int(round(TOPE_UF_MENSUAL * valor_uf))
    base_topeada = min(int(remuneracion), tope_pesos)
    valor_dia = remuneracion / 30.0

    aplica_ias = causal == "art161" and indemnizables >= 1
    aplica_aviso = causal == "art161" and not aviso_30_dias

    ias = base_topeada * indemnizables if aplica_ias else 0
    aviso = base_topeada if aplica_aviso else 0

    meses_prop = max(0.0, _meses_desde_aniversario(ingreso, termino))
    feriado_prop_dias = round(meses_prop * FACTOR_MES, 2)
    feriado_pend = max(0.0, float(vacaciones_pendientes))
    feriado_dias = feriado_prop_dias + feriado_pend
    feriado = int(round(feriado_dias * valor_dia))

    dias_mes = max(0, min(31, int(dias_trabajados_mes)))
    sueldo_prop = int(round(valor_dia * dias_mes))

    total = ias + aviso + feriado + sueldo_prop

    notas = [
        "Estimación educativa. No reemplaza asesoría de un abogado o la DT.",
        f"Tope Art. 172: 90 UF = ${tope_pesos:,}".replace(",", "."),
        "IAS y aviso usan la remuneración topeada. El feriado y el sueldo del mes usan la remuneración informada.",
        "Feriado proporcional: 1,25 días hábiles por mes desde el último aniversario (Art. 67/73). No convierte a días corridos.",
    ]
    if causal != "art161":
        notas.append("Esta causal no activa indemnización por años de servicio ni aviso previo.")
    if aplica_ias and anos + (1 if meses > 6 else 0) > TOPE_ANOS:
        notas.append("Se aplicó el tope legal de 11 años.")
    if remuneracion > tope_pesos:
        notas.append("La remuneración supera 90 UF: IAS y aviso se calcularon con el tope.")

    return Resultado(
        anos_exactos=anos,
        meses_fraccion=meses,
        anos_indemnizables=indemnizables if aplica_ias else 0,
        remuneracion_base=int(remuneracion),
        remuneracion_topeada=base_topeada,
        tope_90_uf=tope_pesos,
        aplica_ias=aplica_ias,
        aplica_aviso=aplica_aviso,
        ias=ias,
        aviso=aviso,
        feriado_prop_dias=feriado_prop_dias,
        feriado_pend_dias=feriado_pend,
        feriado_total_dias=feriado_dias,
        feriado=feriado,
        dias_mes=dias_mes,
        sueldo_proporcional=sueldo_prop,
        total=total,
        notas=notas,
    )
