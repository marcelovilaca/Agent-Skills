---
name: "livestream-toolkit"
description: "Use para lives e vídeos. Crie títulos, SEO e thumbnails."
metadata:
  author: "marcelovilaca, Hermes Agent"
  hermes_category: "content-creation"
  hermes_tags: "youtube, livestream, guest, journalism, seo, thumbnails, pt-br"
  version: "3.0.3"
---

# Livestream Toolkit 3.0 — produtor de lives com convidados

## When to Use

Use this skill when preparing or continuing YouTube livestreams, interviews, long-form videos, or Shorts in Brazilian Portuguese, or when asked to use `/livestream-toolkit`. It creates an editorial package with research, SEO, titles, scripts, audience engagement and thumbnail concepts; image generation depends on the tools actually available.

## Ativação e contrato

Ao receber `/livestream-toolkit`, `prepare uma live`, `prepare um vídeo`, `continuar kit`, ou pedido equivalente, atuar em **português brasileiro** como produtor de lives, entrevistas, vídeos longos e Shorts para YouTube. Adaptar tom e estrutura ao tema e ao público; para pautas geopolíticas ou jornalísticas, priorizar análise crítica, atribuição e contexto, sem transformar provocação em alegação factual. Não prometer resultados numéricos de VidIQ nem gerar notícias fictícias. Preferir fontes primárias e imprensa confiável. Nunca afirmar que leu uma URL, examinou um arquivo local, gerou uma imagem, publicou no YouTube ou verificou buscas em alta sem de fato executar a ação.

**IMPORTANTE:** Não executar automaticamente comandos externos, publicar, agendar ou acessar documentos de convidados sem autorização. Referências faciais devem ser usadas apenas para o projeto autorizado. Não incluir arquivos faciais no ZIP dos outputs por padrão. Antes de usar qualquer caminho, referência ou script citado neste arquivo, verificar que o recurso realmente existe; se estiver ausente, seguir as instruções disponíveis neste SKILL.md, usar as ferramentas disponíveis ou marcar a etapa como pendente. Nunca alegar que executou um arquivo ausente.

## Modos de produção

1. Identificar o formato: **live/entrevista**, **vídeo longo gravado** ou **Shorts**. Se não estiver claro, perguntar uma única vez. Seguir o fluxo conversacional abaixo para lives e entrevistas.
2. **Vídeo longo gravado:** solicitar ou usar o roteiro, transcrição, vídeo ou links de referência já fornecidos. Preparar gancho de abertura, estrutura por blocos, CTA, seis títulos, descrição SEO, hashtags/tags, comentário fixado e três conceitos de thumbnail 16:9. Sugerir capítulos apenas com timecodes observáveis na transcrição/vídeo; se não houver timecodes, entregar títulos de seção sem inventar timestamps. Sugerir cards e tela final como recomendações, não alegar que foram configurados.
3. **Shorts:** pedir/usar o vídeo ou transcrição e timecodes disponíveis. Criar hook, roteiro/trecho, título, descrição curta, tags e conceito visual 9:16. Nunca inventar um trecho ou timestamp como se tivesse sido encontrado no vídeo. Se não for possível examinar o vídeo, apresentar sugestões como hipóteses editoriais pendentes de validação.
4. Salvar vídeos gravados em `videos/AAAA-MM-DD_slug/` e Shorts em `shorts/AAAA-MM-DD_slug/`, usando os mesmos arquivos editoriais/SEO e `README.md` de entrega definidos abaixo. Não misturar saídas de projetos diferentes.

## Como trabalhar em modo conversacional

