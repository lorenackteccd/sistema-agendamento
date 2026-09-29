# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from threading import Thread

# ---------------------------------------------------------
# 1. ESTRUTURA DE DADOS EM MEMÓRIA
# ---------------------------------------------------------
agendamentos = []
proximo_id = 1

# ---------------------------------------------------------
# 2. FUNÇÕES DE VALIDAÇÃO E UTILITÁRIOS (Qualidade de Código)
# ---------------------------------------------------------
def obter_data_validada():
    while True:
        data_input = input("Data da consulta Ano, Mês e Dia (AAAA-MM-DD): ").strip()
        try:
            datetime.strptime(data_input, "%Y-%m-%d")
            return data_input
        except ValueError:
            print("❌ Erro: Formato de data inválido. Por favor, reescreva no formato Ano, Mês e Dia (AAAA-MM-DD).")

def obter_horario_validado():
    while True:
        hora_input = input("Horário da consulta Hora e Minuto (HH:MM): ").strip()
        try:
            datetime.strptime(hora_input, "%H:%M")
            return hora_input
        except ValueError:
            print("❌ Erro: Formato de horário inválido. Por favor, reescreva no formato Hora e Minuto (HH:MM).")

# ---------------------------------------------------------
# 3. INTEGRAÇÃO E LEMBRETES
# ---------------------------------------------------------
def enviar_lembrete_24h(agendamento):
    nome = agendamento['paciente']
    telefone = agendamento['telefone']
    data_pt = datetime.strptime(agendamento['data'], "%Y-%m-%d").strftime("%d-%m-%Y")
    hora = agendamento['hora']

    mensagem = f"Olá {nome}, sua consulta médica está agendada para o dia {data_pt} as {hora}."

    print(f"\n--- [NOTIFICAÇÃO ENVIADA PARA {telefone}] ---")
    print(f"Mensagem: {mensagem}")

def verificar_agendamentos_para_notificar():
    agora = datetime.now()
    janela_24h = agora + timedelta(days=1)

    print("\nBuscando consultas nas próximas 24 horas...")
    for a in agendamentos:
        data_hora_consulta = datetime.strptime(f"{a['data']} {a['hora']}", "%Y-%m-%d %H:%M")
        if agora < data_hora_consulta <= janela_24h and not a.get('lembrete_enviado'):
            enviar_lembrete_24h(a)
            a['lembrete_enviado'] = True

# ---------------------------------------------------------
# 4. CANCELAMENTO DE CONSULTA
# ---------------------------------------------------------
def cancelar_consulta_cli():
    global agendamentos
    nome_busca = input("Digite o nome do paciente para cancelar a consulta: ").strip().lower()

    tamanho_antes = len(agendamentos)
    agendamentos = [a for a in agendamentos if a['paciente'].lower() != nome_busca]

    if len(agendamentos) < tamanho_antes:
        print("✅ Consulta cancelada.")
    else:
        print("⚠️ Paciente não encontrado.")

# ---------------------------------------------------------
# 5. API REST
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
        "id": proximo_id, "paciente": dados['paciente'], "telefone": dados['telefone'],
        "data": dados['data'], "hora": dados['hora'], "lembrete_enviado": False
    }
    agendamentos.append(novo)
    proximo_id += 1
    return jsonify(novo), 201

@app.route('/consultas/<int:id>', methods=['DELETE'])
def api_deletar(id):
    global agendamentos
    agendamentos = [a for a in agendamentos if a['id'] != id]
    return jsonify({"mensagem": "Removido via API"}), 200

# ---------------------------------------------------------
# 6. MENU PRINCIPAL
# ---------------------------------------------------------
def menu():
    while True:
        print("\n====================================")
        print("   SISTEMA DE AGENDAMENTO MÉDICO")
        print("====================================")
        print("1. Agendar Nova Consulta")
        print("2. Listar Todas as Consultas")
        print("3. Cancelar Consulta (por Nome)")
        print("4. Verificar e Enviar Lembretes")
        print("5. Sair")

        opcao = input("\nEscolha uma opção digitando o número correspondente (1-5): ").strip()

        if opcao == "1":
            nome = input("Nome do Paciente: ").strip()
            tel = input("Telefone do Paciente: ").strip()
            data = obter_data_validada()
            hora = obter_horario_validado()

            global proximo_id
            novo = {"id": proximo_id, "paciente": nome, "telefone": tel, "data": data, "hora": hora, "lembrete_enviado": False}
            agendamentos.append(novo)
            proximo_id += 1
            print(f"✅ Consulta agendada com sucesso para {data} às {hora}!")

        elif opcao == "2":
            print("\n--- LISTA DE AGENDAMENTOS ---")
            for a in agendamentos:
                print(f"ID: {a['id']} | Paciente: {a['paciente']} | Data: {a['data']} | Hora: {a['hora']}")

        elif opcao == "3":
            cancelar_consulta_cli()

        elif opcao == "4":
            verificar_agendamentos_para_notificar()

        elif opcao == "5":
            print("Sistema Finalizado.")
            break
        else:
            print("❌ Opção inválida! Escolha um número de 1 a 5.")

if __name__ == "__main__":
    Thread(target=lambda: app.run(port=5000, debug=False, use_reloader=False)).start()
    menu()
