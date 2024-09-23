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
def media_mensagens_diarias_por_contato(mensagens, file):
    from collections import defaultdict

    mensagens_por_dia = defaultdict(lambda: defaultdict(int))
    usuarios = set()

    for data_str, hora_str, usuario, _ in mensagens:
        data = datetime.strptime(data_str, '%d/%m/%Y')
        mensagens_por_dia[usuario][data] += 1
        usuarios.add(usuario)

    medias = {}
    for usuario in usuarios:
        total_mensagens = sum(mensagens_por_dia[usuario].values())
        dias_participados = len(mensagens_por_dia[usuario])
        medias[usuario] = total_mensagens / dias_participados if dias_participados else 0

    file.write("Média de mensagens diárias por contato:\n")
    for usuario, media in medias.items():
        file.write(f"{usuario}: {media:.2f} mensagens por dia\n")
    file.write("\n")


def numero_palavras_por_pessoa(mensagens, file):
    contador_palavras = Counter()
    for _, _, usuario, conteudo in mensagens:
        if len(conteudo) <= 500:
            palavras = conteudo.split()
            contador_palavras[usuario] += len(palavras)
    file.write("Número de palavras enviadas por cada participante (ignorando mensagens com mais de 500 caracteres):\n")
    for usuario, total_palavras in contador_palavras.items():
        file.write(f"{usuario}: {total_palavras} palavras\n")
    file.write("\n")

def tempo_resposta_medio(mensagens, file):
    tempos_resposta = {}
    ultimas_mensagens = {}

    for data_str, hora_str, usuario, _ in mensagens:
        tempo_atual = datetime.strptime(f'{data_str} {hora_str}', '%d/%m/%Y %H:%M')
        for outro_usuario in ultimas_mensagens:
            if outro_usuario != usuario:
                delta = (tempo_atual - ultimas_mensagens[outro_usuario]).total_seconds()
                if usuario not in tempos_resposta:
                    tempos_resposta[usuario] = []
                tempos_resposta[usuario].append(delta)
        ultimas_mensagens[usuario] = tempo_atual

    medias_resposta = {usuario: sum(tempos)/len(tempos) for usuario, tempos in tempos_resposta.items() if tempos}
    file.write("Tempo de resposta médio de cada usuário (em segundos):\n")
    for usuario, media in medias_resposta.items():
        file.write(f"{usuario}: {media:.2f} segundos\n")
    file.write("\n")

def conexoes_entre_membros(mensagens, file):
    conexoes = Counter()
    for i in range(1, len(mensagens)):
        usuario_anterior = mensagens[i-1][2]
        usuario_atual = mensagens[i][2]
        if usuario_anterior != usuario_atual:
            par = (usuario_anterior, usuario_atual)
            conexoes[par] += 1
    file.write("Conexões entre membros (quem interage mais com quem):\n")
    for (usuario1, usuario2), freq in conexoes.most_common():
        file.write(f"{usuario1} -> {usuario2}: {freq} interações\n")
    file.write("\n")
def uso_girias_abreviacoes(mensagens, file):
    girias = ['blz', 'vc', 'pq', 'tb', 'td', 'q', 'kd', 'n', 'vlw', 'vlr', 'qq', 'eh', 'krl', 'mano', 'ta', 'tá', 'tmj', 'vlw', 'vcs', 'tbm', 'blz', 'aff', 'kkkk', 'kkk']
    contagem_girias = Counter()

    for _, _, usuario, conteudo in mensagens:
        palavras = conteudo.lower().split()
        count = sum(palavras.count(giria) for giria in girias)
        contagem_girias[usuario] += count

    file.write("Uso de gírias e abreviações por participante:\n")
    for usuario, total in contagem_girias.items():
        file.write(f"{usuario}: {total} gírias/abreviações\n")
    file.write("\n")
def nivel_formalidade(mensagens, file):
    formalidade_por_usuario = {}

    for _, _, usuario, conteudo in mensagens:
        palavras = conteudo.split()
        total_palavras = len(palavras)
        if total_palavras == 0:
            continue
        palavras_formais = sum(1 for palavra in palavras if palavra.istitle())
        porcentagem_formal = (palavras_formais / total_palavras) * 100

        if usuario not in formalidade_por_usuario:
            formalidade_por_usuario[usuario] = []

        formalidade_por_usuario[usuario].append(porcentagem_formal)

    file.write("Nível de formalidade por participante (baseado no uso de palavras iniciadas com maiúsculas):\n")
    for usuario, formalidades in formalidade_por_usuario.items():
        media_formalidade = sum(formalidades) / len(formalidades)
        file.write(f"{usuario}: {media_formalidade:.2f}% palavras formais\n")
    file.write("\n")