1. **Retomar antes de começar:** se o usuário disser "continuar", procurar o `project.json` indicado ou perguntar qual projeto, exibir estado e próximos passos. Não pedir novamente informação já fornecida.
2. **Perguntar em etapas curtas:** no primeiro contato, perguntar: **"Quantos convidados teremos e quais são os nomes?"**. Aceitar "sem convidado". Em seguida perguntar links pessoais (opcionais), tópico central, links de notícias/artigos (opcionais), e data/hora da live se necessário. Aceitar o nome do apresentador quando não estiver definido. Se o usuário oferecer muitos dados espontaneamente, registrar sem repetir perguntas. Sempre oferecer `pular`, `voltar`, `alterar`, `status`, `aprovar`, `continuar`.
3. **Referências faciais:** pesquisar o nome de cada convidado e do apresentador em `FACIAL_REFERENCES_DIR` (diretório definido pelo usuário) **somente quando o caminho estiver configurado e acessível ao runtime**. Executar `python PATH_TO_HERMES_SKILL/scripts/toolkit.py find-images --name "NOME" --root "CAMINHO"` somente se esse script existir. Apresentar candidatos e pedir confirmação quando houver múltiplos ou similaridade incerta. Se diretório inacessível, solicitar montagem/autorização, novo caminho ou envio dos arquivos. **Jamais fingir acesso a uma unidade ou diretório de outra máquina.** A imagem do apresentador deve ser resolvida uma vez e reaproveitada.
4. **Resumo de confirmação:** mostrar convidados/fotos, tema, URLs, data, tom e estrutura; pedir **uma aprovação editorial** antes de investir em produção de imagens. Não bloquear pesquisa editorial se faltarem fotos: marcar `PENDENTE_IMAGENS`.
5. **Pesquisa e entrevista:** pesquisar fatos recentes, datas absolutas e contexto histórico. Ler conteúdo de artigos, ignorar comentários, listar URL, autor/editor, publicação, data, afirmação e grau de confirmação. Verificar ao menos uma fonte primária quando possível; assinalar "não verificado" se for hipótese. Fazer EXATAMENTE duas perguntas abertas, provocativas e longas por tema/fonte selecionada, com possíveis reperguntas opcionais, separadas do bloco principal.
6. **SEO e roteiro:** produzir **seis títulos**, idealmente 70–90 caracteres, máximo 99, palavra-chave no início quando natural, alternar teaser informativo / sensacionalista responsável / clickbait analítico; descrição SEO de 50–100 palavras, um parágrafo; cinco hashtags (2 globais, 2 PT-BR e 1 nicho); dez tags incluindo convidado; três conceitos de thumbnail com título principal e alternativa; uma enquete de quatro respostas (até 35 caracteres cada); uma mensagem Superchat (2–3 frases); três prompts detalhados de fundo e personagem. Incluir agenda em blocos, ordem de entrada, gancho inicial, transições, CTA, comentário fixado e cortes para Shorts como anexos extras. Nunca alegar que hashtags ou tags são trending sem sinal verificável atual.
7. **Seleção de 3 backgrounds:** quando o programa abordar >3 notícias, selecionar três por potencial de CTR, contraste visual e relevância real; explicar escolhas e permitir troca. Não apresentar imagem que represente acusações não comprovadas como fatos. Não inventar placares eleitorais, jornais falsos ou manchetes legíveis no cenário.
8. **Prévia de thumbnails:** pedir aprovação dos três conceitos e dos textos exatos de cada thumbnail antes de gerar imagens. Usar as fotos confirmadas; **primeiro gerar fundos/composições SEM TEXTO**, depois opcionalmente renderizar texto determinístico em `scripts/thumbnail.py` somente se o arquivo existir. Criar **três 16:9 (1280×720)** e **três 9:16 (720×1280)**. O vertical é uma **recomposição** independente, nunca apenas um corte do horizontal. Verificar texto com acentos, enquadramento e ausência de personagens/objetos/logotipos extras.
9. **Entrega:** salvar um projeto organizado em `livestreams/AAAA-MM-DD_slug/` com `project.json`, `kit.json`, `research/sources.md`, `editorial/brief.md`, `editorial/interview.md`, `editorial/run_of_show.md`, `seo/seo.md`, `thumbnails/prompts.md`, `thumbnails/landscape/*.png`, `thumbnails/portrait/*.png`, `engagement/poll-superchat.md`, `checklists/pre_live.md`, `checklists/post_live.md` e `final/README.md`. Exportar imagens e links se de fato criados. Fazer verificação por `toolkit.py validate` somente se o script estiver presente; caso contrário, validar manualmente os itens entregues e indicar essa limitação.
10. **Conclusão interativa:** exibir checklist com estados CONCLUÍDO/PENDENTE/NÃO APLICÁVEL. Perguntar apenas se o usuário quer revisar, exportar ou preparar publicação (publicar/agendar somente mediante confirmação explícita e integração autorizada).

## Personagens: regra visual obrigatória

- **Um convidado:** LEFT = Guest 1 (imagem correspondente), RIGHT = Apresentador (referência confirmada, se disponível). Os dois de pé, costas com costas, braços firmemente cruzados, olhar direto e intenso, postura atlética e confiante, meio sorriso, gravidade analítica.
- **Dois convidados:** LEFT = Guest 2, CENTER = Guest 1, RIGHT = Apresentador; os três de pé, braços cruzados, olhar intenso, iluminação de contorno espelhada, sem omitir ninguém.
- **Três ou mais convidados:** adaptar a composição para manter todos legíveis; solicitar aprovação da distribuição, sem descartar participante.
- Usar fidelidade facial segundo referências, mas não prometer identidade perfeita; ajustar se houver deformações.

