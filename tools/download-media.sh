#!/bin/zsh
# Télécharge les images et sons du blog dans public/wp-content/uploads,
# en gardant les mêmes chemins que sur WordPress (les adresses restent valides).
# À lancer sur le Mac, depuis le dossier du site :  zsh tools/download-media.sh
# Relançable sans risque : les fichiers déjà présents sont sautés.
cd "$(dirname "$0")/.."
total=$(wc -l < tools/media-list.txt | tr -d ' ')
ok=0; skip=0; fail=0; i=0
: > tools/media-errors.txt
while IFS=$'\t' read -r dest url; do
  [[ -z "$dest" ]] && continue
  i=$((i+1))
  out="public/$dest"
  if [[ -s "$out" ]]; then skip=$((skip+1)); continue; fi
  mkdir -p "$(dirname "$out")"
  if curl -sSLf --retry 2 -m 60 -o "$out" "$url"; then
    ok=$((ok+1))
    # Réduit les photos trop grandes à 1600 px de large (sips est fourni avec macOS).
    case "${out:l}" in
      *.jpg|*.jpeg|*.png)
        w=$(sips -g pixelWidth "$out" 2>/dev/null | awk '/pixelWidth/{print $2}')
        [[ -n "$w" && "$w" -gt 1600 ]] && sips -Z 1600 "$out" >/dev/null 2>&1 ;;
    esac
  else
    fail=$((fail+1)); rm -f "$out"; echo "$url" >> tools/media-errors.txt
  fi
  printf "\r%d/%d  téléchargés %d · déjà là %d · échecs %d" $i $total $ok $skip $fail
done < tools/media-list.txt
echo
echo "Terminé. Échecs listés dans tools/media-errors.txt"
