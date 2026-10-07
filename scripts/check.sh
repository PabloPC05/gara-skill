#!/usr/bin/env bash
# Comprueba la coherencia del bundle: frontmatter, copias de referencias y enlaces.
set -u
cd "$(dirname "$0")/.."
fail=0
err() { echo "ERROR: $*"; fail=1; }

field() { # field <archivo> <clave>: valor del frontmatter, sin comillas
  awk -v k="$2" 'NR==1&&$0!="---"{exit} NR>1&&$0=="---"{exit} index($0,k":")==1{sub(k": *","");gsub(/^"|"$/,"");print;exit}' "$1"
}

for dir in skills/*/; do
  name=$(basename "$dir"); file="$dir/SKILL.md"
  [ -f "$file" ] || { err "$dir sin SKILL.md"; continue; }
  [ "$(field "$file" name)" = "$name" ] || err "$file: name no coincide con la carpeta"
  [ -n "$(field "$file" description)" ] || err "$file: falta description"
  case "$name" in gara-*) ;; *) err "$dir: el nombre debe empezar por gara-" ;; esac
done

for file in agents/*.md; do
  name=$(basename "$file" .md)
  [ "$(field "$file" name)" = "$name" ] || err "$file: name no coincide con el archivo"
  [ -n "$(field "$file" description)" ] || err "$file: falta description"
  [ "$(field "$file" model)" = "inherit" ] || err "$file: model debe ser inherit"
  [ "$(field "$file" disallowedTools)" = "Agent" ] || err "$file: debe declarar disallowedTools: Agent"
done

# Las referencias de cada skill son copias de las fuentes compartidas.
for dir in skills/*/; do
  for pair in "gara.md:profiles/gara.md" "flujo.md:references/flujo.md" \
              "artifacts.md:references/artifacts.md" "delegation.md:references/delegation.md" \n              "casos-de-uso.md:references/casos-de-uso.md"; do
    copy="$dir/references/${pair%%:*}"
    [ -f "$copy" ] && ! cmp -s "$copy" "${pair##*:}" && err "$copy difiere de ${pair##*:}"
    [ -f "$copy" ] && ! grep -q "references/${pair%%:*}" "$dir/SKILL.md" && err "$copy no está enlazada desde su SKILL.md"
  done
  # flujo.md enlaza artifacts.md: la skill que lleve uno debe llevar el otro.
  [ -f "$dir/references/flujo.md" ] && [ ! -f "$dir/references/artifacts.md" ] && err "$dir: flujo.md sin artifacts.md"
  [ -f "$dir/references/casos-de-uso.md" ] && [ ! -f "$dir/references/delegation.md" ] && err "$dir: casos-de-uso.md sin delegation.md"
done

# Enlaces Markdown relativos de skills, agentes y referencias.
broken=$(find skills agents references profiles -name '*.md' | while IFS= read -r file; do
  base=$(dirname "$file")
  grep -o ']([^)#]*' "$file" | sed 's/^](//' | while IFS= read -r link; do
    case "$link" in ''|http*|mailto:*) continue ;; esac
    [ -e "$base/$link" ] || echo "$file: enlace roto $link"
  done
done)
[ -z "$broken" ] || { echo "$broken" | sed 's/^/ERROR: /'; fail=1; }

# Helper de commits duplicado a propósito.
cmp -s skills/gara-commit/scripts/gara_commit.py plugins/gara-commit/skills/commit/scripts/gara_commit.py || err "gara_commit.py difiere entre skill y plugin"
cmp -s skills/gara-commit/scripts/test_gara_commit.py plugins/gara-commit/skills/commit/scripts/test_gara_commit.py || err "test_gara_commit.py difiere entre skill y plugin"

[ "$fail" = 0 ] && echo "OK: $(ls -d skills/*/ | wc -l) skills, $(ls agents/*.md | wc -l) agentes"
exit "$fail"
