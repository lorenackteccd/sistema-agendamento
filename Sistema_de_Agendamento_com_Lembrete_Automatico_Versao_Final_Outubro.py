# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from threading import Thread
from time import sleep
from twilio.rest import Client

# ---------------------------------------------------------
# 1. CREDENCIAIS DA API DO TWILIO
# Valores fictícios para protótipo acadêmico.
# ---------------------------------------------------------
TWILIO_ACCOUNT_SID = "SEU_ACCOUNT_SID_AQUI"
TWILIO_AUTH_TOKEN = "SEU_AUTH_TOKEN_AQUI"
TWILIO_PHONE_NUMBER = "+1234567890"

# ---------------------------------------------------------
# 2. ESTRUTURA DE DADOS EM MEMÓRIA (Sem Banco de Dados)
# ---------------------------------------------------------
agendamentos = []
proximo_id = 1

# ---------------------------------------------------------
# 3. FUNÇÕES DE VALIDAÇÃO
# ---------------------------------------------------------
def validar_data(data_input):
    """Valida se a data está no formato AAAA-MM-DD."""
    try:
        datetime.strptime(data_input, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def validar_horario(hora_input):
    """Valida se o horário está no formato HH:MM."""
    try:
        datetime.strptime(hora_input, "%H:%M")
        return True
    except (ValueError, TypeError):
        return False


def obter_data_validada():
    """Solicita uma data no CLI até que ela seja válida."""
    while True:
        data_input = input("Data da consulta (AAAA-MM-DD): ").strip()
        if validar_data(data_input):
            return data_input
        print("❌ Erro: Formato de data inválido. Por favor, reescreva no formato AAAA-MM-DD.")


def obter_horario_validado():
    """Solicita um horário no CLI até que ele seja válido."""
    while True:
        hora_input = input("Horário da consulta (HH:MM): ").strip()
        if validar_horario(hora_input):
            return hora_input
        print("❌ Erro: Formato de horário inválido. Por favor, reescreva no formato HH:MM.")


def existe_conflito(data, hora):
    """Verifica se já existe consulta agendada para a mesma data e horário."""
    return any(a["data"] == data and a["hora"] == hora for a in agendamentos)


# ---------------------------------------------------------
# 4. INTEGRAÇÃO COM API DO TWILIO (Lembrete 24h)
# ---------------------------------------------------------
def enviar_lembrete_24h(agendamento):
    """Conecta-se à API do Twilio para enviar o lembrete."""
    nome = agendamento["paciente"]
    telefone = agendamento["telefone"]
    data_pt = datetime.strptime(agendamento["data"], "%Y-%m-%d").strftime("%d-%m-%Y")
    hora = agendamento["hora"]

    mensagem_texto = (
        f"Olá {nome}, sua consulta médica está agendada para o dia "
        f"{data_pt} às {hora}."
    )

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=mensagem_texto,
            from_=TWILIO_PHONE_NUMBER,
            to=telefone,
        )
        print(
            f"\n✅ [TWILIO API] Lembrete enviado com sucesso para "
            f"{telefone}! (SID: {message.sid})"
        )
        return True
    except Exception as e:
        print(f"\n❌ [TWILIO API] Erro ao enviar mensagem via Twilio: {e}")
        return False


def verificar_agendamentos_para_notificar():
    """Verifica consultas nas próximas 24 horas e envia lembretes ainda pendentes."""
    agora = datetime.now()
    janela_24h = agora + timedelta(days=1)

    for agendamento in agendamentos:
        try:
            data_hora_consulta = datetime.strptime(
                f"{agendamento['data']} {agendamento['hora']}",
                "%Y-%m-%d %H:%M",
            )
        except ValueError:
            # Os dados criados pelo sistema passam por validação, mas esta proteção
            # evita que um registro inválido interrompa a rotina automática.
            continue

        if (
            agora < data_hora_consulta <= janela_24h
            and not agendamento.get("lembrete_enviado")
        ):
            if enviar_lembrete_24h(agendamento):
                agendamento["lembrete_enviado"] = True


def rotina_lembretes_automatica():
    """Executa a verificação automaticamente enquanto o sistema estiver aberto."""
    while True:
        verificar_agendamentos_para_notificar()
        sleep(60)


# ---------------------------------------------------------
# 5. CANCELAMENTO DE CONSULTA (Por ID)
# ---------------------------------------------------------
def cancelar_consulta_cli():
    global agendamentos

    id_input = input("Digite o ID da consulta que deseja cancelar: ").strip()
    try:
        id_busca = int(id_input)
    except ValueError:
        print("⚠️ ID inválido. Digite um número inteiro.")
        return

    tamanho_antes = len(agendamentos)
    agendamentos = [a for a in agendamentos if a["id"] != id_busca]

    if len(agendamentos) < tamanho_antes:
        print("✅ Consulta cancelada.")
    else:
        print("⚠️ Consulta não encontrada.")


# ---------------------------------------------------------
# 6. API REST FUNCIONAL (Flask)
# ---------------------------------------------------------
app = Flask(__name__)


