"""Portuguese (pt-BR) message templates for deck analysis output.

Single source of truth for the user-facing strings that used to be hardcoded
inline in app/analysis/deck_analyzer.py. Analysis code should produce
IssueCode/StrengthCode + params; rendering to text happens here.
"""

from app.analysis.issue_codes import IssueCode, StrengthCode

ISSUE_TEMPLATES = {
    IssueCode.EMPTY_DECK: "Deck vazio.",
    IssueCode.MISSING_SPELL: "Sem feitiço - adiciona versatilidade e utilidade.",
    IssueCode.MISSING_LIGHT_SPELL: (
        "Sem feitiço leve (Zap/Tronco) - considere adicionar para ciclar "
        "rápido e defender de enxames."
    ),
    IssueCode.NO_WIN_CONDITION: (
        "Sem condição de vitória - seu deck precisa de um dano primário."
    ),
    IssueCode.NO_AIR_DEFENSE: (
        "Sem defesa aérea - vulnerável a unidades voadoras (Dragão, Balão, etc.)."
    ),
    IssueCode.ELIXIR_TOO_HIGH: (
        "Elixir muito alto ({avg_elixir}) - deck pode sofrer pra ciclar e contra-atacar."
    ),
    IssueCode.ELIXIR_TOO_LOW: (
        "Elixir muito baixo ({avg_elixir}) - pode carecer de poder defensivo."
    ),
    IssueCode.INCOMPLETE_DECK_SYNC: (
        "⚠️ API retornou deck incompleto ({card_count}/8 cartas). Isso costuma "
        "acontecer por atraso de sincronização do servidor logo após uma "
        "batalha recente. Jogue uma partida rápida e tente novamente em "
        "alguns minutos."
    ),
    IssueCode.RARITY_CLUSTERING: (
        "Muitas cartas {rarity} ({count}) - pode sofrer com variância de nível."
    ),
}

STRENGTH_TEMPLATES = {
    StrengthCode.WELL_ROUNDED: (
        "Bem balanceado com tanque + suporte + condição de vitória."
    ),
    StrengthCode.GOOD_SPELL_COVERAGE: (
        "Boa cobertura de feitiços para utilidade e versatilidade."
    ),
    StrengthCode.GOOD_AIR_DEFENSE: "Boa defesa aérea e cobertura de feitiços.",
    StrengthCode.BALANCED_CURVE: (
        "Curva de elixir balanceada ({avg_elixir}) - bom potencial de ciclo."
    ),
}


def render_issue(code: IssueCode, **params) -> str:
    """Render an IssueCode into its pt-BR message, interpolating params."""
    return ISSUE_TEMPLATES[code].format(**params)


def render_strength(code: StrengthCode, **params) -> str:
    """Render a StrengthCode into its pt-BR message, interpolating params."""
    return STRENGTH_TEMPLATES[code].format(**params)
