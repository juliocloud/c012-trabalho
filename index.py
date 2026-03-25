import threading
import time
import random
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

def tempo_de_checkout():
    r = random.uniform(0.1, 0.2)
    if random.random() > 0.7:
        r += 0.3
    return r


def tempo_de_api():
    r = random.uniform(0.03, 0.08)
    if random.random() > 0.7:
        r += 0.01
    return r

class Produto:
    def __init__(self, nome, estoque_inicial):
        self.nome = nome
        self.quantidade_estoque = estoque_inicial

def processar_checkout(cliente_id, produto):

    print(f"Cliente {cliente_id}: Verificando estoque para {produto.nome}...")
    
    if produto.quantidade_estoque > 0:
        # Simula um pequeno atraso no processamento (ex: validação de pagamento)
        # Isso aumenta a janela de oportunidade para a race condition ocorrer
        r = tempo_de_checkout()
        time.sleep(r)
        
        print(f"Cliente {cliente_id}: Estoque disponível. Finalizando compra...")
        produto.quantidade_estoque -= 1
        print(f"Cliente {cliente_id}: Compra concluída.")
    else:
        print(f"Cliente {cliente_id}: Falha na compra. Produto esgotado.")


def processar_checkout_com_logs(cliente_id, produto, logs):
    def registrar(msg):
        logs.append(msg)
        print(msg)

    registrar(f"Cliente {cliente_id}: Verificando estoque para {produto.nome}...")

    if produto.quantidade_estoque > 0:
        r = tempo_de_checkout()
        registrar(str(r))
        time.sleep(r)

        registrar(f"Cliente {cliente_id}: Estoque disponivel. Finalizando compra...")
        produto.quantidade_estoque -= 1
        registrar(f"Cliente {cliente_id}: Compra concluida.")
    else:
        registrar(f"Cliente {cliente_id}: Falha na compra. Produto esgotado.")


def processar_checkout_visual(cliente_id, produto, logs, clientes, inicio_simulacao):
    cliente_key = str(cliente_id)

    def registrar_etapa(etapa):
        tempo = round(time.perf_counter() - inicio_simulacao, 3)
        clientes[cliente_key]["etapas"].append({"etapa": etapa, "tempo_s": tempo})
        logs.append(f"[{tempo:.3f}s] Cliente {cliente_id}: {etapa}")

        print(f"[{tempo:.3f}s] Cliente {cliente_id}: {etapa}")

    registrar_etapa("pagou")
    clientes[cliente_key]["visual"]["fez_pedido_s"] = round(time.perf_counter() - inicio_simulacao, 3)

    atraso_api = tempo_de_api()
    registrar_etapa(f"aguardando API ({atraso_api:.3f}s)")
    time.sleep(atraso_api)

    registrar_etapa(f"verificando estoque para {produto.nome}")

    if produto.quantidade_estoque > 0:
        r = tempo_de_checkout()
        clientes[cliente_key]["tempo_processamento_s"] = round(r, 3)
        clientes[cliente_key]["visual"]["processando_s"] = round(time.perf_counter() - inicio_simulacao, 3)

        registrar_etapa("processando pagamento")
        time.sleep(r)

        registrar_etapa("processado")
        produto.quantidade_estoque -= 1
        registrar_etapa("compra concluida")

        clientes[cliente_key]["visual"]["final_s"] = round(time.perf_counter() - inicio_simulacao, 3)
        clientes[cliente_key]["visual"]["estado_final"] = "Completo"
        clientes[cliente_key]["saldo_apos_cliente"] = produto.quantidade_estoque
    else:
        clientes[cliente_key]["tempo_processamento_s"] = 0.0
        clientes[cliente_key]["visual"]["processando_s"] = round(time.perf_counter() - inicio_simulacao, 3)

        registrar_etapa("falha na compra (produto esgotado)")

        clientes[cliente_key]["visual"]["final_s"] = round(time.perf_counter() - inicio_simulacao, 3)
        clientes[cliente_key]["visual"]["estado_final"] = "Falhou"
        clientes[cliente_key]["saldo_apos_cliente"] = produto.quantidade_estoque

def simular_sistema():
    # Produto com apenas 1 unidade em estoque
    notebook = Produto(nome="Notebook Gamer", estoque_inicial=1)
    
    # Criando threads para 2 clientes simultâneos
    thread_cliente_1 = threading.Thread(target=processar_checkout, args=(1, notebook))
    thread_cliente_2 = threading.Thread(target=processar_checkout, args=(2, notebook))
    
    print(f"Estoque inicial: {notebook.quantidade_estoque}\n")

    # Inicia as compras ao mesmo tempo
    thread_cliente_1.start()
    thread_cliente_2.start()

    # Aguarda a finalização das threads
    thread_cliente_1.join()
    thread_cliente_2.join()

    print(f"\nEstoque final: {notebook.quantidade_estoque}")
    if notebook.quantidade_estoque < 0:
        print("ERRO: O estoque está negativo! A race condition foi bem-sucedida.")


def simular_sistema_com_resultado():
    notebook = Produto(nome="Notebook Gamer", estoque_inicial=1)
    logs = []

    inicio_simulacao = time.perf_counter()

    clientes = {
        "1": {
            "nome": "Cliente 1",
            "tempo_processamento_s": None,
            "saldo_apos_cliente": None,
            "etapas": [],
            "visual": {
                "fez_pedido_s": None,
                "processando_s": None,
                "final_s": None,
                "estado_final": None,
            },
        },
        "2": {
            "nome": "Cliente 2",
            "tempo_processamento_s": None,
            "saldo_apos_cliente": None,
            "etapas": [],
            "visual": {
                "fez_pedido_s": None,
                "processando_s": None,
                "final_s": None,
                "estado_final": None,
            },
        },
    }

    logs.append(f"[0.000s] Estoque inicial: {notebook.quantidade_estoque}")

    thread_cliente_1 = threading.Thread(
        target=processar_checkout_visual,
        args=(1, notebook, logs, clientes, inicio_simulacao),
    )
    thread_cliente_2 = threading.Thread(
        target=processar_checkout_visual,
        args=(2, notebook, logs, clientes, inicio_simulacao),
    )

    thread_cliente_1.start()
    thread_cliente_2.start()

    thread_cliente_1.join()
    thread_cliente_2.join()

    tempo_total = round(time.perf_counter() - inicio_simulacao, 3)
    logs.append(f"[{tempo_total:.3f}s] Estoque final: {notebook.quantidade_estoque}")
    erro_race_condition = notebook.quantidade_estoque < 0
    if erro_race_condition:
        logs.append("ERRO: O estoque esta negativo! A race condition foi bem-sucedida.")

    return {
        "estoque_inicial": 1,
        "estoque_final": notebook.quantidade_estoque,
        "race_condition": erro_race_condition,
        "tempo_total_s": tempo_total,
        "clientes": clientes,
        "logs": logs,
    }


class SimulacaoAPIHandler(BaseHTTPRequestHandler):
    def _enviar_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path != "/api/simular":
            self._enviar_json(404, {"erro": "Rota nao encontrada"})
            return

        resultado = simular_sistema_com_resultado()
        self._enviar_json(200, resultado)


def iniciar_api(host="127.0.0.1", porta=8000):
    servidor = HTTPServer((host, porta), SimulacaoAPIHandler)
    print(f"API iniciada em http://{host}:{porta}")
    print("Endpoint: POST /api/simular")
    servidor.serve_forever()

if __name__ == "__main__":
    iniciar_api()