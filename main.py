import customtkinter, os, requests, threading, json, sys, subprocess
import auth.token_api as token_api
from PIL import Image, ImageOps, ImageDraw
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from datetime import datetime

# ================== 🔥 SISTEMA DE CAMINHOS (CORREÇÃO EXE) ==================
def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# pasta onde o exe está (para salvar PDF etc)
APP_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

# ================== ARQUIVOS ==================
caminho_json = resource_path("auth/link.json")
with open(caminho_json, "r", encoding="utf-8") as f:
    link = json.load(f)

linhas_produtos = []

# ================== LOADING ==================

def mostrar_loading():
    label_loading.configure(text="Carregando...")
    label_loading.pack(side="left", padx=10)

def esconder_loading():
    label_loading.pack_forget()

# ================== API ==================

def info_artesao_thread(id):
    mostrar_loading()
    threading.Thread(target=info_artesao, args=(id,), daemon=True).start()

def info_artesao(id):
    token_api.capturar_token()
    token = token_api.carregar_token()
    header = {"Authorization": token}

    url = link["producaoArtesao"]

    payload = {
        "situacao": "ATIVADA",
        "numeroCarteira": id,
        "pageNumber": 1,
        "pageSize": 10,
        "direction": "DESC",
        "paginate": True,
        "by": ["dataCadastro"],
        "dataInicioCarteira": None,
        "dataFimCarteira": None
    }

    response = requests.post(url=url, json=payload, headers=header)
    data = response.json()

    nome = data['response'][0]['nome']
    foto = "http://apiceart.sps.ce.gov.br:8894/ceart-artesao/artesao/imagens/" + data['response'][0]['foto']

    app.after(0, lambda: atualizar_artesao(nome, foto))
    app.after(0, esconder_loading)


def info_entidade(id):
    token_api.capturar_token()
    token = token_api.carregar_token()
    header = {"Authorization": token}
    url = link["producaoEntidade"]

    payload = {
        "tipo": "ENTIDADE",
        "numeroCarteira": id,
        "pageNumber": 1,
        "pageSize": 10,
        "direction": "DESC",
        "paginate": True,
        "by": ["id"],
        "dataInicioCarteira": None,
        "dataFimCarteira": None
    }

    response = requests.post(url=url, json=payload, headers=header)
    data = response.json()
    nome = data['response'][0]['nome']
    atualizar_artesao(nome, None)


def atualizar_artesao(nome, foto_url):
    entry_nome.delete(0, "end")
    entry_nome.insert(0, nome)

    if foto_url:
        try:
            response = requests.get(foto_url)
            img = Image.open(BytesIO(response.content)).convert("RGBA")
            img = ImageOps.fit(img, (80, 80), Image.LANCZOS)

            mask = Image.new("L", (80, 80), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 80, 80), fill=255)
            img.putalpha(mask)

            nova_img = customtkinter.CTkImage(light_image=img, dark_image=img, size=(80, 80))
            label_foto.configure(image=nova_img)
            label_foto.image = nova_img

        except Exception as e:
            print("Erro ao carregar foto:", e)

# ================== PRODUTO ==================

def info_produto(codigo, e_desc, id):
    token_api.capturar_token()
    token = token_api.carregar_token()
    header = {"Authorization": token}
    url = link["comercializacaoProduto"]

    if radio_tipo_var.get() == "Artesao":
        payload = {
            "selecionado": False,
            "tipoFiltro": "ARTESAO",
            "codigoProduto": codigo,
            "numeroCarteiraArtesao": id,
            "paginate": True,
            "pageNumber": 1,
            "pageSize": 10,
            "direction": "ASC",
            "comercializacao": True,
            "by": [
                "produto.nome"
            ],
            "tipo": 0
            }
    else:
        payload = {
            "selecionado": False,
            "tipoFiltro": "ENTIDADE",
            "numeroCarteiraEntidade": id,
            "codigoProduto": codigo,
            "paginate": True,
            "pageNumber": 1,
            "pageSize": 10,
            "direction": "ASC",
            "comercializacao": True,
            "by": [
                "produto.nome"
            ],
            "tipo": 1
            }

    response = requests.post(url=url, json=payload, headers=header)
    data = response.json()
    id_produto = data['response'][0]['id']
    info_reajuste(id_produto)
    atualizar_entry(data, e_desc)

