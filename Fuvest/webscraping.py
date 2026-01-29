import pdfplumber
import re
from collections import defaultdict

# ===============================
# CONFIGURAÇÃO
# ===============================

PDF_ARQUIVO = "fuvest_aprovados.pdf"

CURSOS_LN = {
    "305-10", "307-15", "309-20",
    "309-21", "309-22", "309-23",
    "201-02"
}

PADRAO_CPF = re.compile(r"\d{3}\.\d{3}")
PADRAO_CURSO = re.compile(r"\d{3}[−–—-]\d{2}")

# ===============================
# FUNÇÕES
# ===============================


def normalizar(texto: str) -> str:
    return (
        texto
        .replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
        .strip()
    )

# ===============================
# EXTRAÇÃO
# ===============================

resultado = defaultdict(list)

with pdfplumber.open(PDF_ARQUIVO) as pdf:
    for num_pagina, pagina in enumerate(pdf.pages, start=1):
        print(f"Processando página {num_pagina}...")

        palavras = pagina.extract_words(
            use_text_flow=False,
            keep_blank_chars=False
        )

        # Agrupa por linha (posição Y)
        linhas = defaultdict(list)
        for p in palavras:
            y = round(p["top"], 1)
            linhas[y].append(p)

        for y in linhas:
            # Reconstrói a linha (esquerda → direita)
            linha = " ".join(
                p["text"] for p in sorted(linhas[y], key=lambda x: x["x0"])
            )

            linha = normalizar(linha)

            # percorre TODOS os CPFs da linha (ou seja, os três CPFs)
            for cpf_match in PADRAO_CPF.finditer(linha):
                inicio_nome = 0
                fim_nome = cpf_match.start()

                anteriores = list(PADRAO_CPF.finditer(linha[:cpf_match.start()])) # pega tudo antes do CPF atual
                if anteriores:
                    inicio_nome = anteriores[-1].end() # se tiver um CPF antes do nome ele vai ser identificado, como a marcação do começo do nome 

                nome = linha[inicio_nome:fim_nome].strip()

                # 🔥 LIMPA curso da coluna à esquerda
                nome = re.sub(r"^\d{3}-\d{2}\s*", "", nome)

                # curso = primeiro código à direita do CPF, a procura depois do cpf se deve ao uso de .end
                curso_match = PADRAO_CURSO.search(linha, cpf_match.end())
                if not curso_match:
                    continue

                codigo = curso_match.group()

                if codigo in CURSOS_LN and nome:
                    resultado[codigo].append(nome)

# ===============================
# SAÍDA
# ===============================

with open("aprovados_lorena.txt", "w", encoding="utf-8") as f:
    for curso in sorted(resultado):
        f.write(f"\n===== CURSO {curso} =====\n")
        for nome in resultado[curso]:
            f.write(nome + "\n")

print("\nExtração concluída com sucesso ✅")
