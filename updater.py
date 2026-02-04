import sys, os, requests, zipfile, io, shutil, subprocess, time

REPO_ZIP = "https://github.com/SEU_USUARIO/SEU_REPO/archive/refs/heads/main.zip"

def baixar_atualizacao():
    print("Baixando atualização...")
    r = requests.get(REPO_ZIP)
    z = zipfile.ZipFile(io.BytesIO(r.content))

    pasta_temp = "_update_temp"
    if os.path.exists(pasta_temp):
        shutil.rmtree(pasta_temp)
    z.extractall(pasta_temp)

    pasta_extraida = os.path.join(pasta_temp, os.listdir(pasta_temp)[0])

    for item in os.listdir(pasta_extraida):
        s = os.path.join(pasta_extraida, item)
        d = os.path.join(".", item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

    shutil.rmtree(pasta_temp)
    print("Atualização concluída!")
    return True


def fechar_main(pid):
    try:
        os.kill(int(pid), 9)
    except:
        pass


if "--check" in sys.argv:
    pid_main = sys.argv[2]

    # 👉 AQUI VOCÊ DEFINE SUA CONDIÇÃO DE ATUALIZAÇÃO
    # Simulação:
    precisa_atualizar = False  # MUDE depois pra sua lógica real

    if precisa_atualizar:
        fechar_main(pid_main)
        if baixar_atualizacao():
            time.sleep(1)
            subprocess.Popen(["main.exe"])
    else:
        print("Programa já está atualizado.")
        # ❌ NÃO ABRE O MAIN AQUI
