"""
¿Crecieron 4 % las ventas entre 2024 y 2025?
Presentación académica e interactiva basada en la sección 9.3 del notebook regresion.ipynb

Ejecutar desde esta carpeta:
    streamlit run app.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="¿Crecimos 4 %?", page_icon="📈", layout="wide")

# ---------------------------------------------------------------------------
# Estilo
# ---------------------------------------------------------------------------
AZUL, NARANJA, AQUA, VIOLETA, GRIS = "#2a78d6", "#eb6834", "#1baf7a", "#6250d6", "#8a8984"
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

st.markdown("""
<style>
.block-container {padding-top: 1.6rem; max-width: 1200px;}
.caja {border-left: 5px solid #2a78d6; background: rgba(42,120,214,.08);
       padding: .85rem 1.1rem; border-radius: 6px; margin: .5rem 0 1rem 0;}
.alerta {border-left: 5px solid #eb6834; background: rgba(235,104,52,.08);
         padding: .85rem 1.1rem; border-radius: 6px; margin: .5rem 0 1rem 0;}
.veredicto {border: 2px solid rgba(128,128,128,.35); border-radius: 10px;
            padding: 1.1rem 1.3rem; margin: .6rem 0 1.2rem 0;}
.etiqueta {font-size: .78rem; letter-spacing: .09em; text-transform: uppercase; opacity: .65;}
.heroe {font-size: 3.4rem; font-weight: 700; line-height: 1.05;}
</style>
""", unsafe_allow_html=True)


def caja(txt, tipo="caja"):
    icono = "💡" if tipo == "caja" else "⚠️"
    st.markdown(f'<div class="{tipo}">{icono} {txt}</div>', unsafe_allow_html=True)


def estilo(fig, alto=380, titulo=None, leyenda=True):
    fig.update_layout(height=alto, title=titulo, showlegend=leyenda,
                      margin=dict(l=10, r=10, t=55 if titulo else 20, b=10),
                      legend=dict(orientation="h", y=1.1, x=0), hoverlabel=dict(font_size=13),
                      plot_bgcolor="rgba(0,0,0,0)")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,.15)", zerolinecolor="rgba(128,128,128,.5)")
    return fig


def p(x, signo=True):
    return f"{x:+.1f} %" if signo else f"{x:.1f} %"


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
@st.cache_data
def cargar():
    aqui = Path(__file__).parent
    for ruta in [aqui / "ventas_mensuales.csv", aqui.parent / "ventas_mensuales.csv"]:
        if ruta.exists():
            df = pd.read_csv(ruta, encoding="utf-8")
            break
    else:
        st.error("No encuentro `ventas_mensuales.csv` ni en esta carpeta ni en la carpeta superior.")
        st.stop()
    df["periodo"] = pd.to_datetime(df["periodo"], format="%Y-%m")

    meses_s = df.groupby("sucursal")["periodo"].nunique()
    apertura = df.groupby("sucursal")["periodo"].min()

    def tipo(s):
        if meses_s[s] == 24:
            return "Estables (24 meses)"
        return "Abrieron en 2024" if apertura[s].year == 2024 else "Abrieron en 2025"

    df["grupo"] = df["sucursal"].map({s: tipo(s) for s in meses_s.index})
    return df


df = cargar()
EST = df[df["grupo"] == "Estables (24 meses)"]
ORDEN_GRUPOS = ["Estables (24 meses)", "Abrieron en 2024", "Abrieron en 2025"]


def g(d, m):
    """Tasa de crecimiento 2025 vs 2024 (%) de la métrica m."""
    v = d.groupby("anio")[m].sum()
    return (v.get(2025, 0) / v.get(2024, np.nan) - 1) * 100


# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------
META = 4.0      # crecimiento a validar (%)

with st.sidebar:
    st.markdown("### 📈 ¿Crecimos 4 %?")
    pagina = st.radio("Sección", ["🏠 Pregunta y método", "💵 1. Ventas en dinero",
                                  "📦 2. Unidades vendidas"], label_visibility="collapsed")
    st.divider()
    st.caption(f"Base: `ventas_mensuales.csv` · {len(df):,} filas · "
               f"{df['sucursal'].nunique()} sucursales · {df['producto'].nunique()} productos · "
               f"ene-2024 a dic-2025")


# ---------------------------------------------------------------------------
# Bloques reutilizables (misma lógica para ventas y unidades)
# ---------------------------------------------------------------------------
def kpis(m, unidad):
    t = df.groupby("anio")[m].sum()
    gt = g(df, m)
    fmt = (lambda x: f"${x/1e6:,.2f} M") if m == "ventas" else (lambda x: f"{x/1e3:,.1f} mil")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("2024", fmt(t[2024]))
    c2.metric("2025", fmt(t[2025]))
    c3.metric("Crecimiento total", p(gt))
    c4.metric(f"Brecha vs meta {META:.1f} %", f"{gt - META:+.1f} p.p.",
              delta="cumple" if abs(gt - META) <= 0.5 else ("por encima" if gt > META else "por debajo"),
              delta_color="off")
    return gt


def grafico_mensual(m, etiqueta):
    piv = df.pivot_table(index="mes", columns="anio", values=m, aggfunc="sum")
    yoy = (piv[2025] / piv[2024] - 1) * 100
    c1, c2 = st.columns([1.15, 1])
    fig = go.Figure()
    for anio, col in [(2024, AZUL), (2025, NARANJA)]:
        fig.add_scatter(x=MESES, y=piv[anio], name=str(anio), mode="lines+markers",
                        line=dict(color=col, width=2.5), marker=dict(size=8),
                        hovertemplate="%{x}: %{y:,.0f}<extra>" + str(anio) + "</extra>")
    c1.plotly_chart(estilo(fig, 360, f"{etiqueta} por mes: 2024 vs 2025"), width="stretch")

    fig = go.Figure(go.Bar(x=MESES, y=yoy, marker_color=[AZUL if v >= 0 else NARANJA for v in yoy],
                           text=[f"{v:+.0f}" for v in yoy], textposition="outside",
                           hovertemplate="%{x}: %{y:+.1f} %<extra></extra>"))
    fig.add_hline(y=META, line_dash="dash", line_color=GRIS,
                  annotation_text=f"meta {META:.1f} %", annotation_position="top left")
    c2.plotly_chart(estilo(fig, 360, "Crecimiento de cada mes vs mismo mes 2024 (%)", False),
                    width="stretch")
    return yoy


def bloque_origen(m):
    tot24 = df[df["anio"] == 2024][m].sum()
    c = df.pivot_table(index="grupo", columns="anio", values=m, aggfunc="sum").fillna(0).reindex(ORDEN_GRUPOS)
    c["sucursales"] = df.groupby("grupo")["sucursal"].nunique()
    c["contribución (p.p.)"] = (c[2025] - c[2024]) / tot24 * 100
    c["crecimiento propio %"] = (c[2025] / c[2024].replace(0, np.nan) - 1) * 100

    col1, col2 = st, st
    fig = go.Figure(go.Waterfall(
        x=["Estables", "Abrieron 2024", "Abrieron 2025", "TOTAL"],
        measure=["relative"] * 3 + ["total"],
        y=list(c["contribución (p.p.)"]) + [0],
        text=[f"{v:+.1f}" for v in c["contribución (p.p.)"]] + [f"{c['contribución (p.p.)'].sum():.1f} %"],
        textposition="outside",
        increasing=dict(marker=dict(color=AZUL)), decreasing=dict(marker=dict(color=NARANJA)),
        totals=dict(marker=dict(color=GRIS)), connector=dict(line=dict(color="rgba(128,128,128,.4)"))))
    fig.add_hline(y=META, line_dash="dash", line_color=VIOLETA,
                  annotation_text=f"meta {META:.1f} %", annotation_position="top left")
    col1.plotly_chart(estilo(fig, 340, "Contribución al crecimiento por tipo de sucursal (p.p.)", False),
                      width="stretch")
    tabla = c.rename(columns={2024: "2024", 2025: "2025"})
    col2.dataframe(tabla.style.format({"2024": "{:,.0f}", "2025": "{:,.0f}", "sucursales": "{:.0f}",
                                       "contribución (p.p.)": "{:+.2f}", "crecimiento propio %": "{:+.1f}"},
                                      na_rep="— (no existían)"), width="stretch")
    col2.latex(r"\text{Contribución}_g=\frac{Y_{g,2025}-Y_{g,2024}}{Y_{\text{total},2024}}\times 100")
    return c


def bloque_lfl(m):
    sin10 = lambda d: d[d["producto"] != "P10"]
    filas = {
        "Total empresa": (g(df, m), g(sin10(df), m)),
        "LFL (126 estables)": (g(EST, m), g(sin10(EST), m)),
        "LFL Region_A": (g(EST[EST.region == "Region_A"], m), g(sin10(EST[EST.region == "Region_A"]), m)),
        "LFL Region_B": (g(EST[EST.region == "Region_B"], m), g(sin10(EST[EST.region == "Region_B"]), m)),
    }
    t = pd.DataFrame(filas, index=["con P10", "sin P10"]).T
    fig = go.Figure()
    for col, color in [("con P10", AZUL), ("sin P10", NARANJA)]:
        fig.add_bar(x=t.index, y=t[col], name=col, marker_color=color,
                    text=[f"{v:+.1f}" for v in t[col]], textposition="outside",
                    hovertemplate="%{x}<br>%{y:+.2f} %<extra>" + col + "</extra>")
    fig.add_hline(y=META, line_dash="dash", line_color=GRIS,
                  annotation_text=f"meta {META:.1f} %", annotation_position="top left")
    fig.update_layout(barmode="group", bargap=.3)
    st.plotly_chart(estilo(fig, 380, "Crecimiento según la base de comparación (%)"), width="stretch")
    return t


# ---------------------------------------------------------------------------
# PÁGINA 0: Pregunta y método
# ---------------------------------------------------------------------------
if pagina.startswith("🏠"):
    st.markdown('<div class="etiqueta">Análisis de crecimiento · 2024 → 2025</div>', unsafe_allow_html=True)
    st.title(f"¿Crecieron realmente las ventas un {META:.0f} %?")
    st.markdown("""