def analise_estilo_escrita(mensagens, file):
    estilo_por_usuario = {}

    for _, _, usuario, conteudo in mensagens:
        num_maiusculas = sum(1 for c in conteudo if c.isupper())
        num_caracteres = len(conteudo)
        num_pontuacao = sum(1 for c in conteudo if c in '.,!?;:')
        if num_caracteres == 0:
            continue

        porcentagem_maiusculas = (num_maiusculas / num_caracteres) * 100
        porcentagem_pontuacao = (num_pontuacao / num_caracteres) * 100

        if usuario not in estilo_por_usuario:
            estilo_por_usuario[usuario] = {'maiusculas': [], 'pontuacao': []}

        estilo_por_usuario[usuario]['maiusculas'].append(porcentagem_maiusculas)
        estilo_por_usuario[usuario]['pontuacao'].append(porcentagem_pontuacao)

    file.write("Análise do estilo de escrita de cada usuário (uso de maiúsculas e pontuação):\n")
    for usuario, dados in estilo_por_usuario.items():
        media_maiusculas = sum(dados['maiusculas']) / len(dados['maiusculas'])
        media_pontuacao = sum(dados['pontuacao']) / len(dados['pontuacao'])
        file.write(f"{usuario}: {media_maiusculas:.2f}% maiúsculas, {media_pontuacao:.2f}% pontuação\n")
    file.write("\n")
def erros_ortograficos_por_pessoa(mensagens, file):
    from spellchecker import SpellChecker

    spell = SpellChecker(language='pt')
    erros_por_usuario = Counter()

    for _, _, usuario, conteudo in mensagens:
        palavras = conteudo.split()
        erros = spell.unknown(palavras)
        erros_por_usuario[usuario] += len(erros)

    file.write("Quantidade de erros ortográficos por pessoa:\n")
    for usuario, total_erros in erros_por_usuario.items():
        file.write(f"{usuario}: {total_erros} erros\n")
    file.write("\n")
def analise_sentimento(mensagens, file):
    from transformers import pipeline

    # Carregando o modelo de análise de sentimento em português
    sentiment_analysis = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment", framework="pt")


    sentimento_por_usuario = {'Positivo': Counter(), 'Negativo': Counter(), 'Neutro': Counter()}

    for _, _, usuario, conteudo in mensagens:
        try:
            resultado = sentiment_analysis(conteudo[:512])[0]  # Limitar a 512 caracteres
            label = resultado['label']
            if 'positive' in label.lower():
                sentimento_por_usuario['Positivo'][usuario] += 1
            elif 'negative' in label.lower():
                sentimento_por_usuario['Negativo'][usuario] += 1
            else:
                sentimento_por_usuario['Neutro'][usuario] += 1
        except Exception:
            continue  # Ignorar erros na análise

    file.write("Análise de sentimento por usuário:\n")
    for sentimento, usuarios in sentimento_por_usuario.items():
        file.write(f"\nSentimento {sentimento}:\n")
        for usuario, count in usuarios.items():
            file.write(f"{usuario}: {count} mensagens\n")
    file.write("\n")
def palavras_carinhosas_por_pessoa(mensagens, file):
    palavras_carinhosas = ['parabéns', 'obrigado', 'valeu', 'bom trabalho', 'gostei', 'amigo', 'amiga', 'querido', 'querida', 'saudades', 'desculpa', 'amo', 'adoro']
    contagem_carinhosas = Counter()

    for _, _, usuario, conteudo in mensagens:
        palavras = conteudo.lower().split()
        count = sum(palavras.count(palavra) for palavra in palavras_carinhosas)
        contagem_carinhosas[usuario] += count

    file.write("Uso de palavras carinhosas ou de incentivo por usuário:\n")
    for usuario, total in contagem_carinhosas.items():
        file.write(f"{usuario}: {total} palavras carinhosas\n")
    file.write("\n")
def expressoes_frustracao_por_pessoa(mensagens, file):
    expressoes_frustracao = ['estressado', 'cansado', 'não aguento', 'chateado', 'raiva', 'triste', 'irritado', 'frustrado', 'pior', 'odeio']
    contagem_frustracao = Counter()

    for _, _, usuario, conteudo in mensagens:
        palavras = conteudo.lower().split()
        count = sum(palavras.count(exp) for exp in expressoes_frustracao)
        contagem_frustracao[usuario] += count

    file.write("Expressões de frustração ou desabafo por usuário:\n")
    for usuario, total in contagem_frustracao.items():
        file.write(f"{usuario}: {total} expressões de frustração\n")
    file.write("\n")
def mensagens_mais_citadas(mensagens, file):
    padrao_citacao = re.compile(r'^".+"$')
    citacoes = Counter()

    for _, _, _, conteudo in mensagens:
        if padrao_citacao.match(conteudo):
            citacoes[conteudo] += 1

    mensagens_mais_citadas = citacoes.most_common(5)
    file.write("Mensagens mais respondidas ou citadas:\n")
    for mensagem, count in mensagens_mais_citadas:
        file.write(f"\"{mensagem}\": {count} citações\n")
    file.write("\n")
