import unittest
from unittest.mock import patch

import importlib.util
from pathlib import Path

ARQUIVO = Path(__file__).with_name("Sistema_de_Agendamento_com_Lembrete_Automatico_Versao_Final_Outubro.py")
spec = importlib.util.spec_from_file_location("sistema", ARQUIVO)
sistema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sistema)


class TestSistemaAgendamento(unittest.TestCase):
    def setUp(self):
        sistema.agendamentos.clear()
        sistema.proximo_id = 1
        self.client = sistema.app.test_client()

    def test_get_lista_vazia(self):
        resposta = self.client.get("/consultas")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json(), [])

    def test_post_agendamento_valido(self):
        resposta = self.client.post("/consultas", json={
            "paciente": "Ana",
            "telefone": "+5567999999999",
            "data": "2030-01-10",
            "hora": "10:30",
        })
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.get_json()["id"], 1)

    def test_post_rejeita_campo_obrigatorio_ausente(self):
        resposta = self.client.post("/consultas", json={
            "paciente": "Ana",
            "telefone": "+5567999999999",
            "data": "2030-01-10",
        })
        self.assertEqual(resposta.status_code, 400)

    def test_post_rejeita_data_invalida(self):
        resposta = self.client.post("/consultas", json={
            "paciente": "Ana",
            "telefone": "+5567999999999",
            "data": "10-01-2030",
            "hora": "10:30",
        })
        self.assertEqual(resposta.status_code, 400)

    def test_post_rejeita_horario_invalido(self):
        resposta = self.client.post("/consultas", json={
            "paciente": "Ana",
            "telefone": "+5567999999999",
            "data": "2030-01-10",
            "hora": "25:90",
        })
        self.assertEqual(resposta.status_code, 400)

    def test_post_rejeita_conflito_de_horario(self):
        dados = {
            "paciente": "Ana",
            "telefone": "+5567999999999",
            "data": "2030-01-10",
            "hora": "10:30",
        }
        primeira = self.client.post("/consultas", json=dados)
        segunda = self.client.post("/consultas", json={**dados, "paciente": "Bruno"})
        self.assertEqual(primeira.status_code, 201)
        self.assertEqual(segunda.status_code, 409)

    def test_delete_consulta_existente(self):
        resposta = self.client.post("/consultas", json={
            "paciente": "Ana",
            "telefone": "+5567999999999",
            "data": "2030-01-10",
            "hora": "10:30",
        })
        consulta_id = resposta.get_json()["id"]
        resposta_delete = self.client.delete(f"/consultas/{consulta_id}")
        self.assertEqual(resposta_delete.status_code, 200)

    def test_delete_consulta_inexistente(self):
        resposta = self.client.delete("/consultas/999")
        self.assertEqual(resposta.status_code, 404)

    @patch.object(sistema, "Client")
    def test_envio_de_lembrete_com_sucesso(self, mock_client):
        mock_message = mock_client.return_value.messages.create.return_value
        mock_message.sid = "TEST-SID"

        agendamento = {
            "id": 1,
            "paciente": "Ana",
            "telefone": "+5567999999999",
            "data": "2030-01-10",
            "hora": "10:30",
            "lembrete_enviado": False,
        }

        resultado = sistema.enviar_lembrete_24h(agendamento)
        self.assertTrue(resultado)
        mock_client.return_value.messages.create.assert_called_once()

    def test_post_rejeita_json_invalido(self):
        resposta = self.client.post(
            "/consultas",
            data="isto nao e json",
            content_type="application/json",
        )
        self.assertEqual(resposta.status_code, 400)


if __name__ == "__main__":
    unittest.main()
