import re
import os
import hashlib
import emoji
from collections import Counter
from datetime import datetime

# Função para calcular o hash de um arquivo (usado para identificar figurinhas duplicadas)
def calcular_hash_arquivo(caminho_arquivo):
    hash_md5 = hashlib.md5()
    with open(caminho_arquivo, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Função para encontrar a figurinha mais recorrente em uma pasta
def encontrar_figurinha_recorrente(pasta, file):
    figurinhas = []
    hash_para_arquivo = {}
    if not os.path.exists(pasta):
        file.write(f"A pasta '{pasta}' não existe.\n")
        return None, None
    for arquivo in os.listdir(pasta):
        caminho_arquivo = os.path.join(pasta, arquivo)
        if arquivo.lower().endswith('.webp'):
            try:
                hash_arquivo = calcular_hash_arquivo(caminho_arquivo)
                figurinhas.append(hash_arquivo)
                hash_para_arquivo[hash_arquivo] = caminho_arquivo
            except Exception as e:
                file.write(f"Erro ao processar {arquivo}: {e}\n")
    contador_figurinhas = Counter(figurinhas)
    if contador_figurinhas:
        hash_mais_recorrente, ocorrencias = contador_figurinhas.most_common(1)[0]
        return hash_para_arquivo[hash_mais_recorrente], ocorrencias
    return None, None

# Função para encontrar os N arquivos de áudio .opus mais longos em uma pasta com base no tamanho do arquivo
def encontrar_audios_maiores(pasta, file, quantidade=10):
    audios = []
    if not os.path.exists(pasta):
        file.write(f"A pasta '{pasta}' não existe.\n")
        return []
    for arquivo in os.listdir(pasta):
        caminho_arquivo = os.path.join(pasta, arquivo)
        if arquivo.lower().endswith('.opus'):
            try:
                tamanho = os.path.getsize(caminho_arquivo)
                audios.append((arquivo, tamanho))
            except Exception as e:
                file.write(f"Erro ao processar {arquivo}: {e}\n")
    audios_ordenados = sorted(audios, key=lambda x: x[1], reverse=True)
    return audios_ordenados[:quantidade]

# Função para processar e limpar os dados (removendo datas, horas, etc.)
# Função para processar e limpar os dados (removendo datas, horas, etc.)
def processar_mensagens(dados):
    mensagens = []
    padrao_mensagem = re.compile(r'\[(\d{2}/\d{2}/\d{2}), (\d{2}:\d{2}:\d{2})\] (.*?): (.*)')
    for linha in dados:
        resultado = padrao_mensagem.match(linha)
        if resultado:
            data = resultado.group(1)
            hora = resultado.group(2)
            usuario = resultado.group(3)
            mensagem = resultado.group(4)
            mensagens.append([data, hora, usuario, mensagem])
    return mensagens


# Função para contar quem manda mais mensagens seguidas
def mensagens_seguidas(mensagens, file):
    usuario_anterior = ''
    contador = 0
    max_mensagens = {}
    seq_usuarios = {}
    for _, _, usuario, _ in mensagens:
        if usuario == usuario_anterior:
            contador += 1
        else:
            if usuario_anterior:
                max_mensagens[usuario_anterior] = max(max_mensagens.get(usuario_anterior, 0), contador)
                if contador > 3:
                    seq_usuarios[usuario_anterior] = seq_usuarios.get(usuario_anterior, []) + [contador]
            usuario_anterior = usuario
            contador = 1
    return max_mensagens, seq_usuarios

# Função para identificar o usuário mais engraçado
def pontuacao_usuarios_mais_engracados(mensagens, file):
    padrao_risada = re.compile(r'(k{2,}|ha{2,}|rs{2,}|😂|🤣)', re.IGNORECASE)
    pontuacao_risadas = Counter()
    for i in range(1, len(mensagens)):
        usuario_atual, mensagem_atual = mensagens[i-1][2], mensagens[i][3]
        if padrao_risada.search(mensagem_atual):
            pontuacao_risadas[usuario_atual] += 1
    file.write("Pontuação dos usuários mais engraçados:\n")
    for usuario, pontos in pontuacao_risadas.most_common():
        file.write(f"{usuario}: {pontos} risadas\n")
    file.write("\n")

# Função para encontrar os emojis mais usados (Top 3)
def top_emojis_usados(mensagens, file, top_n=3):
    todos_emojis = ''.join([char for mensagem in mensagens for char in mensagem[3] if emoji.is_emoji(char)])
    contagem_emojis = Counter(todos_emojis)
    emojis_mais_usados = contagem_emojis.most_common(top_n)
    file.write("Top 3 emojis mais usados:\n")
    for emoji_char, count in emojis_mais_usados:
        file.write(f"{emoji_char}: {count} vezes\n")
    file.write("\n")

# Função para calcular o menor tempo de resposta (média)
def menor_tempo_resposta(mensagens, file):
    tempos_resposta = {}
    ultimo_usuario = None
    ultimo_tempo = None
    for i, (data, hora, usuario, _) in enumerate(mensagens):
        tempo_atual = datetime.strptime(f'{data} {hora}', '%d/%m/%y %H:%M:%S')  # Atualização no formato de data/hora
        if ultimo_usuario and usuario != ultimo_usuario:
            diferenca = (tempo_atual - ultimo_tempo).total_seconds()
            if usuario not in tempos_resposta:
                tempos_resposta[usuario] = []
            tempos_resposta[usuario].append(diferenca)
        ultimo_usuario = usuario
        ultimo_tempo = tempo_atual
    medias_resposta = {usuario: sum(tempos) / len(tempos) for usuario, tempos in tempos_resposta.items() if tempos}
    file.write("Média de tempo de resposta entre usuários (em segundos):\n")
    for usuario, media in medias_resposta.items():
        file.write(f"{usuario}: {media:.2f} segundos\n")
    file.write("\n")

# Função para identificar a palavra mais usada por pessoa, ignorando arquivos e mídias
def palavra_mais_usada_por_pessoa(mensagens, file, min_length=4):
    palavras_por_usuario = {}
    ignorar_mensagens = ["(arquivo", "<mídia", "whatsapp"]

    for mensagem in mensagens:
        usuario = mensagem[2]
        conteudo = mensagem[3].lower()

        # Ignorar completamente mensagens com palavras-chave como "(arquivo)" ou "<mídia>"
        if any(ignorar in conteudo for ignorar in ignorar_mensagens):
            continue

        palavras = [palavra for palavra in conteudo.split() if len(palavra) >= min_length]

        if usuario not in palavras_por_usuario:
            palavras_por_usuario[usuario] = Counter(palavras)
        else:
            palavras_por_usuario[usuario].update(palavras)

    file.write("Palavra mais usada por cada pessoa (ignorando arquivos e mídias):\n")
    for usuario, contagem in palavras_por_usuario.items():
        if contagem:  # Somente mostrar se houver palavras válidas
            palavra_top = contagem.most_common(1)[0][0]
        else:
            palavra_top = "Nenhuma palavra"
        file.write(f"{usuario}: {palavra_top}\n")
    file.write("\n")
# Função para identificar a palavra mais falada no grupo, ignorando arquivos e mídias
def palavra_mais_falada_no_grupo(mensagens, file, min_length=4):
    todas_palavras = []
    ignorar_mensagens = ["(arquivo", "<mídia", "whatsapp"]

    for mensagem in mensagens:
        conteudo = mensagem[3].lower()

        # Ignorar completamente mensagens com palavras-chave como "(arquivo)" ou "<mídia>"
        if any(ignorar in conteudo for ignorar in ignorar_mensagens):
            continue

        palavras = [palavra for palavra in conteudo.split() if len(palavra) >= min_length]
        todas_palavras.extend(palavras)

    contagem_palavras = Counter(todas_palavras)
    if contagem_palavras:
        palavra_top = contagem_palavras.most_common(1)[0]
        file.write(f"Palavra mais falada no grupo: {palavra_top[0]} (usada {palavra_top[1]} vezes)\n\n")
    else:
        file.write("Nenhuma palavra válida encontrada no grupo.\n\n")

# Função para determinar o período mais ativo do dia (manhã, tarde, noite, madrugada)
def periodo_mais_ativo(mensagens, file):
    periodos = {'Madrugada': 0, 'Manhã': 0, 'Tarde': 0, 'Noite': 0}
    for mensagem in mensagens:
        hora = int(mensagem[1][:2])
        if 0 <= hora < 6:
            periodos['Madrugada'] += 1
        elif 6 <= hora < 12:
            periodos['Manhã'] += 1
        elif 12 <= hora < 18:
            periodos['Tarde'] += 1
        else:
            periodos['Noite'] += 1
    periodo_mais_frequente = max(periodos, key=periodos.get)
    file.write(f"Período mais ativo do grupo: {periodo_mais_frequente}\n\n")
# Função para contar a quantidade de mensagens por período do dia
def soma_mensagens_por_periodo(mensagens, file):
    periodos = {'Madrugada': 0, 'Manhã': 0, 'Tarde': 0, 'Noite': 0}

    for mensagem in mensagens:
        hora = int(mensagem[1][:2])
        if 0 <= hora < 6:
            periodos['Madrugada'] += 1
        elif 6 <= hora < 12:
            periodos['Manhã'] += 1
        elif 12 <= hora < 18:
            periodos['Tarde'] += 1
        else:
            periodos['Noite'] += 1

    # Grava no arquivo o resumo da contagem de mensagens por período
    file.write("Soma de mensagens por período do dia:\n")
    for periodo, contagem in periodos.items():
        file.write(f"{periodo}: {contagem} mensagens\n")
    file.write("\n")

# Função para contar mensagens por mês
def mensagens_por_mes(mensagens, file):
    contagem_mensal = Counter()
    for mensagem in mensagens:
        data = datetime.strptime(mensagem[0], '%d/%m/%y')  # Alteração para aceitar ano com dois dígitos
        mes_ano = data.strftime('%Y-%m')
        contagem_mensal[mes_ano] += 1
    file.write("Quantidade de mensagens por mês:\n")
    for mes, contagem in sorted(contagem_mensal.items()):
        file.write(f"{mes}: {contagem} mensagens\n")
    file.write("\n")

# Função para encontrar o usuário que faz mais perguntas
def usuario_que_faz_mais_perguntas(mensagens, file):
    perguntas = [msg for msg in mensagens if '?' in msg[3]]  # Verifica se a mensagem contém "?"
    contagem_perguntas = Counter([msg[2] for msg in perguntas])  # Conta quantas perguntas cada usuário fez
    usuario_top = contagem_perguntas.most_common(1)[0] if contagem_perguntas else ('Ninguém', 0)
    
    # Gravar no arquivo
    file.write(f"Usuário que mais faz perguntas: {usuario_top[0]} com {usuario_top[1]} perguntas\n\n")

# Função para salvar todas as análises em um arquivo de texto
# Função para salvar todas as análises em um arquivo de texto
def salvar_resumo_txt(nome_arquivo, mensagens, pasta_midia, pasta_audio):
    with open(nome_arquivo, 'w', encoding='utf-8') as file:
        # Encontrar figurinha mais usada
        figurinha_mais_usada, ocorrencias_figurinhas = encontrar_figurinha_recorrente(pasta_midia, file)
        file.write(f"Figurinha mais usada: {figurinha_mais_usada}, Ocorrências: {ocorrencias_figurinhas}\n\n")


        # Encontrar os maiores áudios
        maiores_audios = encontrar_audios_maiores(pasta_audio, file)
        file.write("Maiores arquivos de áudio:\n")
        for i, (arquivo, tamanho) in enumerate(maiores_audios, start=1):
            file.write(f"{i}. {arquivo} - Tamanho: {tamanho / 1024:.2f} KB\n")
        file.write("\n")

        # Análise de perguntas
        usuario_que_faz_mais_perguntas(mensagens, file)

        # Outras análises
        max_mensagens_seguidas, seq_usuarios = mensagens_seguidas(mensagens, file)
        file.write("Top 5 usuários com mais mensagens seguidas:\n")
        top5_mensagens_seguidas = Counter(max_mensagens_seguidas).most_common(5)
        for i, (usuario, max_msgs) in enumerate(top5_mensagens_seguidas, start=1):
            media_seguidas = sum(seq_usuarios[usuario]) / len(seq_usuarios[usuario]) if usuario in seq_usuarios else 0
            file.write(f"{i}. {usuario} - Máx: {max_msgs} mensagens seguidas, Média: {media_seguidas:.2f}\n")
        file.write("\n")

        # Outras análises
        pontuacao_usuarios_mais_engracados(mensagens, file)
        top_emojis_usados(mensagens, file)
        menor_tempo_resposta(mensagens, file)
        palavra_mais_usada_por_pessoa(mensagens, file)
        palavra_mais_falada_no_grupo(mensagens, file)
        periodo_mais_ativo(mensagens, file)

        # Adicionando a soma das mensagens por período
        soma_mensagens_por_periodo(mensagens, file)

        mensagens_por_mes(mensagens, file)
        file.write("Análises concluídas e salvas no arquivo.\n")

# Função para carregar o arquivo de conversa
def carregar_conversa(arquivo_conversa):
    with open(arquivo_conversa, 'r', encoding='utf-8') as f:
        dados = f.readlines()
    return processar_mensagens(dados)

# Função principal para execução da análise
def executar_analise():
    arquivo_conversa = 'conversa.txt'  # Substitua pelo caminho correto do seu arquivo
    pasta_midia = 'pastaconversa'  # Substitua pelo caminho da sua pasta de mídia
    pasta_audio = 'pastaconversa'  # Substitua pelo caminho da sua pasta de áudios
    mensagens = carregar_conversa(arquivo_conversa)
    salvar_resumo_txt('resumo_analises_final.txt', mensagens, pasta_midia, pasta_audio)

# Execução da análise
executar_analise()
