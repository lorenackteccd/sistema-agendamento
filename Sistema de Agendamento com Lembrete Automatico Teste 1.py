# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from threading import Thread
import time

# ---------------------------------------------------------
# 1. ESTRUTURA DE DADOS EM MEMÓRIA
# ---------------------------------------------------------
agendamentos = []
proximo_id = 1

# ---------------------------------------------------------
# 2. INTEGRAÇÃO E LEMBRETE
# ---------------------------------------------------------
def enviar_lembrete_24h(agendamento):
    """
    Simula a integração com uma API externa de mensagens.
    O lembrete usa o formato de mensagem solicitado.
    """
    nome = agendamento['paciente']
    telefone = agendamento['telefone']
    # Formata a data para o padrão brasileiro xx-xx-xxxx no lembrete
    data_formatada = datetime.strptime(agendamento['data'], "%Y-%m-%d").strftime("%d-%m-%Y")
    hora = agendamento['hora']

    mensagem = f"Olá {nome}, sua consulta médica está agendada para o dia {data_formatada} as {hora}."

    print(f"\n--- [NOTIFICAÇÃO ENVIADA PARA {telefone}] ---")
    print(f"Mensagem: {mensagem}")
    print("----------------------------------------------")

def verificar_agendamentos_para_notificar():
    """
    Lógica de Engenharia de Software: verifica quais consultas ocorrerão
    em exatamente 24 horas a partir de agora para disparar o lembrete.
    """
    agora = datetime.now()
    janela_24h = agora + timedelta(days=1)

    for a in agendamentos:
        # Combina data e hora para comparação
        data_hora_consulta = datetime.strptime(f"{a['data']} {a['hora']}", "%Y-%m-%d %H:%M")

        # Se a consulta for daqui a 24 horas (considerando uma margem de 1 hora para o teste)
        if agora < data_hora_consulta <= janela_24h and not a.get('lembrete_enviado'):
            enviar_lembrete_24h(a)
            a['lembrete_enviado'] = True

# ---------------------------------------------------------
# 3. API REST
# ---------------------------------------------------------
app = Flask(__name__)

@app.route('/consultas', methods=['GET'])
def api_listar():
    return jsonify(agendamentos), 200

@app.route('/consultas', methods=['POST'])
def api_agendar():
    global proximo_id
    dados = request.get_json()
    novo = {
        "id": proximo_id,
        "paciente": dados['paciente'],
        "telefone": dados['telefone'],
        "data": dados['data'], # Formato esperado: YYYY-MM-DD
        "hora": dados['hora'], # Formato esperado: HH:MM
        "lembrete_enviado": False
    }
    agendamentos.append(novo)
    proximo_id += 1
    return jsonify(novo), 201

@app.route('/consultas/<int:id>', methods=['DELETE'])
def api_cancelar(id):
    global agendamentos
    agendamentos = [a for a in agendamentos if a['id'] != id]
    return jsonify({"status": "sucesso", "mensagem": "Consulta cancelada"}), 200

# ---------------------------------------------------------
# 4. INTERFACE DO USUÁRIO 
# ---------------------------------------------------------
def menu():
    while True:
        print("\n====================================")
        print("   SISTEMA DE AGENDAMENTO MÉDICO")
        print("====================================")
        print("1. Agendar Consulta (Paciente)")
        print("2. Listar Agendamentos")
        print("3. Verificar e Enviar Lembretes")
        print("4. Sair")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            nome = input("Nome do Paciente: ")
            tel = input("Telefone (com DDD): ")
            data = input("Data da consulta (AAAA-MM-DD): ")
            hora = input("Horário da consulta (HH:MM): ")

            novo = {
                "id": len(agendamentos) + 1,
                "paciente": nome,
                "telefone": tel,
                "data": data,
                "hora": hora,
                "lembrete_enviado": False
            }
            agendamentos.append(novo)
            print(f"✅ Consulta agendada com sucesso para o dia {data} às {hora}!")

        elif opcao == "2":
            print("\n--- LISTA DE CONSULTAS ---")
            for a in agendamentos:
                status = "🔔 Lembrete enviado!" if a['lembrete_enviado'] else "⏳ Aguardando 24h anterior a consulta para enviar lembrete."
                print(f"ID: {a['id']} | {a['paciente']} | {a['data']} {a['hora']} | {status}")

        elif opcao == "3":
            print("\n ⏳ Verificando consultas que ocorrem nas próximas 24 horas...")
            verificar_agendamentos_para_notificar()

        elif opcao == "4":
            print("Encerrando sistema...")
            break

if __name__ == "__main__":
    # Inicia a API REST em uma Thread separada (Arquitetura Monolítica)
    Thread(target=lambda: app.run(port=5000, debug=False, use_reloader=False)).start()
    menu()