def info_reajuste(id):
    token_api.capturar_token()
    token = token_api.carregar_token()
    header = {"Authorization": token}

    url = link["comercializacaoReajuste"] + str(id)

    try:
        response = requests.get(url=url, headers=header)
        data = response.json()

        # Se não existir reajuste
        if not data.get("response") or not data["response"].get("dataReajuste"):
            l_reajuste.configure(text="Nunca Reajustado")
            return

        ultimo_reajuste = data["response"]["dataReajuste"][:10]  # yyyy-mm-dd
        dia = ultimo_reajuste[8:]
        mes = ultimo_reajuste[5:7]
        ano = ultimo_reajuste[:4]

        l_reajuste.configure(text=f"{dia}/{mes}/{ano}")

    except Exception as e:
        print("Erro ao buscar reajuste:", e)
        l_reajuste.configure(text="Nunca Reajustado")


def atualizar_entry(data, e_desc):
    descricao = data['response'][0]['produto']['nome']
    valor = data['response'][0]['valorVarejo']
    reajuste = round(valor * 1.10, 2)

    e_desc.delete(0, "end")
    e_desc.insert(0, descricao)
    e_val.delete(0, "end")
    e_val.insert(0, f"R$ {valor}")
    e_reaj.delete(0, "end")
    e_reaj.insert(0, f"R$ {reajuste}")

# ================== UI LINHA PRODUTO ==================

def adicionar_linha():
    global e_cod, e_desc, e_val, e_reaj, l_reajuste

    linha_frame = customtkinter.CTkFrame(frame_produtos, fg_color="transparent")
    linha_frame.pack(fill="x", padx=10, pady=5)

    # Colunas que vão se esticar (o que sobra da linha)
    linha_frame.grid_columnconfigure(0, weight=1)  # Código
    linha_frame.grid_columnconfigure(2, weight=6)  # Descrição
    linha_frame.grid_columnconfigure(3, weight=1)  # Data reajuste
    linha_frame.grid_columnconfigure(4, weight=1)  # Valor
    linha_frame.grid_columnconfigure(5, weight=1)  # Reajuste

    # Colunas FIXAS (sem weight)
    linha_frame.grid_columnconfigure(1, weight=0)  # Botão pesquisar
    linha_frame.grid_columnconfigure(6, weight=0)  # Botão -

    e_cod = customtkinter.CTkEntry(linha_frame, placeholder_text="Código")
    e_cod.grid(row=0, column=0, padx=2, sticky="ew")

    btn_pesquisar = customtkinter.CTkButton(
        linha_frame,
        text="Pesquisar",
        width=120,  # FIXO
        fg_color="green",
        hover_color="darkgreen",
        command=lambda: info_produto(e_cod.get(), e_desc, entry_id.get())
    )
    btn_pesquisar.grid(row=0, column=1, padx=2)

    e_desc = customtkinter.CTkEntry(linha_frame, placeholder_text="Descrição")
    e_desc.grid(row=0, column=2, padx=2, sticky="ew")

    l_reajuste = customtkinter.CTkLabel(linha_frame, text="", fg_color="transparent")
    l_reajuste.grid(row=0, column=3, padx=2, sticky="ew")

    e_val = customtkinter.CTkEntry(linha_frame, placeholder_text="Valor")
    e_val.grid(row=0, column=4, padx=2, sticky="ew")

    e_reaj = customtkinter.CTkEntry(linha_frame, placeholder_text="Reajuste")
    e_reaj.grid(row=0, column=5, padx=2, sticky="ew")

    btn_menos = customtkinter.CTkButton(
        linha_frame,
        text="-",
        width=80,  # FIXO
        fg_color="#922b21",
        hover_color="#641e16",
        command=lambda: linha_frame.destroy()
    )
    btn_menos.grid(row=0, column=6, padx=2)

    linhas_produtos.append({
        "codigo": e_cod,
        "descricao": e_desc,
        "valor": e_val,
        "reajuste": e_reaj
    })



