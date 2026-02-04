import os, sys, requests, zipfile, io, subprocess, shutil, time
import psutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GITHUB_REPO = "BrennoReboucas/ReajusteComercializacao"
RAW_URL = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/main.zip"

def matar_main(pid):
    try:
        p = psutil.Process(int(pid))
        p.terminate()
        p.wait(5)
        print(f"Main PID {pid} finalizado.")
    except Exception as e:
        print(f"Erro ao finalizar main: {e}")

def baixar_atualizacao():
    print("Baixando atualização...")
    r = requests.get(RAW_URL)
    if r.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            temp_dir = os.path.join(BASE_DIR, "temp_update")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            z.extractall(temp_dir)

            pasta_extracao = os.path.join(temp_dir, os.listdir(temp_dir)[0])
            for item in os.listdir(pasta_extracao):
                s = os.path.join(pasta_extracao, item)
                d = os.path.join(BASE_DIR, item)
                if os.path.isdir(s):
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
            shutil.rmtree(temp_dir)
        print("Atualização concluída!")
        return True
    else:
        print("Erro ao baixar atualização!")
        return False

if __name__ == "__main__":
    # Se recebeu o argumento --update, fecha o main antes de atualizar
    if "--update" in sys.argv:
        idx = sys.argv.index("--update")
        pid_main = sys.argv[idx + 1]
        print(f"Morrendo processo main {pid_main} antes de atualizar...")
        matar_main(pid_main)
        if baixar_atualizacao():
            # Reinicia o main atualizado
            subprocess.Popen([sys.executable, os.path.join(BASE_DIR, "main.py")])
        sys.exit()
