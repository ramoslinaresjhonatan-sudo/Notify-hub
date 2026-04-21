import io
import os
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
from datetime import timedelta

STORAGE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'Storage'))

def format_seconds(seg):
    seg = int(seg)
    h = seg // 3600
    m = (seg % 3600) // 60
    s = seg % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def ajustar_texto(texto, width=18):
    return textwrap.fill(str(texto), width=width)

def horas_en_banda(inicio, fin, banda_h_inicio, banda_h_fin):
    total = 0.0
    dia_base = inicio.replace(hour=0, minute=0, second=0, microsecond=0)
    for offset in range(2):
        dia = dia_base + timedelta(days=offset)
        b_ini = dia + timedelta(hours=banda_h_inicio)
        b_fin = dia + timedelta(hours=banda_h_fin)
        solape = max(timedelta(0), min(fin, b_fin) - max(inicio, b_ini))
        total += solape.total_seconds()
    return total

def generar_graficos(ruta_archivo) -> list[str]:
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR, exist_ok=True)

    df = pd.read_csv(ruta_archivo, sep=";")
    df["Inicio de Recarga"] = pd.to_datetime(df["Inicio de Recarga"], dayfirst=True)
    df["Fin de Recarga"]    = pd.to_datetime(df["Fin de Recarga"],    dayfirst=True)
    df["Tiempo de Recarga"] = pd.to_timedelta(df["Tiempo de Recarga"])
    df["segundos"]          = df["Tiempo de Recarga"].dt.total_seconds()

    file_paths = []

    top10 = (
        df[["Nombre de Tarea", "segundos", "Inicio de Recarga", "Fin de Recarga"]]
        .sort_values("segundos", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    fig, ax = plt.subplots(figsize=(14, 6))
    barras = ax.bar(range(len(top10)), top10["segundos"].values, color="#ED7D31", edgecolor="black")
    for i, bar in enumerate(barras):
        row = top10.iloc[i]
        valor = row["segundos"]
        inicio = row["Inicio de Recarga"].strftime("%H:%M:%S")
        fin = row["Fin de Recarga"].strftime("%H:%M:%S")
        altura = bar.get_height()
        
        texto = f"{format_seconds(valor)}\n({inicio} - {fin})"
        ax.text(bar.get_x() + bar.get_width() / 2, altura + 30,
                texto, ha="center", va="bottom", fontsize=6, fontweight='bold')
    
    max_y = int(top10["segundos"].max())
    paso  = 1800
    yticks = list(range(0, max_y + paso, paso))
    ax.set_yticks(yticks)
    ax.set_yticklabels([format_seconds(y) for y in yticks], fontsize=7)
    ax.set_xticks(range(len(top10)))
    ax.set_xticklabels([ajustar_texto(l) for l in top10["Nombre de Tarea"]], rotation=0, ha="center", fontsize=8)
    plt.tight_layout()

    path1 = os.path.join(STORAGE_DIR, "grafica1.png")
    plt.savefig(path1, format="png", bbox_inches="tight", dpi=100)
    plt.close()
    file_paths.append(path1)

    nodos = df["Nombre de Servicio"].value_counts().head(2)
    plt.figure(figsize=(8, 6))
    colores = ["#ED7D31", "#2C3E50"]
    wedges, texts, autotexts = plt.pie(
        nodos, autopct="%1.1f%%", pctdistance=0.72, startangle=90,
        counterclock=False, colors=colores,
        wedgeprops=dict(width=0.45, edgecolor="black", linewidth=1),
        textprops=dict(color="#333333", fontsize=12, fontweight="bold")
    )
    plt.legend(wedges, nodos.index, title="Nodos", loc="center left", bbox_to_anchor=(1, 0.5), fontsize=12)
    plt.axis("equal")
    plt.tight_layout()

    path2 = os.path.join(STORAGE_DIR, "grafica2.png")
    plt.savefig(path2, format="png", bbox_inches="tight", dpi=100)
    plt.close()
    file_paths.append(path2)

    madrugada_total = manana_total = tarde_total = noche_total = 0.0
    for _, row in df.iterrows():
        inicio = row["Inicio de Recarga"]
        fin    = row["Fin de Recarga"]
        madrugada_total += horas_en_banda(inicio, fin, 2, 8)
        manana_total    += horas_en_banda(inicio, fin, 8, 14)
        tarde_total     += horas_en_banda(inicio, fin, 14, 20)
        noche_total     += horas_en_banda(inicio, fin, 20, 26)

    values = [madrugada_total, manana_total, tarde_total, noche_total]
    labels = ["Madrugada", "Mañana", "Tarde", "Noche"]
    colors = ["#ED7D31", "#F4B183", "#BDD7EE", "#8EA9DB"]
    total  = sum(values)
    porc   = [v / total if total > 0 else 0 for v in values]
    
    fig, ax = plt.subplots(figsize=(8, 5))
    y = 0.0; left_sum = porc[0] + porc[1]
    
    for i in range(4):
        w = left_sum if i < 2 else 1 - left_sum
        x = 0 if i < 2 else left_sum
        h = porc[i] / w if w > 0 else 0
        ax.add_patch(plt.Rectangle((x, y if i % 2 == 0 else 0), w, h, facecolor=colors[i], edgecolor="black"))
        h_str = format_seconds(values[i])
        ax.text(x + w/2, (y + h/2 if i % 2 == 0 else h/2), f"{labels[i]}\n{porc[i]*100:.1f}%\n({h_str})", 
                ha="center", va="center", fontsize=9, fontweight="bold")
        y = h if i % 2 == 0 else 0
    
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    plt.tight_layout()

    path3 = os.path.join(STORAGE_DIR, "grafica3.png")
    plt.savefig(path3, format="png", bbox_inches="tight", dpi=100)
    plt.close()
    file_paths.append(path3)

    df_g4 = df[df["Inicio de Recarga"].dt.time.between(pd.to_datetime("02:00:00").time(), pd.to_datetime("14:00:00").time())]
    top10_g4 = df_g4.sort_values("segundos", ascending=False).head(10).reset_index(drop=True)
    
    if not top10_g4.empty:
        fig4, ax4 = plt.subplots(figsize=(14, 6))
        barras4 = ax4.bar(range(len(top10_g4)), top10_g4["segundos"].values, color="#ED7D31", edgecolor="black")
        for i, bar in enumerate(barras4):
            row = top10_g4.iloc[i]
            valor = row["segundos"]
            inicio = row["Inicio de Recarga"].strftime("%H:%M:%S")
            fin = row["Fin de Recarga"].strftime("%H:%M:%S")
            altura = bar.get_height()
            texto = f"{format_seconds(valor)}\n({inicio} - {fin})"
            ax4.text(bar.get_x() + bar.get_width() / 2, altura + 30, texto, ha="center", va="bottom", fontsize=6, fontweight='bold')
        
        max_y4 = int(top10_g4["segundos"].max())
        paso  = 1800
        yticks4 = list(range(0, max_y4 + paso, paso))
        ax4.set_yticks(yticks4)
        ax4.set_yticklabels([format_seconds(y) for y in yticks4], fontsize=7)
        ax4.set_xticks(range(len(top10_g4)))
        ax4.set_xticklabels([ajustar_texto(l) for l in top10_g4["Nombre de Tarea"]], rotation=0, ha="center", fontsize=8)
        ax4.set_title("Top 10 Tiempos de Recarga (02:00 - 14:00)", fontsize=12, fontweight='bold')
        plt.tight_layout()
        path4 = os.path.join(STORAGE_DIR, "grafica4.png")
        plt.savefig(path4, format="png", bbox_inches="tight", dpi=100)
        plt.close()
        file_paths.append(path4)
    else:
        file_paths.append(None) # Placeholder to maintain indexing if needed, or handle in script

    df_g5 = df[(df["Inicio de Recarga"].dt.time >= pd.to_datetime("14:00:00").time()) | 
               (df["Inicio de Recarga"].dt.time < pd.to_datetime("02:00:00").time())]
    top10_g5 = df_g5.sort_values("segundos", ascending=False).head(10).reset_index(drop=True)

    if not top10_g5.empty:
        fig5, ax5 = plt.subplots(figsize=(14, 6))
        barras5 = ax5.bar(range(len(top10_g5)), top10_g5["segundos"].values, color="#ED7D31", edgecolor="black")
        for i, bar in enumerate(barras5):
            row = top10_g5.iloc[i]
            valor = row["segundos"]
            inicio = row["Inicio de Recarga"].strftime("%H:%M:%S")
            fin = row["Fin de Recarga"].strftime("%H:%M:%S")
            altura = bar.get_height()
            texto = f"{format_seconds(valor)}\n({inicio} - {fin})"
            ax5.text(bar.get_x() + bar.get_width() / 2, altura + 30, texto, ha="center", va="bottom", fontsize=6, fontweight='bold')
        
        max_y5 = int(top10_g5["segundos"].max())
        paso  = 1800
        yticks5 = list(range(0, max_y5 + paso, paso))
        ax5.set_yticks(yticks5)
        ax5.set_yticklabels([format_seconds(y) for y in yticks5], fontsize=7)
        ax5.set_xticks(range(len(top10_g5)))
        ax5.set_xticklabels([ajustar_texto(l) for l in top10_g5["Nombre de Tarea"]], rotation=0, ha="center", fontsize=8)
        ax5.set_title("Top 10 Tiempos de Recarga (14:00 - 02:00)", fontsize=12, fontweight='bold')
        plt.tight_layout()
        path5 = os.path.join(STORAGE_DIR, "grafica5.png")
        plt.savefig(path5, format="png", bbox_inches="tight", dpi=100)
        plt.close()
        file_paths.append(path5)
    else:
        file_paths.append(None)

    print(f"Gráficos guardados exitosamente en: {STORAGE_DIR}")
    return file_paths


import base64

TITULOS = [
    ("Top 10 Tiempos de Recarga",       "Tareas con mayor tiempo total de ejecución"),
    ("Distribución por Nodo",            "Porcentaje de recargas por servidor"),
    ("Horario de Processing",            "Distribución de tiempo por banda horaria"),
    ("Top 10 (Madrugada / Mañana)",      "Tareas más largas entre 02:00 y 14:00"),
    ("Top 10 (Tarde / Noche)",           "Tareas más largas entre 14:00 y 02:00"),
]

def _fig_to_b64(fig, dpi=150) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=dpi)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def generar_figuras_b64(ruta_archivo: str) -> list[dict]:

    df = pd.read_csv(ruta_archivo, sep=";")
    df["Inicio de Recarga"] = pd.to_datetime(df["Inicio de Recarga"], dayfirst=True)
    df["Fin de Recarga"]    = pd.to_datetime(df["Fin de Recarga"],    dayfirst=True)
    df["Tiempo de Recarga"] = pd.to_timedelta(df["Tiempo de Recarga"])
    df["segundos"]          = df["Tiempo de Recarga"].dt.total_seconds()

    figuras = []
    top10 = (df[["Nombre de Tarea", "segundos", "Inicio de Recarga", "Fin de Recarga"]]
             .sort_values("segundos", ascending=False).head(10).reset_index(drop=True))
    fig, ax = plt.subplots(figsize=(14, 6))
    barras = ax.bar(range(len(top10)), top10["segundos"].values, color="#ED7D31", edgecolor="black")
    for i, bar in enumerate(barras):
        row = top10.iloc[i]
        texto = f"{format_seconds(row['segundos'])}\n({row['Inicio de Recarga'].strftime('%H:%M:%S')} - {row['Fin de Recarga'].strftime('%H:%M:%S')})"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 30,
                texto, ha="center", va="bottom", fontsize=6, fontweight="bold")
    max_y = int(top10["segundos"].max())
    yticks = list(range(0, max_y + 1800, 1800))
    ax.set_yticks(yticks)
    ax.set_yticklabels([format_seconds(y) for y in yticks], fontsize=8)
    ax.set_xticks(range(len(top10)))
    ax.set_xticklabels([ajustar_texto(l) for l in top10["Nombre de Tarea"]], rotation=0, ha="center", fontsize=9)
    ax.set_title(TITULOS[0][0], fontsize=13, fontweight="bold", pad=12)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5); ax.set_axisbelow(True)
    plt.tight_layout()
    figuras.append({"b64": _fig_to_b64(fig), "titulo": TITULOS[0][0], "descripcion": TITULOS[0][1], "nombre_archivo": "grafico1.png"})

    nodos = df["Nombre de Servicio"].value_counts().head(2)
    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        nodos, autopct="%1.1f%%", pctdistance=0.72, startangle=90,
        counterclock=False, colors=["#ED7D31", "#2C3E50"],
        wedgeprops=dict(width=0.45, edgecolor="black", linewidth=1),
        textprops=dict(color="#333333", fontsize=12, fontweight="bold")
    )
    plt.legend(wedges, nodos.index, title="Nodos", loc="center left", bbox_to_anchor=(1, 0.5), fontsize=12)
    ax.axis("equal")
    ax.set_title(TITULOS[1][0], fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    figuras.append({"b64": _fig_to_b64(fig), "titulo": TITULOS[1][0], "descripcion": TITULOS[1][1], "nombre_archivo": "grafico2.png"})

    madrugada = manana = tarde = noche = 0.0
    for _, row in df.iterrows():
        madrugada += horas_en_banda(row["Inicio de Recarga"], row["Fin de Recarga"], 2, 8)
        manana    += horas_en_banda(row["Inicio de Recarga"], row["Fin de Recarga"], 8, 14)
        tarde     += horas_en_banda(row["Inicio de Recarga"], row["Fin de Recarga"], 14, 20)
        noche     += horas_en_banda(row["Inicio de Recarga"], row["Fin de Recarga"], 20, 26)
    values = [madrugada, manana, tarde, noche]
    labels = ["Madrugada", "Mañana", "Tarde", "Noche"]
    colors = ["#ED7D31", "#F4B183", "#BDD7EE", "#8EA9DB"]
    total  = sum(values)
    porc   = [v / total if total > 0 else 0 for v in values]
    fig, ax = plt.subplots(figsize=(8, 5))
    y = 0.0; left_sum = porc[0] + porc[1]
    for i in range(4):
        w = left_sum if i < 2 else 1 - left_sum
        x = 0 if i < 2 else left_sum
        h = porc[i] / w if w > 0 else 0
        ax.add_patch(plt.Rectangle((x, y if i % 2 == 0 else 0), w, h, facecolor=colors[i], edgecolor="white", linewidth=2))
        ax.text(x + w/2, (y + h/2 if i % 2 == 0 else h/2),
                f"{labels[i]}\n{porc[i]*100:.1f}%\n({format_seconds(values[i])})",
                ha="center", va="center", fontsize=10, fontweight="bold", color="#1a1a1a")
        y = h if i % 2 == 0 else 0
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.set_title(TITULOS[2][0], fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    figuras.append({"b64": _fig_to_b64(fig), "titulo": TITULOS[2][0], "descripcion": TITULOS[2][1], "nombre_archivo": "grafico3.png"})

    df_g4 = df[df["Inicio de Recarga"].dt.time.between(
        pd.to_datetime("02:00:00").time(), pd.to_datetime("14:00:00").time())]
    top10_g4 = df_g4.sort_values("segundos", ascending=False).head(10).reset_index(drop=True)
    if not top10_g4.empty:
        fig, ax = plt.subplots(figsize=(14, 6))
        barras = ax.bar(range(len(top10_g4)), top10_g4["segundos"].values, color="#ED7D31", edgecolor="black")
        for i, bar in enumerate(barras):
            row = top10_g4.iloc[i]
            texto = f"{format_seconds(row['segundos'])}\n({row['Inicio de Recarga'].strftime('%H:%M:%S')} - {row['Fin de Recarga'].strftime('%H:%M:%S')})"
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 30,
                    texto, ha="center", va="bottom", fontsize=6, fontweight="bold")
        max_y = int(top10_g4["segundos"].max())
        yticks = list(range(0, max_y + 1800, 1800))
        ax.set_yticks(yticks); ax.set_yticklabels([format_seconds(y) for y in yticks], fontsize=8)
        ax.set_xticks(range(len(top10_g4)))
        ax.set_xticklabels([ajustar_texto(l) for l in top10_g4["Nombre de Tarea"]], rotation=0, ha="center", fontsize=9)
        ax.set_title(TITULOS[3][0], fontsize=13, fontweight="bold", pad=12)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        ax.yaxis.grid(True, linestyle="--", alpha=0.5); ax.set_axisbelow(True)
        plt.tight_layout()
        figuras.append({"b64": _fig_to_b64(fig), "titulo": TITULOS[3][0], "descripcion": TITULOS[3][1], "nombre_archivo": "grafico4.png"})
    else:
        figuras.append(None)

    df_g5 = df[(df["Inicio de Recarga"].dt.time >= pd.to_datetime("14:00:00").time()) |
               (df["Inicio de Recarga"].dt.time < pd.to_datetime("02:00:00").time())]
    top10_g5 = df_g5.sort_values("segundos", ascending=False).head(10).reset_index(drop=True)
    if not top10_g5.empty:
        fig, ax = plt.subplots(figsize=(14, 6))
        barras = ax.bar(range(len(top10_g5)), top10_g5["segundos"].values, color="#ED7D31", edgecolor="black")
        for i, bar in enumerate(barras):
            row = top10_g5.iloc[i]
            texto = f"{format_seconds(row['segundos'])}\n({row['Inicio de Recarga'].strftime('%H:%M:%S')} - {row['Fin de Recarga'].strftime('%H:%M:%S')})"
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 30,
                    texto, ha="center", va="bottom", fontsize=6, fontweight="bold")
        max_y = int(top10_g5["segundos"].max())
        yticks = list(range(0, max_y + 1800, 1800))
        ax.set_yticks(yticks); ax.set_yticklabels([format_seconds(y) for y in yticks], fontsize=8)
        ax.set_xticks(range(len(top10_g5)))
        ax.set_xticklabels([ajustar_texto(l) for l in top10_g5["Nombre de Tarea"]], rotation=0, ha="center", fontsize=9)
        ax.set_title(TITULOS[4][0], fontsize=13, fontweight="bold", pad=12)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        ax.yaxis.grid(True, linestyle="--", alpha=0.5); ax.set_axisbelow(True)
        plt.tight_layout()
        figuras.append({"b64": _fig_to_b64(fig), "titulo": TITULOS[4][0], "descripcion": TITULOS[4][1], "nombre_archivo": "grafico5.png"})
    else:
        figuras.append(None)

    return figuras