@app.route("/consultas", methods=["GET"])
def api_listar():
    return jsonify(agendamentos), 200


@app.route("/consultas", methods=["POST"])
def api_agendar():
    global proximo_id

    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify({"erro": "O corpo da requisição deve ser um JSON válido."}), 400

    campos_obrigatorios = ["paciente", "telefone", "data", "hora"]
    campos_ausentes = [campo for campo in campos_obrigatorios if campo not in dados]
    if campos_ausentes:
        return jsonify({
            "erro": "Campos obrigatórios ausentes.",
            "campos": campos_ausentes,
        }), 400

    paciente = str(dados["paciente"]).strip()
    telefone = str(dados["telefone"]).strip()
    data = str(dados["data"]).strip()
    hora = str(dados["hora"]).strip()

    if not paciente:
        return jsonify({"erro": "O nome do paciente não pode ficar vazio."}), 400

    if not telefone:
        return jsonify({"erro": "O telefone não pode ficar vazio."}), 400

    if not validar_data(data):
        return jsonify({"erro": "Data inválida. Use o formato AAAA-MM-DD."}), 400

    if not validar_horario(hora):
        return jsonify({"erro": "Horário inválido. Use o formato HH:MM."}), 400

    if existe_conflito(data, hora):
        return jsonify({
            "erro": "Já existe uma consulta agendada para esta data e horário. Agende para outro dia ou outro horário."
        }), 409

    novo = {
        "id": proximo_id,
        "paciente": paciente,
        "telefone": telefone,
        "data": data,
        "hora": hora,
        "lembrete_enviado": False,
    }

    agendamentos.append(novo)
    proximo_id += 1
    return jsonify(novo), 201


@app.route("/consultas/<int:id>", methods=["DELETE"])
def api_deletar(id):
    global agendamentos

    consulta_encontrada = any(a["id"] == id for a in agendamentos)
    if not consulta_encontrada:
        return jsonify({
            "status": "erro",
            "mensagem": "Consulta não encontrada.",
        }), 404

    agendamentos = [a for a in agendamentos if a["id"] != id]
    return jsonify({
        "status": "sucesso",
        "mensagem": "Consulta removida via API",
    }), 200


# ---------------------------------------------------------
# 7. INTERFACE DO USUÁRIO (Menu CLI Interativo)
# ---------------------------------------------------------
def menu():
    while True:
        print("\n====================================")
        print("   SISTEMA DE AGENDAMENTO MÉDICO")
        print("====================================")
        print("1. Agendar Nova Consulta")
        print("2. Listar Todas as Consultas")
        print("3. Cancelar Consulta (por ID)")
        print("4. Verificar Lembretes Manualmente")
        print("5. Sair")

        opcao = input("\nEscolha uma opção digitando o número correspondente (1-5): ").strip()

        if opcao == "1":
            nome = input("Nome do Paciente: ").strip()
            tel = input("Telefone com código do país e DDD (ex: +5567999998888): ").strip()
            data = obter_data_validada()
            hora = obter_horario_validado()

            if not nome:
                print("❌ O nome do paciente não pode ficar vazio.")
                continue

            if not tel:
                print("❌ O telefone não pode ficar vazio.")
                continue

            if existe_conflito(data, hora):
                print("❌ Já existe uma consulta agendada para esta data e horário.")
                continue

            global proximo_id
            novo = {
                "id": proximo_id,
                "paciente": nome,
                "telefone": tel,
                "data": data,
                "hora": hora,
                "lembrete_enviado": False,
            }
            agendamentos.append(novo)
            proximo_id += 1
            print(f"✅ Consulta agendada com sucesso para {data} às {hora}!")

        elif opcao == "2":
            print("\n--- LISTA DE AGENDAMENTOS ---")
            if not agendamentos:
                print("Nenhuma consulta agendada.")
            for a in agendamentos:
                status_lembrete = (
                    "🔔 Lembrete enviado"
                    if a["lembrete_enviado"]
                    else "⏳ Aguardando janela de 24h"
                )
                print(
                    f"ID: {a['id']} | Paciente: {a['paciente']} | "
                    f"Tel: {a['telefone']} | Data: {a['data']} {a['hora']} | "
                    f"{status_lembrete}"
                )

        elif opcao == "3":
            cancelar_consulta_cli()

        elif opcao == "4":
            print("\nVerificação manual de lembretes iniciada...")
            verificar_agendamentos_para_notificar()
            print("Verificação concluída.")

        elif opcao == "5":
            print("Encerrando o sistema...")
            break
        else:
            print("❌ Opção inválida! Escolha um número de 1 a 5.")


if __name__ == "__main__":
    # Inicia a API REST Flask em segundo plano.
    Thread(
        target=lambda: app.run(port=5000, debug=False, use_reloader=False),
        daemon=True,
    ).start()

    # Inicia a rotina automática de lembretes.
    Thread(target=rotina_lembretes_automatica, daemon=True).start()

    menu()