La pregunta parece tener una sola respuesta, pero **"crecimiento" no es un número único**: depende de
**qué** se mide (dinero o unidades), **sobre qué base** (todas las tiendas o tiendas iguales) y
**cómo** se agrega. Esta presentación valida la hipótesis en dos dimensiones:
""")
    c1, c2 = st.columns(2)
    c1.markdown(f'<div class="veredicto"><div class="etiqueta">Sección 1</div><h3>💵 Ventas en dinero</h3>'
                f'Monto facturado neto de descuento.<br><div class="heroe">{p(g(df, "ventas"))}</div></div>',
                unsafe_allow_html=True)
    c2.markdown(f'<div class="veredicto"><div class="etiqueta">Sección 2</div><h3>📦 Unidades vendidas</h3>'
                f'Volumen físico (columna <code>cantidad</code>).<br><div class="heroe">{p(g(df, "cantidad"))}</div></div>',
                unsafe_allow_html=True)

    st.subheader("Datos")
    st.markdown(f"""
- Panel **sucursal × producto × mes**, enero 2024 – diciembre 2025 ({len(df):,} observaciones).
- {df['sucursal'].nunique()} sucursales en 2 regiones, {df['producto'].nunique()} productos en {df['categoria'].nunique()} categorías terapéuticas.
- Identidad contable verificada en el EDA:
""")
    st.latex(r"\text{ventas}_{ipt} = \text{cantidad}_{ipt}\times \text{precio}_{p}\times(1-\text{descuento}_{ipt})")

    st.subheader("Método")
    st.markdown("Tasa de crecimiento anual, válida porque ambos años tienen los 12 meses completos:")
    st.latex(r"g = \left(\frac{Y_{2025}}{Y_{2024}} - 1\right)\times 100")
    st.markdown("""
