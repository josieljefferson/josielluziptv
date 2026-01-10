# runner.py - VERSÃO RECOMENDADA
import subprocess
import sys
import os
import threading
import signal
import time

def install_requirements():
    """Instala requirements apenas se necessário"""
    if not os.path.exists("requirements.txt"):
        print("⚠️  requirements.txt não encontrado. Continuando...")
        return True
    
    try:
        # Tenta instalar apenas pacotes faltantes
        print("🔍 Verificando dependências...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True,
            check=False  # Não falha imediatamente
        )
        
        if result.returncode == 0:
            print("✅ Dependências verificadas/instaladas")
            return True
        else:
            print(f"⚠️  Aviso na instalação: {result.stderr[:200]}")
            # Continua mesmo com erro (para desenvolvimento)
            return True
            
    except Exception as e:
        print(f"⚠️  Erro na verificação de dependências: {e}")
        return True  # Continua para desenvolvimento

def run_script(script_name, stop_event):
    """Executa um script com gerenciamento de parada"""
    try:
        if not os.path.exists(script_name):
            print(f"❌ {script_name} não encontrado")
            return
        
        print(f"🚀 Iniciando {script_name}...")
        process = subprocess.Popen(
            [sys.executable, script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Função para capturar saída
        def capture_output():
            try:
                while not stop_event.is_set():
                    # Lê linha por linha
                    for line in iter(process.stdout.readline, ''):
                        if stop_event.is_set():
                            break
                        if line.strip():
                            print(f"[{script_name}] {line}", end='')
            except:
                pass
        
        # Thread para capturar saída
        output_thread = threading.Thread(target=capture_output, daemon=True)
        output_thread.start()
        
        # Aguarda processo ou sinal de parada
        while not stop_event.is_set():
            if process.poll() is not None:
                break
            time.sleep(0.5)
        
        # Se recebeu sinal de parada, termina processo
        if stop_event.is_set():
            process.terminate()
            process.wait(timeout=5)
        
    except Exception as e:
        print(f"❌ Erro em {script_name}: {e}")

def main():
    """Função principal"""
    # Instala/verifica dependências
    install_requirements()
    
    # Evento para controle de parada
    stop_event = threading.Event()
    
    # Configura handler para Ctrl+C
    def signal_handler(signum, frame):
        print("\n\n⚠️  Encerrando...")
        stop_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Scripts a executar
    scripts = ["app.py", "epg.py"]
    
    # Filtra scripts que existem
    valid_scripts = [s for s in scripts if os.path.exists(s)]
    
    if not valid_scripts:
        print("❌ Nenhum script válido encontrado!")
        return
    
    # Threads para cada script
    threads = []
    for script in valid_scripts:
        thread = threading.Thread(
            target=run_script,
            args=(script, stop_event),
            daemon=True
        )
        thread.start()
        threads.append(thread)
    
    print(f"\n🎯 Executando {len(valid_scripts)} scripts")
    print("Pressione Ctrl+C para encerrar\n")
    
    # Aguarda todas as threads ou sinal de parada
    try:
        while any(t.is_alive() for t in threads) and not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()
    
    # Aguarda finalização
    for thread in threads:
        thread.join(timeout=2)
    
    print("\n🏁 Execução finalizada")

if __name__ == "__main__":
    main()
