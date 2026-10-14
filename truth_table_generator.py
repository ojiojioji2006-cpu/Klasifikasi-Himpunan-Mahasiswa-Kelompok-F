"""
===============================================================================
PARSER & GENERATOR TABEL KEBENARAN OTOMATIS (TRUTH TABLE ENGINE v2.0)
Milestone PJBL-1 (Sesi Ke-2) — Matematika Diskrit
-------------------------------------------------------------------------------
Kelompok : F Gyaneswar
Anggota  : 1. Hasdan Fauji  (25210060)
           2. Intan Farida  (25210002)
           3. Riski Maulana (25210051)
Bahasa   : Python 3 (Modul Bawaan: re, itertools, dataclasses, typing)
===============================================================================
"""

from __future__ import annotations
import itertools
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


# =============================================================================
# TAHAP 1: KONFIGURASI KATA KUNCI & STRUKTUR DATA HASIL
# =============================================================================

RESERVED_KEYWORDS = {
    "AND", "OR", "NOT", "XOR", "NAND", "NOR", "IMPLIES", "IFF", "TRUE", "FALSE"
}


@dataclass(frozen=True)
class TruthTableReport:
    """Menyimpan seluruh hasil evaluasi dan analisis tabel kebenaran."""
    raw_expression: str
    normalized_expression: str
    variables: List[str]
    sub_expressions: List[str]
    rows: List[Tuple[Dict[str, bool], Dict[str, bool], bool]]
    classification: str
    true_count: int
    false_count: int
    dnf_expression: str
    cnf_expression: str


# =============================================================================
# TAHAP 2: NORMALISASI OPERATOR & DETEKSI VARIABEL OTOMATIS (REGEX)
# =============================================================================

def normalize_expression(expression_str: str) -> str:
    """
    Menormalisasi variasi input (huruf kecil, simbol ∧, ∨, ¬, ->, <->)
    menjadi operator standar berhuruf kapital.
    """
    if not expression_str or not expression_str.strip():
        raise ValueError("Ekspresi logika tidak boleh kosong.")

    expr = expression_str.strip()

    # Konversi simbol matematika ke operator kata standar
    expr = re.sub(r"<->|<=>|↔|≡", " IFF ", expr)
    expr = re.sub(r"->|=>|→|⇒", " IMPLIES ", expr)
    expr = re.sub(r"&&|&|∧", " AND ", expr)
    expr = re.sub(r"\|\||\|+|∨", " OR ", expr)
    expr = re.sub(r"!|~|¬", " NOT ", expr)
    expr = re.sub(r"\^|⊕|≢", " XOR ", expr)

    # Normalisasi penulisan kata kunci secara case-insensitive
    word_ops = ["AND", "OR", "NOT", "XOR", "NAND", "NOR", "IMPLIES", "IFF", "TRUE", "FALSE"]
    for op in word_ops:
        expr = re.sub(rf"\b{op}\b", op, expr, flags=re.IGNORECASE)

    # Rapikan spasi di sekitar tanda kurung dan spasi berlebih
    expr = re.sub(r"\(\s*", "(", expr)
    expr = re.sub(r"\s*\)", ")", expr)
    expr = re.sub(r"\s+", " ", expr).strip()
    return expr


def tokenize(normalized_expr: str) -> List[str]:
    """Memecah string ekspresi menjadi daftar token (kurung, operator, variabel)."""
    token_pattern = re.compile(r"\(|\)|[A-Za-z_]\w*")
    tokens = token_pattern.findall(normalized_expr)

    # Cek apakah ada karakter asing yang tidak valid
    cleaned_check = token_pattern.sub("", normalized_expr).strip()
    if cleaned_check:
        raise ValueError(f"Terdapat karakter tidak valid dalam ekspresi: '{cleaned_check}'")

    return tokens


def extract_variables(tokens: Sequence[str]) -> List[str]:
    """Mengambil seluruh variabel unik (bukan operator) dan mengurutkannya secara alfabetis."""
    variables = {
        tok for tok in tokens
        if re.match(r"^[A-Za-z_]\w*$", tok) and tok.upper() not in RESERVED_KEYWORDS
    }
    return sorted(variables)


# =============================================================================
# TAHAP 3: ABSTRACT SYNTAX TREE (AST) & RECURSIVE DESCENT PARSER
# =============================================================================