| Paso | Qué se hace | Por qué |
|---|---|---|
| 1 | Crecimiento total y mes a mes (YoY) | Punto de partida y volatilidad |
| 2 | Descomposición por **tipo de sucursal** (aditiva, en p.p.) | Separar **expansión** de crecimiento **orgánico** |
| 3 | **Like-for-like (LFL)**: solo tiendas abiertas los 24 meses, con y sin **P10** | Estándar del retail; aísla el producto retirado en jul-2025 |
| 4 | Mecanismo: volumen–mezcla–descuento / unidades × precio medio | Entender **por qué** crece |
""")
    caja("Usa el menú lateral para avanzar entre las dos secciones.")

# ---------------------------------------------------------------------------
# PÁGINA 1: Ventas
# ---------------------------------------------------------------------------
elif pagina.startswith("💵"):
    st.markdown('<div class="etiqueta">Sección 1</div>', unsafe_allow_html=True)
    st.title("💵 Ventas en dinero")
    gt = kpis("ventas", "$")
    tabs = st.tabs(["1 · Panorama", "2 · ¿De dónde viene?", "3 · Tiendas iguales", "4 · Mecanismo"])

    with tabs[0]:
        yoy = grafico_mensual("ventas", "Ventas ($)")
        sem = df.assign(s=np.where(df.mes <= 6, "1.er semestre", "2.º semestre")).groupby("s").apply(
            lambda d: g(d, "ventas"), include_groups=False)
        caja(f"Las ventas crecieron <b>{gt:.1f} %</b>, pero no de forma pareja: <b>{sem.iloc[0]:.1f} %</b> en el primer "
             f"semestre y <b>{sem.iloc[1]:.1f} %</b> en el segundo. Los crecimientos mensuales van de "
             f"<b>{yoy.min():+.0f} %</b> a <b>{yoy.max():+.0f} %</b>: su promedio ({yoy.mean():.1f} %) no es la "
             f"tasa anual, porque <i>el promedio de porcentajes no es el porcentaje del total</i>.")

    with tabs[1]:
        c = bloque_origen("ventas")
        exp = c["contribución (p.p.)"].iloc[1:].sum()
        caja(f"De los {gt:.1f} p.p., <b>{exp:.1f} p.p. ({exp/gt*100:.0f} %)</b> vienen de sucursales nuevas. "
             f"Las 126 tiendas estables aportan solo <b>{c['contribución (p.p.)'].iloc[0]:.1f} p.p.</b> "
             "El crecimiento es sobre todo <b>expansión</b>, no tiendas que vendan más.")

    with tabs[2]:
        t = bloque_lfl("ventas")
        caja(f"A tiendas iguales el crecimiento <b>orgánico</b> es {t.loc['LFL (126 estables)', 'con P10']:.1f} %. "
             f"Sin el producto retirado P10 sube a <b>{t.loc['LFL (126 estables)', 'sin P10']:.1f} %</b>, muy cerca de la meta. "
             f"Las regiones divergen: Region_B {t.loc['LFL Region_B', 'con P10']:+.1f} % vs Region_A "
             f"{t.loc['LFL Region_A', 'con P10']:+.1f} % (P10 solo se vendía en A).")

    with tabs[3]:
        st.markdown("Como el **precio de lista de cada producto no cambió**, el crecimiento LFL se reparte en tres efectos:")
        st.latex(r"\Delta V = \underbrace{V_{24}\left(\tfrac{Q_{25}}{Q_{24}}-1\right)}_{\text{volumen}}"
                 r"+\underbrace{\left(\textstyle\sum_p q_{p,25}\,\bar p_{p,24}-V_{24}-\text{vol}\right)}_{\text{mezcla}}"
                 r"+\underbrace{\left(V_{25}-\textstyle\sum_p q_{p,25}\,\bar p_{p,24}\right)}_{\text{descuento}}")
        gp = EST.groupby(["producto", "anio"]).agg(u=("cantidad", "sum"), v=("ventas", "sum")).unstack("anio").fillna(0)
        u24, u25, v24, v25 = gp["u"][2024], gp["u"][2025], gp["v"][2024], gp["v"][2025]
        vol = v24.sum() * (u25.sum() / u24.sum() - 1)
        a_p24 = (u25 * (v24 / u24)).sum()
        mez = a_p24 - v24.sum() - vol
        des = v25.sum() - a_p24
        ef = pd.Series({"Volumen": vol, "Mezcla": mez, "Descuento": des}) / v24.sum() * 100

        c1, c2 = st.columns(2)
        fig = go.Figure(go.Waterfall(x=list(ef.index) + ["LFL"], measure=["relative"] * 3 + ["total"],
                                     y=list(ef) + [0], text=[f"{v:+.2f}" for v in ef] + [f"{ef.sum():.2f} %"],
                                     textposition="outside", increasing=dict(marker=dict(color=AZUL)),
                                     decreasing=dict(marker=dict(color=NARANJA)), totals=dict(marker=dict(color=GRIS))))
        c1.plotly_chart(estilo(fig, 360, "Descomposición del crecimiento LFL (p.p.)", False), width="stretch")
        aporte = ((v25 - v24) / v24.sum() * 100).sort_values()
        fig = go.Figure(go.Bar(x=aporte.values, y=aporte.index, orientation="h",
                               marker_color=[AZUL if v >= 0 else NARANJA for v in aporte],
                               hovertemplate="%{y}: %{x:+.2f} p.p.<extra></extra>"))
        c2.plotly_chart(estilo(fig, 360, "Aporte de cada producto (p.p. del LFL)", False), width="stretch")
        caja(f"Las tiendas estables vendieron casi las mismas unidades (volumen {ef['Volumen']:+.1f} p.p.); "
             f"el crecimiento viene de la <b>mezcla</b> ({ef['Mezcla']:+.1f} p.p.): más productos caros, liderados por "
             f"<b>{aporte.idxmax()}</b>. Algo más de descuento restó {ef['Descuento']:.1f} p.p.")

# ---------------------------------------------------------------------------
# PÁGINA 2: Unidades
# ---------------------------------------------------------------------------
else:
    st.markdown('<div class="etiqueta">Sección 2</div>', unsafe_allow_html=True)
    st.title("📦 Unidades vendidas")
    gt = kpis("cantidad", "u")
    tabs = st.tabs(["1 · Panorama", "2 · ¿De dónde viene?", "3 · Tiendas iguales", "4 · Dinero = unidades × precio"])

    with tabs[0]:
        yoy = grafico_mensual("cantidad", "Unidades")
        caja(f"En volumen físico la empresa creció <b>{gt:.1f} %</b> ({gt - META:+.1f} p.p. frente a la meta de "
             f"{META:.1f} %). Igual que en dinero, el mes a mes es volátil "
             f"(de {yoy.min():+.0f} % a {yoy.max():+.0f} %).")

    with tabs[1]:
        c = bloque_origen("cantidad")
        exp = c["contribución (p.p.)"].iloc[1:].sum()
        caja(f"En unidades la dependencia de la expansión es aún mayor: las tiendas nuevas aportan "
             f"<b>{exp:.1f} de {gt:.1f} p.p.</b> y las estables apenas <b>{c['contribución (p.p.)'].iloc[0]:+.1f} p.p.</b>")

    with tabs[2]:
        t = bloque_lfl("cantidad")
        caja(f"Las mismas tiendas vendieron prácticamente las mismas unidades (LFL "
             f"<b>{t.loc['LFL (126 estables)', 'con P10']:+.1f} %</b>). Sin P10 el LFL sube a "
             f"<b>{t.loc['LFL (126 estables)', 'sin P10']:+.1f} %</b>: el retiro de P10 explica casi toda la diferencia. "
             f"Region_A cae {t.loc['LFL Region_A', 'con P10']:.1f} % en unidades.")
        p10 = df[df.producto == "P10"].groupby("periodo")["cantidad"].sum()
        fig = go.Figure(go.Scatter(x=p10.index, y=p10.values, mode="lines+markers", line=dict(color=NARANJA, width=2.5),
                                   marker=dict(size=7), hovertemplate="%{x|%b %Y}: %{y:,.0f} u<extra></extra>"))
        st.plotly_chart(estilo(fig, 280, "Unidades de P10 por mes: el producto desaparece en jul-2025", False),
                        width="stretch")

    with tabs[3]:
        st.markdown("Las ventas en dinero son unidades por el precio neto promedio por unidad, así que los "
                    "crecimientos se **multiplican**:")
        st.latex(r"V = Q\cdot\bar P \quad\Rightarrow\quad (1+g_V) = (1+g_Q)(1+g_{\bar P})")
        v = df.groupby("anio")["ventas"].sum()
        q = df.groupby("anio")["cantidad"].sum()
        pm = v / q
        gV, gQ, gP = (v[2025] / v[2024] - 1), (q[2025] / q[2024] - 1), (pm[2025] / pm[2024] - 1)
        c1, c2, c3 = st.columns(3)
        c1.metric("Unidades (g_Q)", p(gQ * 100))
        c2.metric("Precio neto medio (g_P)", p(gP * 100))
        c3.metric("Ventas (g_V)", p(gV * 100))
        st.latex(r"(1+%.4f)\times(1+%.4f) = %.4f \;\Rightarrow\; %+.2f\%%" % (gQ, gP, (1 + gQ) * (1 + gP), gV * 100))

        cat = EST.pivot_table(index="categoria", columns="anio", values="cantidad", aggfunc="sum")
        ap = ((cat[2025] - cat[2024]) / cat[2024].sum() * 100).sort_values()
        fig = go.Figure(go.Bar(x=ap.values, y=ap.index, orientation="h",
                               marker_color=[AZUL if x >= 0 else NARANJA for x in ap],
                               text=[f"{x:+.2f}" for x in ap], textposition="outside",
                               hovertemplate="%{y}: %{x:+.2f} p.p.<extra></extra>"))
        st.plotly_chart(estilo(fig, 340, "Aporte de cada categoría al crecimiento LFL en unidades (p.p.)", False),
                        width="stretch")
        caja(f"El precio <i>de lista</i> no cambió, pero el precio <b>medio</b> subió {gP*100:.1f} % por "
             "<b>efecto mezcla</b> (más unidades de productos caros). Por eso la empresa crece "
             f"<b>{gQ*100:.1f} % en unidades</b> y <b>{gV*100:.1f} % en dinero</b>.")
