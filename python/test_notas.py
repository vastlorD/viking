import unittest

from notas import gerar_relatorio


class TestNotas(unittest.TestCase):
    def test_media_e_quantidade(self):
        self.assertEqual(gerar_relatorio([8, 7, 9]),
                         {"quantidade": 3, "media": 8, "situacao": "Aprovado"})

    def test_limite_de_aprovacao(self):
        self.assertEqual(gerar_relatorio([7])["situacao"], "Aprovado")
        self.assertEqual(gerar_relatorio([6.999])["situacao"], "Reprovado")

    def test_extremos_validos(self):
        self.assertEqual(gerar_relatorio([0, 10])["media"], 5)

    def test_entradas_invalidas(self):
        for notas in ([], [-1], [11], [float("nan")], [float("inf")], [True], ["8"]):
            with self.subTest(notas=notas), self.assertRaises(ValueError):
                gerar_relatorio(notas)


if __name__ == "__main__":
    unittest.main()