class ASTNode:
    def evaluate(self, env: Dict[str, bool]) -> bool:
        raise NotImplementedError

    def to_canonical(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class VarNode(ASTNode):
    name: str

    def evaluate(self, env: Dict[str, bool]) -> bool:
        return bool(env[self.name])

    def to_canonical(self) -> str:
        return self.name


@dataclass(frozen=True)
class ConstNode(ASTNode):
    value: bool

    def evaluate(self, env: Dict[str, bool]) -> bool:
        return self.value

    def to_canonical(self) -> str:
        return "TRUE" if self.value else "FALSE"


@dataclass(frozen=True)
class UnaryNode(ASTNode):
    op: str
    operand: ASTNode

    def evaluate(self, env: Dict[str, bool]) -> bool:
        val = self.operand.evaluate(env)
        if self.op == "NOT":
            return not val
        raise ValueError(f"Operator unary tidak dikenal: {self.op}")

    def to_canonical(self) -> str:
        inner = self.operand.to_canonical()
        if isinstance(self.operand, BinaryNode):
            return f"NOT ({inner})"
        return f"NOT {inner}"


@dataclass(frozen=True)
class BinaryNode(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode

    def evaluate(self, env: Dict[str, bool]) -> bool:
        l_val = self.left.evaluate(env)
        r_val = self.right.evaluate(env)
        if self.op == "AND":
            return l_val and r_val
        if self.op == "OR":
            return l_val or r_val
        if self.op == "XOR":
            return l_val != r_val
        if self.op == "NAND":
            return not (l_val and r_val)
        if self.op == "NOR":
            return not (l_val or r_val)
        if self.op == "IMPLIES":
            return (not l_val) or r_val
        if self.op == "IFF":
            return l_val == r_val
        raise ValueError(f"Operator biner tidak dikenal: {self.op}")

    def to_canonical(self) -> str:
        l_str = self.left.to_canonical()
        r_str = self.right.to_canonical()
        if isinstance(self.left, BinaryNode) and _precedence(self.left.op) < _precedence(self.op):
            l_str = f"({l_str})"
        if isinstance(self.right, BinaryNode) and _precedence(self.right.op) <= _precedence(self.op):
            if not (self.right.op == self.op and self.op in {"AND", "OR", "XOR"}):
                r_str = f"({r_str})"
        return f"{l_str} {self.op} {r_str}"


def _precedence(op: str) -> int:
    return {
        "IFF": 1,
        "IMPLIES": 2,
        "OR": 3,
        "NOR": 3,
        "XOR": 4,
        "AND": 5,
        "NAND": 5,
        "NOT": 6,
    }.get(op, 0)


class LogicParser:
    """
    Memvalidasi urutan token dan membangun pohon sintaks (AST) sesuai hierarki
    operator logika: Kurung () > NOT > AND/NAND > XOR > OR/NOR > IMPLIES > IFF.
    """

    def __init__(self, tokens: Sequence[str]):
        self.tokens = list(tokens)
        self.pos = 0

    def peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected: str | None = None) -> str:
        tok = self.peek()
        if tok is None:
            raise ValueError("Ekspresi berakhir secara tidak terduga.")
        if expected is not None and tok != expected:
            raise ValueError(f"Diharapkan '{expected}', tetapi ditemukan '{tok}'.")
        self.pos += 1
        return tok

    def parse(self) -> Tuple[ASTNode, List[Tuple[str, ASTNode]]]:
        if not self.tokens:
            raise ValueError("Tidak ada token untuk diparse.")
        root = self._parse_iff()
        if self.peek() is not None:
            raise ValueError(f"Token berlebih atau sintaks tidak valid di dekat '{self.peek()}'.")

        sub_nodes: List[Tuple[str, ASTNode]] = []
        seen = set()

        def collect(node: ASTNode) -> None:
            if isinstance(node, UnaryNode):
                collect(node.operand)
            elif isinstance(node, BinaryNode):
                collect(node.left)
                collect(node.right)

            if isinstance(node, (UnaryNode, BinaryNode)):
                label = node.to_canonical()
                if label not in seen:
                    seen.add(label)
                    sub_nodes.append((label, node))

        collect(root)
        return root, sub_nodes

    def _parse_iff(self) -> ASTNode:
        node = self._parse_implies()
        while self.peek() == "IFF":
            op = self.consume()
            right = self._parse_implies()
            node = BinaryNode(op, node, right)
        return node

    def _parse_implies(self) -> ASTNode:
        node = self._parse_or()
        if self.peek() == "IMPLIES":
            op = self.consume()
            right = self._parse_implies()
            node = BinaryNode(op, node, right)
        return node

    def _parse_or(self) -> ASTNode:
        node = self._parse_xor()
        while self.peek() in {"OR", "NOR"}:
            op = self.consume()
            right = self._parse_xor()
            node = BinaryNode(op, node, right)
        return node

    def _parse_xor(self) -> ASTNode:
        node = self._parse_and()
        while self.peek() == "XOR":
            op = self.consume()
            right = self._parse_and()
            node = BinaryNode(op, node, right)
        return node

    def _parse_and(self) -> ASTNode:
        node = self._parse_unary()
        while self.peek() in {"AND", "NAND"}:
            op = self.consume()
            right = self._parse_unary()
            node = BinaryNode(op, node, right)
        return node

    def _parse_unary(self) -> ASTNode:
        if self.peek() == "NOT":
            op = self.consume()
            operand = self._parse_unary()
            return UnaryNode(op, operand)
        return self._parse_primary()

    def _parse_primary(self) -> ASTNode:
        tok = self.peek()
        if tok is None:
            raise ValueError("Diharapkan variabel atau tanda kurung buka, namun ekspresi habis.")
        if tok == "(":
            self.consume("(")
            node = self._parse_iff()
            if self.peek() != ")":
                raise ValueError("Kurung tutup ')' hilang.")
            self.consume(")")
            return node
        if tok == ")":
            raise ValueError("Kurung tutup ')' tanpa pasangan kurung buka.")
        if tok in RESERVED_KEYWORDS and tok not in {"TRUE", "FALSE"}:
            raise ValueError(f"Operator '{tok}' berada pada posisi yang tidak valid.")

        self.consume()
        if tok == "TRUE":
            return ConstNode(True)
        if tok == "FALSE":
            return ConstNode(False)
        return VarNode(tok)


# =============================================================================
# TAHAP 4: FUNGSI KOMPATIBILITAS LAPORAN PJBL-1 & EVALUATOR KOMBINASI 2^n
# =============================================================================

def tokenize_and_parse(expression_str: str) -> Tuple[str, List[str]]:
    """Fungsi standar sesuai struktur laporan PJBL-1."""
    normalized = normalize_expression(expression_str)
    tokens = tokenize(normalized)
    variables = extract_variables(tokens)
    return normalized, variables


def python_eval_expr(expr: str, var_dict: Dict[str, bool]) -> bool:
    """Mengevaluasi satu baris kombinasi nilai variabel secara aman melalui AST."""
    normalized = normalize_expression(expr)
    tokens = tokenize(normalized)
    root, _ = LogicParser(tokens).parse()
    return root.evaluate(var_dict)


def analyze_expression(expression_str: str) -> TruthTableReport:
    """Membangkitkan 2^n kombinasi dengan itertools.product dan menganalisis hasil."""
    normalized, variables = tokenize_and_parse(expression_str)
    tokens = tokenize(normalized)
    root, sub_nodes = LogicParser(tokens).parse()

    intermediate_nodes = sub_nodes[:-1] if len(sub_nodes) > 1 else []
    sub_labels = [lbl for lbl, _ in intermediate_nodes]

    n = len(variables)
    combinations = list(itertools.product([True, False], repeat=n))

    rows: List[Tuple[Dict[str, bool], Dict[str, bool], bool]] = []
    true_count = 0
    minterms: List[str] = []
    maxterms: List[str] = []

    for combo in combinations:
        var_dict = dict(zip(variables, combo))
        sub_evals = {lbl: node.evaluate(var_dict) for lbl, node in intermediate_nodes}
        final_val = root.evaluate(var_dict)

        rows.append((var_dict, sub_evals, final_val))
        if final_val:
            true_count += 1
            if variables:
                terms = [v if var_dict[v] else f"NOT {v}" for v in variables]
                minterms.append(f"({' AND '.join(terms)})" if len(terms) > 1 else terms[0])
        else:
            if variables:
                terms = [f"NOT {v}" if var_dict[v] else v for v in variables]
                maxterms.append(f"({' OR '.join(terms)})" if len(terms) > 1 else terms[0])

    total_rows = len(combinations)
    false_count = total_rows - true_count

    if true_count == total_rows:
        classification = "TAUTOLOGI (Selalu Benar / True)"
    elif false_count == total_rows:
        classification = "KONTRADIKSI (Selalu Salah / False)"
    else:
        classification = "KONTINGENSI (Campuran True & False)"

    dnf_expr = " OR ".join(minterms) if minterms else "FALSE (Tidak ada Minterm)"
    cnf_expr = " AND ".join(maxterms) if maxterms else "TRUE (Tidak ada Maxterm)"

    return TruthTableReport(
        raw_expression=expression_str,
        normalized_expression=normalized,
        variables=variables,
        sub_expressions=sub_labels,
        rows=rows,
        classification=classification,
        true_count=true_count,
        false_count=false_count,
        dnf_expression=dnf_expr,
        cnf_expression=cnf_expr,
    )


# =============================================================================
# TAHAP 5: RENDERER TABEL CONSOLE UNICODE BOX-DRAWING
# =============================================================================

def format_unicode_table(
    report: TruthTableReport,
    show_steps: bool = True,
    symbol_mode: str = "TF",
) -> str:
    """Mencetak bingkai metadata dan tabel kebenaran bergaris Unicode rapi."""
    t_sym, f_sym = ("1", "0") if symbol_mode == "10" else ("T", "F")
    n = len(report.variables)
    total = 2 ** n

    sub_cols = report.sub_expressions if show_steps else []
    headers = report.variables + sub_cols + [report.normalized_expression]
    col_widths = [max(len(h), 3) + 2 for h in headers]

    def build_border(left: str, mid: str, right: str, fill: str = "─") -> str:
        return left + mid.join(fill * w for w in col_widths) + right

    top_border = build_border("┌", "┬", "┐")
    header_sep = build_border("╞", "╪", "╡", "═")
    bottom_border = build_border("└", "┴", "┘")

    lines: List[str] = []
    box_width = max(len(top_border), 68)
    val_width = box_width - 24

    lines.append("╭" + "─" * (box_width - 2) + "╮")
    title = "PARSER & GENERATOR TABEL KEBENARAN OTOMATIS"
    lines.append(f"│{title:^{box_width - 2}}│")
    lines.append("├" + "─" * (box_width - 2) + "┤")
    lines.append(f"│  Ekspresi Input    : {report.raw_expression:<{val_width}}│")
    lines.append(f"│  Bentuk Normalisasi: {report.normalized_expression:<{val_width}}│")
    var_str = f"{', '.join(report.variables)} (n = {n})" if report.variables else "(Konstanta, n = 0)"
    lines.append(f"│  Variabel Unik     : {var_str:<{val_width}}│")
    comb_str = f"2^{n} = {total} Kombinasi ({report.true_count} True, {report.false_count} False)"
    lines.append(f"│  Jumlah Baris      : {comb_str:<{val_width}}│")
    lines.append(f"│  Klasifikasi       : {report.classification:<{val_width}}│")
    lines.append("╰" + "─" * (box_width - 2) + "╯")
    lines.append("")

    lines.append(top_border)
    header_cells = [f"{h:^{w}}" for h, w in zip(headers, col_widths)]
    lines.append("│" + "│".join(header_cells) + "│")
    lines.append(header_sep)

    for var_dict, sub_evals, final_val in report.rows:
        row_cells: List[str] = []
        for idx, var in enumerate(report.variables):
            val_str = t_sym if var_dict[var] else f_sym
            row_cells.append(f"{val_str:^{col_widths[idx]}}")

        offset = len(report.variables)
        for idx, sub_lbl in enumerate(sub_cols):
            val_str = t_sym if sub_evals[sub_lbl] else f_sym
            row_cells.append(f"{val_str:^{col_widths[offset + idx]}}")

        res_str = t_sym if final_val else f_sym
        row_cells.append(f"{res_str:^{col_widths[-1]}}")
        lines.append("│" + "│".join(row_cells) + "│")

    lines.append(bottom_border)
    return "\n".join(lines)


def generate_truth_table(
    expression_str: str,
    show_steps: bool = True,
    symbol_mode: str = "TF",
) -> TruthTableReport:
    """Fungsi utama untuk mencetak tabel kebenaran ke terminal."""
    report = analyze_expression(expression_str)
    print(format_unicode_table(report, show_steps=show_steps, symbol_mode=symbol_mode))
    print()
    return report


def interactive_cli() -> None:
    """Mode interaktif di terminal untuk menguji rumus bebas."""
    print("\nKetik ekspresi logika (contoh: p AND (q OR NOT r) atau (p -> q) <-> (!q -> !p))")
    print("Ketik 'keluar' atau 'exit' untuk berhenti.\n")
    while True:
        try:
            user_input = input("Masukkan Ekspresi > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSesi selesai.")
            break

        if not user_input or user_input.lower() in {"exit", "quit", "keluar", "q"}:
            print("Sesi selesai.")
            break

        try:
            generate_truth_table(user_input, show_steps=True)
        except ValueError as err:
            print(f"[Kesalahan Sintaks] {err}\n")


if __name__ == "__main__":
    # Pengujian 1 (Sesuai Laporan PJBL-1)
    generate_truth_table("p AND (q OR NOT r)", show_steps=True)

    # Pengujian 2 (Sesuai Laporan PJBL-1)
    generate_truth_table("(p AND q) OR (NOT p AND r)", show_steps=True)

    # Jalankan prompt interaktif jika diberi flag -i atau --interactive
    if "--interactive" in sys.argv or "-i" in sys.argv:
        interactive_cli()