def gerar_pdf():
    nome = entry_nome.get()
    identidade = entry_id.get()
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    caminho_pdf = os.path.join(APP_DIR, f"Relatorio_{identidade}.pdf")
    doc = SimpleDocTemplate(caminho_pdf, pagesize=A4)
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph(f"<b>Artesão/Entidade:</b> {nome}", styles['Normal']))
    elementos.append(Paragraph(f"<b>Identidade:</b> {identidade}", styles['Normal']))
    elementos.append(Paragraph(f"<b>Data:</b> {data_hoje}", styles['Normal']))
    elementos.append(Spacer(1, 10))

    dados = [["Código", "Descrição", "Último Reajuste", "Valor", "Reajuste"]]

    for frame in frame_produtos.winfo_children():
        widgets = frame.winfo_children()

        codigo = widgets[0].get()                 # Entry Código
        descricao = Paragraph(widgets[2].get(), styles['Normal'])  # Entry Descrição
        ultimo = Paragraph(widgets[3].cget("text"))
        valor = widgets[4].get()                  # Entry Valor
        reajuste = widgets[5].get()               # Entry Reajuste

        dados.append([codigo, descricao, ultimo, valor, reajuste])

    tabela = Table(dados, colWidths=[25*mm, 65*mm, 35*mm, 25*mm, 25*mm])
    tabela.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))

    elementos.append(tabela)
    doc.build(elementos)
    os.startfile(caminho_pdf)


# ================== IMAGEM REDONDA ==================

def make_circle(image_path, size):
    try:
        img = Image.open(image_path).convert("RGBA")
        img = img.resize(size, Image.LANCZOS)

        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)

        output = ImageOps.fit(img, size, centering=(0.5, 0.5))
        output.putalpha(mask)
        return output
    except Exception as e:
        print(f"Erro ao carregar imagem: {e}")
        return Image.new("RGBA", size, (100, 100, 100, 255))

# ================== JANELA ==================

customtkinter.set_appearance_mode("dark")
app = customtkinter.CTk()
app.title("Reajuste Comercialização")
app.after(0, lambda: app.state('zoomed'))

frame_artesao = customtkinter.CTkFrame(app, fg_color="#2b2b2b", corner_radius=15)
frame_artesao.pack(fill="x", padx=20, pady=20)

img_perfil = make_circle("foto.png", (80, 80))
my_image = customtkinter.CTkImage(light_image=img_perfil, dark_image=img_perfil, size=(80, 80))

label_foto = customtkinter.CTkLabel(frame_artesao, image=my_image, text="")
label_foto.pack(side="left", padx=20, pady=20)

label_loading = customtkinter.CTkLabel(frame_artesao, text="", text_color="yellow")

entry_id = customtkinter.CTkEntry(frame_artesao, placeholder_text="Identidade Artesanal", width=150)
entry_id.pack(side="left", padx=(0, 10))

radio_tipo_var = customtkinter.StringVar(value="Artesao")

frame_radio = customtkinter.CTkFrame(frame_artesao, fg_color="transparent")
frame_radio.pack(side="left", padx=(0, 10))

customtkinter.CTkRadioButton(frame_radio, text="Artesão", variable=radio_tipo_var, value="Artesao").pack(anchor="w")
customtkinter.CTkRadioButton(frame_radio, text="Entidade", variable=radio_tipo_var, value="Entidade").pack(anchor="w")

customtkinter.CTkButton(
    frame_artesao,
    text="Pesquisar",
    fg_color="green",
    hover_color="darkgreen",
    command=lambda: info_artesao_thread(entry_id.get()) if radio_tipo_var.get()=="Artesao" else info_entidade(entry_id.get())
).pack(side="left", padx=(0, 20))

entry_nome = customtkinter.CTkEntry(frame_artesao, placeholder_text="Nome do Artesão", width=300)
entry_nome.pack(side="left", padx=(0, 20))

customtkinter.CTkLabel(app, text="LISTA DE PRODUTOS", font=("Arial", 14, "bold")).pack(pady=(10, 0))

frame_produtos = customtkinter.CTkFrame(app, fg_color="#2b2b2b", corner_radius=15)
frame_produtos.pack(fill="x", padx=20, pady=10)

customtkinter.CTkButton(
    app,
    text="+ Adicionar Nova Linha",
    fg_color="green",
    hover_color="darkgreen",
    height=40,
    command=adicionar_linha
).pack(pady=20)

customtkinter.CTkButton(
    app,
    text="Gerar PDF",
    fg_color="#1f6aa5",
    hover_color="#144870",
    height=40,
    command=gerar_pdf
).pack(pady=10)


adicionar_linha()
app.mainloop()
