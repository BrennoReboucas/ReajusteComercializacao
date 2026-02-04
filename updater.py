import os
import shutil
import sys
import subprocess
import requests
from zipfile import ZipFile
from io import BytesIO
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# URL do zip do repositório no GitHub
ZIP_URL = "https://github.com/BrennoReboucas/ReajusteComercializacao/archive/refs/heads/main.zip"

def baixar_e_substituir():
    try:
        print("Baixando atualização...")
        r = requests.get(ZIP_URL)
        zip_file = ZipFile(BytesIO(r.content))

        temp_dir = os.path.join(BASE_DIR, "temp_update")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        zip_file.extractall(temp_dir)

        # pega a pasta extraída (geralmente NOME_REPO-main)
        pasta_extraida = os.path.join(temp_dir, os.listdir(temp_dir)[0])

        # copia tudo da pasta extraída para a pasta principal
        for item in os.listdir(pasta_extraida):
            s = os.path.join(pasta_extraida, item)
            d = os.path.join(BASE_DIR, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        shutil.rmtree(temp_dir)
        print("Atualização concluída!")
    except Exception as e:
        print("Erro ao atualizar:", e)

# baixa e substitui os arquivos
baixar_e_substituir()

# espera 1s pra garantir que tudo esteja salvo
time.sleep(1)

# reinicia o programa principal
subprocess.Popen([sys.executable, os.path.join(BASE_DIR, "ctk.py")])
sys.exit()
