1. Paleta de Cores (Monocromática)

    Background: Branco puro (#FFFFFF) para a área de trabalho.

    Bordas: Cinza muito claro (#EBEBEB ou #F0F0F0). Evite bordas pretas.

    Texto Primário: Preto suave (#1A1A1A ou o #37352F característico do Notion).

    Texto Secundário: Cinza médio (#737373).

    Acentos (Hover/Seleção): Tons de cinza claro (#F5F5F5) para estados de interação.

2. Tipografia e Espaçamento

    Fonte: Use Inter ou system-ui. Peso 500 para títulos e 400 para corpo.

    Hierarchy: Títulos com letter-spacing: -0.02em.

    Whitespace: Aplique a "Lei do Respiro" do Google Labs. Aumente o padding de todos os elementos. Nada deve parecer apertado.

3. Componentes de UI (Especificações)

    Cards (Contatos): Devem ser brancos, com bordas finas (1px solid #EBEBEB). Em vez de tabelas densas, use cartões modulares. Cantos arredondados suaves (border-radius: 8px estilo Notion ou 16px estilo Labs).

    Botões: Estilo "Ghost" ou "Outline". Fundo transparente, borda fina e texto preto. No hover, o fundo torna-se levemente cinza.

    Badges de Status: Fundo cinza muito claro (#F1F1F1) com texto preto. Sem cores vibrantes (use apenas ícones pequenos se precisar diferenciar o status "atrasado").

    Inputs: Minimalistas, apenas com uma borda inferior ou borda completa muito clara, ganhando foco com uma sombra suave (box-shadow: 0 0 0 2px rgba(0,0,0,0.05)).

4. Diretrizes de UX

    Navegação: Sidebar limpa à esquerda com ícones lineares (stroke 1.5px).

    Interatividade: Adicione transições suaves (transition: all 0.2s ease-in-out) em todos os estados de hover.

    Layout: Grid responsivo que se transforma em uma coluna única no mobile, mantendo margens laterais largas no desktop.