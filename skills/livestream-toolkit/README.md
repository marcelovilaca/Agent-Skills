# Kit de lives e vídeos para YouTube

Guia do skill Hermes para preparar lives, entrevistas, vídeos longos e Shorts em português brasileiro. O fluxo produz materiais editoriais e conceitos/arte de thumbnail quando há ferramenta de imagem disponível; não publica no YouTube por conta própria.

Consulte o [SKILL.md](SKILL.md) para o procedimento completo.

## How to Use

Inicie com `/livestream-toolkit`, “prepare uma live”, “prepare um vídeo” ou um pedido equivalente. Informe o formato, tema, público, apresentador/convidados, data e horário com fuso, e links de fontes ou transcrição, quando disponíveis. Pule dados que ainda não foram definidos; o skill deve perguntar o necessário em etapas curtas.

Exemplos:

- `Prepare uma live de entrevista sobre [tema], com [convidados], em [data/hora/fuso].`
- `Prepare um vídeo longo a partir desta transcrição: [texto ou arquivo].`
- `Sugira Shorts a partir deste vídeo/transcrição e destes timecodes: [material].`

Em entrevistas ao vivo, revise e aprove o resumo editorial antes da produção de imagens. Para vídeo longo, forneça roteiro, transcrição ou vídeo acessível. Para Shorts com cortes específicos, forneça timecodes observáveis. O pacote pode incluir títulos, descrição SEO, hashtags/tags, gancho, pauta/roteiro, perguntas, enquete, Superchat, comentário fixado e conceitos visuais, conforme o formato.

## Technical Details

- **Idioma e escopo:** português brasileiro; fluxos para lives/entrevistas, vídeos gravados longos e Shorts.
- **Pesquisa:** use ferramentas de busca e leitura de páginas disponíveis; registre URLs e datas, diferencie fatos confirmados de hipóteses e não invente notícias atuais nem dados de tendências.
- **SEO:** para lives e vídeos longos, o skill define seis títulos, descrição de 50–100 palavras, cinco hashtags e dez tags; os requisitos de Shorts são mais curtos e dependem do material fornecido. Veja o detalhe completo no `SKILL.md`.
- **Thumbnails:** após aprovação do resumo/conceitos e do texto exato, use Hermes `image_generate` quando disponível. Gere composições separadas sem texto: `landscape` para 16:9 e `portrait` para 9:16; o formato não garante dimensões em pixels, então verifique os arquivos e marque redimensionamento/exportação pendente se não forem exatamente 1280×720 ou 720×1280. Use imagens de referência somente com autorização. Adicione texto apenas com editor realmente disponível; não confie em texto gerado dentro da imagem.
- **Saídas:** os projetos de live usam a estrutura de pesquisa, editorial, SEO, thumbnails, engajamento e checklists especificada no `SKILL.md`. Vídeos longos e Shorts ficam separados em `videos/` e `shorts/`.
- **Código auxiliar ausente:** o arquivo de origem recebido continha apenas `SKILL.md`. `scripts/toolkit.py`, `scripts/thumbnail.py` e os documentos de referência suplementares não foram fornecidos. Não alegue executar validação, empacotamento, busca de imagens ou renderização de texto desses arquivos; use ferramentas existentes ou marque a etapa como pendente.
- **Publicação:** não há integração de upload/agendamento do YouTube incluída. Só avance para publicar ou agendar com integração autorizada e confirmação explícita do conteúdo e destino.

## Limites e revisão

Não invente capítulos, trechos ou timestamps: use apenas os observados no vídeo/transcrição. Não afirme ter gerado imagens, verificado URLs, enviado conteúdo, obtido pontuação VidIQ ou consultado tendências sem ter feito a ação. Antes de entregar, confira nomes, datas/fuso, acentos, direitos de uso, fontes, legendas, links e cada item marcado como concluído.