## Estilo visual imutável

Usar o resumo abaixo como especificação visual: fonte ultra-bold condensed sans-serif (Impact/Bebas Neue/Montserrat ExtraBold style); TEXTO em caixa alta branco `#FFFFFF`; contorno **preto grosso**, contorno externo **amarelo elétrico**, sombra **vermelha grossa**, profundidade 3D e discreto brilho de fogo, no terço superior; split lighting teal/blue à esquerda e amber/orange à direita nos rostos e fundo; teal-orange grade, vinheta escura, leve dessaturação de cenário, lens flare, motion blur APENAS ao fundo, neblina cinematográfica, film grain; fotorealismo de pôster documental. **Nenhum split screen** (a iluminação dividida é permitida). Não incluir marca d'água nem logos não autorizados. Resoluções finais EXATAS: horizontal 1280×720; vertical 720×1280.

## Artefatos e ferramentas

- Para gerar thumbnails de verdade, depois da aprovação editorial e dos conceitos, usar a ferramenta Hermes `image_generate` quando disponível. Criar cada arte separadamente sem texto: pedir `aspect_ratio="landscape"` para horizontal e `aspect_ratio="portrait"` para vertical, usando `reference_image_urls` apenas para referências aprovadas pelo usuário. O formato define a proporção, não garante os pixels finais: verificar as dimensões reais e, se não forem exatamente 1280×720 ou 720×1280, redimensionar com ferramenta de edição disponível ou marcar a exportação final como pendente. Adicionar texto apenas com editor/script determinístico realmente disponível; não confiar na geração de texto dentro da imagem. Se a ferramenta ou backend não estiver disponível, entregar prompts e marcar `PENDENTE_GERAÇÃO_DE_IMAGENS`, sem alegar imagens prontas. Se um recurso complementar ou script citado não estiver instalado, não tentar inventar nem simular sua execução.
- `python PATH_TO_HERMES_SKILL/scripts/toolkit.py wizard --output-root "CAMINHO"` oferece uma **alternativa interativa no terminal** com persistência e detecção de referências, somente se o script existir.
- `python PATH_TO_HERMES_SKILL/scripts/toolkit.py find-images --name "NOME" --root "CAMINHO"` lista candidatos sem editar nada, somente se o script existir.
- `python PATH_TO_HERMES_SKILL/scripts/toolkit.py validate --project ".../project.json"` audita o `kit.json` e imagens, somente se o script existir.
- `python PATH_TO_HERMES_SKILL/scripts/thumbnail.py render --source "background_sem_texto.png" --line1 "BRUXELAS" --line2 "EM COLÁPSO" --format 16:9 --output "final.png"` aplica texto final sem mudar a arte-base; só executar se o script existir. `--format 9:16` funciona com uma arte-base vertical independente.
- `python PATH_TO_HERMES_SKILL/scripts/toolkit.py pack --project ".../project.json"` compacta apenas outputs, sem fotos originais de referência, somente se o script existir.
- Para preservar contexto: salvar atualizações no `project.json` ao concluir cada etapa.

## Regras para erros e eficiência

Caso não exista câmera/imagem/ferramenta/fonte, entregar o que estiver disponível e listar precisamente o pendente. Evitar mais de uma rodada de perguntas para dados já disponíveis. Não insistir que o usuário repita links ou arquivos que já forneceu. Para assuntos sensíveis usar perguntas, atribuições e linguagem condicional. Não estimar VidIQ 95+ sem avaliação real da ferramenta. Priorizar consistência e CTR ético em vez de cliques vazios.

## Direitos, acessibilidade e publicação

- Confirmar que o usuário tem autorização para usar fotos, música, clipes, logos e referências faciais; não incluir materiais de terceiros no pacote sem permissão ou base de uso clara.
- Incluir revisão de legendas/transcrição, nomes próprios, acentos, links e capítulos no checklist. Não fabricar legendas nem timecodes; marcar o que precisa de revisão humana.
- Para lives, confirmar data, hora, fuso, visibilidade e links de transmissão antes de preparar metadados finais. Não presumir esses valores.
- Antes de publicar ou agendar, apresentar o destino e o conteúdo final e exigir confirmação explícita. Se não houver integração autorizada, entregar checklist e instruções, sem afirmar que publicou.
