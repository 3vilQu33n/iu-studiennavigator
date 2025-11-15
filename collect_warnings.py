# analyze_all_warnings.py
"""
Vollständige Projekt-Analyse: Findet ALLE PyCharm-ähnlichen Warnings
und exportiert sie in eine strukturierte .txt Datei
"""
import ast
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Tuple


class ComprehensiveWarningAnalyzer:
    """Analysiert Python-Code auf verschiedene Warnings"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.warnings = defaultdict(list)
        self.stats = defaultdict(int)

    def analyze_project(self):
        """Analysiert alle Python-Dateien"""
        print("🔍 Starte vollständige Projekt-Analyse...\n")

        python_files = self._get_python_files()
        print(f"📁 Gefunden: {len(python_files)} Python-Dateien\n")

        for py_file in sorted(python_files):
            rel_path = py_file.relative_to(self.project_root)
            print(f"  Analysiere: {rel_path}")
            self._analyze_file(py_file, rel_path)

        print(f"\n✅ Analyse abgeschlossen!\n")

    def _get_python_files(self) -> List[Path]:
        """Findet alle Python-Dateien"""
        return [
            f for f in self.project_root.rglob("*.py")
            if not any(skip in str(f) for skip in [
                'venv', '.venv', '__pycache__', 'site-packages',
                'fix_', 'analyze_', 'collect_'
            ])
        ]

    def _analyze_file(self, filepath: Path, rel_path: Path):
        """Analysiert eine einzelne Datei"""
        try:
            content = filepath.read_text(encoding='utf-8')
            lines = content.split('\n')

            # 1. Syntax Check
            try:
                tree = ast.parse(content, filename=str(filepath))
            except SyntaxError as e:
                self._add_warning('SYNTAX_ERROR', rel_path, e.lineno,
                                  f"Syntax Error: {e.msg}")
                return

            # 2. Code Style Checks
            self._check_line_length(lines, rel_path)
            self._check_trailing_whitespace(lines, rel_path)
            self._check_missing_whitespace(lines, rel_path)

            # 3. Type Hints & Documentation
            self._check_type_hints(tree, content, rel_path)

            # 4. Naming Conventions
            self._check_naming(tree, rel_path)

            # 5. Code Quality
            self._check_duplicates(lines, rel_path)
            self._check_unused_imports(tree, content, rel_path)

            # 6. Specific Patterns
            self._check_shadowing(tree, rel_path)
            self._check_undefined_variables(content, lines, rel_path)

        except Exception as e:
            self._add_warning('FILE_ERROR', rel_path, 0,
                              f"Error analyzing file: {str(e)}")

    def _check_line_length(self, lines: List[str], filepath: Path):
        """Prüft Zeilenlänge (PEP 8: max 79, praktisch: max 120)"""
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                self._add_warning('LINE_TOO_LONG', filepath, i,
                                  f"Line too long ({len(line)} > 120 characters)")

    def _check_trailing_whitespace(self, lines: List[str], filepath: Path):
        """Prüft auf trailing whitespace"""
        for i, line in enumerate(lines, 1):
            if line.rstrip() != line and line.strip():
                self._add_warning('TRAILING_WHITESPACE', filepath, i,
                                  "Trailing whitespace")

    def _check_missing_whitespace(self, lines: List[str], filepath: Path):
        """Prüft auf fehlende Leerzeichen (z.B. nach Komma)"""
        for i, line in enumerate(lines, 1):
            # Komma ohne Leerzeichen danach (außer in Strings)
            if re.search(r',[^\s\n\)]', line) and '"' not in line and "'" not in line:
                self._add_warning('MISSING_WHITESPACE', filepath, i,
                                  "Missing whitespace after ','")

    def _check_type_hints(self, tree: ast.AST, content: str, filepath: Path):
        """Prüft auf fehlende Type Hints"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Prüfe Parameter ohne Type Hints
                for arg in node.args.args:
                    if arg.arg != 'self' and arg.annotation is None:
                        self._add_warning('MISSING_TYPE_HINT', filepath, node.lineno,
                                          f"Parameter '{arg.arg}' has no type hint")

                # Prüfe Return Type Hint
                if node.returns is None and node.name not in ['__init__', '__str__', '__repr__']:
                    self._add_warning('MISSING_RETURN_TYPE', filepath, node.lineno,
                                      f"Function '{node.name}' has no return type hint")

    def _check_naming(self, tree: ast.AST, filepath: Path):
        """Prüft Naming Conventions (PEP 8)"""
        for node in ast.walk(tree):
            # Funktionsnamen sollten snake_case sein
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_') and not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                    self._add_warning('NAMING_CONVENTION', filepath, node.lineno,
                                      f"Function name '{node.name}' should be snake_case")

            # Klassennamen sollten PascalCase sein
            elif isinstance(node, ast.ClassDef):
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    self._add_warning('NAMING_CONVENTION', filepath, node.lineno,
                                      f"Class name '{node.name}' should be PascalCase")

    def _check_duplicates(self, lines: List[str], filepath: Path):
        """Sucht nach duplizierten Code-Blöcken (vereinfacht)"""
        # Minimum 10 Zeilen für Duplikat
        min_lines = 10
        seen_blocks = {}

        for i in range(len(lines) - min_lines):
            block = '\n'.join(lines[i:i + min_lines])
            block_hash = hash(block)

            if block_hash in seen_blocks and block.strip():
                self._add_warning('DUPLICATED_CODE', filepath, i + 1,
                                  f"Duplicated code fragment ({min_lines}+ lines)")
                seen_blocks[block_hash].append(i)
            else:
                seen_blocks[block_hash] = [i]

    def _check_unused_imports(self, tree: ast.AST, content: str, filepath: Path):
        """Prüft auf ungenutzte Imports (vereinfacht)"""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports.append((name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports.append((name, node.lineno))

        for import_name, lineno in imports:
            # Sehr vereinfachte Check: kommt Import-Name im Rest des Codes vor?
            pattern = rf'\b{re.escape(import_name)}\b'
            occurrences = len(re.findall(pattern, content))

            # Wenn nur 1x vorkommt (= nur im Import selbst)
            if occurrences <= 1:
                self._add_warning('UNUSED_IMPORT', filepath, lineno,
                                  f"Unused import: '{import_name}'")

    def _check_shadowing(self, tree: ast.AST, filepath: Path):
        """Prüft auf Shadowing von Namen"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef):
                # Prüfe ob Name built-in shadowed
                builtins = ['id', 'type', 'list', 'dict', 'set', 'str', 'int',
                            'float', 'input', 'open', 'file', 'filter', 'map']
                if node.name in builtins:
                    self._add_warning('SHADOWING', filepath, node.lineno,
                                      f"Shadows built-in name '{node.name}'")

    def _check_undefined_variables(self, content: str, lines: List[str], filepath: Path):
        """Prüft auf undefined variables in __all__"""
        for i, line in enumerate(lines, 1):
            if '__all__' in line and '=' in line:
                # Extrahiere Namen aus __all__
                match = re.search(r'__all__\s*=\s*\[(.*?)\]', line)
                if match:
                    names = re.findall(r"['\"](\w+)['\"]", match.group(1))
                    for name in names:
                        if f'def {name}' not in content and f'class {name}' not in content:
                            self._add_warning('UNDEFINED_VARIABLE', filepath, i,
                                              f"'{name}' is not declared in __all__")

    def _add_warning(self, category: str, filepath: Path, line: int, message: str):
        """Fügt eine Warning hinzu"""
        self.warnings[category].append({
            'file': str(filepath),
            'line': line,
            'message': message
        })
        self.stats[category] += 1

    def generate_report(self, output_file: str = "all_warnings_report.txt"):
        """Erstellt detaillierten Report"""
        output_path = self.project_root / output_file

        with output_path.open('w', encoding='utf-8') as f:
            self._write_header(f)
            self._write_summary(f)
            self._write_warnings_by_file(f)
            self._write_warnings_by_category(f)
            self._write_footer(f)

        print(f"📄 Report erstellt: {output_path.absolute()}\n")

    def _write_header(self, f):
        """Schreibt Report Header"""
        f.write("=" * 100 + "\n")
        f.write("DASHBOARD PROJECT - VOLLSTÄNDIGE WARNING-ANALYSE\n")
        f.write(f"Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 100 + "\n\n")

    def _write_summary(self, f):
        """Schreibt Zusammenfassung"""
        f.write("📊 ZUSAMMENFASSUNG\n")
        f.write("-" * 100 + "\n\n")

        total = sum(self.stats.values())
        f.write(f"Gesamt-Warnings: {total}\n\n")

        if self.stats:
            f.write("Warnings nach Kategorie:\n")
            for category, count in sorted(self.stats.items(), key=lambda x: x[1], reverse=True):
                category_name = category.replace('_', ' ').title()
                f.write(f"  {count:4d}  {category_name}\n")
        else:
            f.write("  ✅ Keine Warnings gefunden!\n")

        f.write("\n\n")

    def _write_warnings_by_file(self, f):
        """Schreibt Warnings gruppiert nach Datei"""
        f.write("📁 WARNINGS NACH DATEI\n")
        f.write("=" * 100 + "\n\n")

        # Gruppiere nach Datei
        by_file = defaultdict(list)
        for category, warning_list in self.warnings.items():
            for warning in warning_list:
                by_file[warning['file']].append({
                    'category': category,
                    'line': warning['line'],
                    'message': warning['message']
                })

        # Sortiere und schreibe
        for filepath in sorted(by_file.keys()):
            warnings = sorted(by_file[filepath], key=lambda x: x['line'])
            f.write(f"\n{'─' * 100}\n")
            f.write(f"FILE: {filepath} ({len(warnings)} warnings)\n")
            f.write(f"{'─' * 100}\n\n")

            for warning in warnings:
                category_short = warning['category'].replace('_', ' ')
                f.write(f"  Line {warning['line']:4d} | [{category_short}]\n")
                f.write(f"           {warning['message']}\n\n")

    def _write_warnings_by_category(self, f):
        """Schreibt Warnings gruppiert nach Kategorie"""
        f.write("\n\n")
        f.write("🏷️  WARNINGS NACH KATEGORIE\n")
        f.write("=" * 100 + "\n\n")

        for category in sorted(self.warnings.keys()):
            warnings = self.warnings[category]
            if not warnings:
                continue

            f.write(f"\n{'─' * 100}\n")
            f.write(f"[{category.replace('_', ' ').upper()}] ({len(warnings)} warnings)\n")
            f.write(f"{'─' * 100}\n\n")

            for warning in sorted(warnings, key=lambda x: (x['file'], x['line']))[:50]:
                f.write(f"  {warning['file']}:{warning['line']}\n")
                f.write(f"    → {warning['message']}\n\n")

            if len(warnings) > 50:
                f.write(f"  ... und {len(warnings) - 50} weitere\n\n")

    def _write_footer(self, f):
        """Schreibt Footer"""
        f.write("\n" + "=" * 100 + "\n")
        f.write("ENDE DES REPORTS\n")
        f.write("=" * 100 + "\n")


def main():
    print("=" * 100)
    print("🔍 VOLLSTÄNDIGE PROJEKT-ANALYSE - ALLE WARNINGS")
    print("=" * 100)
    print()

    project_root = Path(__file__).parent

    analyzer = ComprehensiveWarningAnalyzer(project_root)
    analyzer.analyze_project()
    analyzer.generate_report("all_warnings_report.txt")

    print("=" * 100)
    print("✅ FERTIG!")
    print("=" * 100)
    print()
    print("📄 Report wurde erstellt: all_warnings_report.txt")
    print()
    print("Der Report enthält:")
    print("  • Alle Warnings mit Datei-Pfad und Zeilennummer")
    print("  • Gruppierung nach Datei und Kategorie")
    print("  • Detaillierte Statistiken")
    print()


if __name__ == "__main__":
    main()