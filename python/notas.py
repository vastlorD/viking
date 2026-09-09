"""Calculadora de notas: funções puras e interface de terminal."""

import math


def gerar_relatorio(notas):
    """Recebe notas entre 0 e 10 e devolve média e situação."""
    if not notas:
        raise ValueError("Informe pelo menos uma nota.")
    for nota in notas:
        if (isinstance(nota, bool) or not isinstance(nota, (int, float))
                or not math.isfinite(nota) or not 0 <= nota <= 10):
            raise ValueError("Cada nota deve ser um número entre 0 e 10.")
    media = sum(notas) / len(notas)
    return {"quantidade": len(notas), "media": media,
            "situacao": "Aprovado" if media >= 7 else "Reprovado"}


def main():
    print("Viking — calculadora de notas")
    try:
        entrada = input("Digite notas separadas por espaço (ex.: 8 7 9): ")
        notas = [float(valor.replace(",", ".")) for valor in entrada.split()]
        relatorio = gerar_relatorio(notas)
    except (ValueError, EOFError) as erro:
        print(f"Não foi possível calcular: {erro}")
        return 1
    print(f"Quantidade: {relatorio['quantidade']}")
    print(f"Média: {relatorio['media']:.2f}")
    print(f"Situação: {relatorio['situacao']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