def mensagem_mais_longa(mensagens, file):
    mensagem_maior = max(mensagens, key=lambda x: len(x[3]))
    usuario = mensagem_maior[2]
    conteudo = mensagem_maior[3]
    tamanho = len(conteudo)
    file.write(f"Mensagem mais longa enviada por {usuario} ({tamanho} caracteres):\n")
    file.write(f"{conteudo}\n\n")
def recorde_mensagens_em_um_dia(mensagens, file):
    mensagens_por_dia = Counter()
    usuarios_por_dia = {}

    for data_str, _, usuario, _ in mensagens:
        data = datetime.strptime(data_str, '%d/%m/%Y').date()
        mensagens_por_dia[data] += 1
        if data not in usuarios_por_dia:
            usuarios_por_dia[data] = Counter()
        usuarios_por_dia[data][usuario] += 1

    dia_recorde, total_mensagens = mensagens_por_dia.most_common(1)[0]
    usuarios_no_dia = usuarios_por_dia[dia_recorde]

    file.write(f"Recorde de mensagens em um dia ({dia_recorde}): {total_mensagens} mensagens\n")
    file.write("Participação dos usuários nesse dia:\n")
    for usuario, count in usuarios_no_dia.items():
        file.write(f"{usuario}: {count} mensagens\n")
    file.write("\n")


def processar_mensagens(dados):
    mensagens = []
    padrao_mensagem = re.compile(r'^(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2}) - (.*?): (.*)$')

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
        # Parseando a data e hora com o formato correto
        tempo_atual = datetime.strptime(f'{data} {hora}', '%d/%m/%Y %H:%M')
        
        if ultimo_usuario and usuario != ultimo_usuario:
            diferenca = (tempo_atual - ultimo_tempo).total_seconds()
            if usuario not in tempos_resposta:
                tempos_resposta[usuario] = []
            tempos_resposta[usuario].append(diferenca)
        
        ultimo_usuario = usuario
        ultimo_tempo = tempo_atual

    # Calculando a média de tempo de resposta para cada usuário
    medias_resposta = {
        usuario: sum(tempos) / len(tempos)
        for usuario, tempos in tempos_resposta.items() if tempos
    }

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
        data = datetime.strptime(mensagem[0], '%d/%m/%Y')
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
        # Análises existentes
        figurinha_mais_usada, ocorrencias_figurinhas = encontrar_figurinha_recorrente(pasta_midia, file)
        file.write(f"Figurinha mais usada: {figurinha_mais_usada}, Ocorrências: {ocorrencias_figurinhas}\n\n")

        maiores_audios = encontrar_audios_maiores(pasta_audio, file)
        file.write("Maiores arquivos de áudio:\n")
        for i, (arquivo, tamanho) in enumerate(maiores_audios, start=1):
            file.write(f"{i}. {arquivo} - Tamanho: {tamanho / 1024:.2f} KB\n")
        file.write("\n")

        usuario_que_faz_mais_perguntas(mensagens, file)

        max_mensagens_seguidas, seq_usuarios = mensagens_seguidas(mensagens, file)
        file.write("Top 5 usuários com mais mensagens seguidas:\n")
        top5_mensagens_seguidas = Counter(max_mensagens_seguidas).most_common(5)
        for i, (usuario, max_msgs) in enumerate(top5_mensagens_seguidas, start=1):
            media_seguidas = sum(seq_usuarios[usuario]) / len(seq_usuarios[usuario]) if usuario in seq_usuarios else 0
            file.write(f"{i}. {usuario} - Máx: {max_msgs} mensagens seguidas, Média: {media_seguidas:.2f}\n")
        file.write("\n")

        pontuacao_usuarios_mais_engracados(mensagens, file)
        top_emojis_usados(mensagens, file)
        menor_tempo_resposta(mensagens, file)
        palavra_mais_usada_por_pessoa(mensagens, file)
        palavra_mais_falada_no_grupo(mensagens, file)
        periodo_mais_ativo(mensagens, file)
        soma_mensagens_por_periodo(mensagens, file)
        mensagens_por_mes(mensagens, file)

        # Novas análises
        media_mensagens_diarias_por_contato(mensagens, file)
        numero_palavras_por_pessoa(mensagens, file)
        tempo_resposta_medio(mensagens, file)
        conexoes_entre_membros(mensagens, file)
        uso_girias_abreviacoes(mensagens, file)
        nivel_formalidade(mensagens, file)
        analise_estilo_escrita(mensagens, file)
        erros_ortograficos_por_pessoa(mensagens, file)
        analise_sentimento(mensagens, file)
        palavras_carinhosas_por_pessoa(mensagens, file)
        expressoes_frustracao_por_pessoa(mensagens, file)
        mensagens_mais_citadas(mensagens, file)
        mensagem_mais_longa(mensagens, file)
        recorde_mensagens_em_um_dia(mensagens, file)

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
