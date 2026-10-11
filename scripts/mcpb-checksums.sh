#!/usr/bin/env bash
# Add SHA256 lines for every immediate *.mcpb in DIR to a sha256sum file.
#
# Usage: mcpb-checksums.sh DIR SUMS
#
# SUMS may already hold lines for other release archives. Those lines stay,
# byte for byte and in their original order, including a final line with no
# trailing newline (a newline is inserted before the bundle lines). A line
# whose filename ends in .mcpb — including a GNU escaped line that starts
# with a backslash — is replaced, so a second run does not duplicate it.
# A directory with no bundles is an error and leaves SUMS untouched.
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: mcpb-checksums.sh DIR SUMS" >&2
  exit 2
fi

dir=$1
sums=$2

if [ ! -d "$dir" ]; then
  echo "mcpb-checksums: not a directory: ${dir}" >&2
  exit 1
fi

# True when the line is a sha256sum record for a name ending in .mcpb.
# GNU sha256sum prefixes a backslash when the name contains '\' or a newline.
mcpb_sum_line() {
  local line=$1
  local body=${line%$'\r'}
  case $body in
    \\*) body=${body#\\} ;;
  esac
  [[ $body =~ ^[[:xdigit:]]{64}\ \ (.*)$ ]] || return 1
  local name=${BASH_REMATCH[1]}
  name=${name%$'\r'}
  [[ $name == *.mcpb ]]
}

bundles=()
for path in "$dir"/*.mcpb; do
  # No match leaves the glob literal; a directory named *.mcpb is not a bundle.
  if [ -f "$path" ]; then
    bundles+=("$(basename -- "$path")")
  fi
done

if [ "${#bundles[@]}" -eq 0 ]; then
  echo "mcpb-checksums: no .mcpb files in ${dir}" >&2
  exit 1
fi

# A bundle name may contain a newline. Sorting on lines would split that name
# and hand sha256sum a path that is not the bundle. NUL keeps the name whole;
# names without a newline stay in the same LC_ALL=C order as a line sort.
mapfile -d '' names < <(printf '%s\0' "${bundles[@]}" | LC_ALL=C sort -z)

sums_dir=$(dirname -- "$sums")
tmp=$(mktemp "${sums_dir}/.mcpb-checksums.XXXXXX")
cleanup() {
  if [ -n "${tmp:-}" ] && [ -f "$tmp" ]; then
    rm -f -- "$tmp"
  fi
}
trap cleanup EXIT

# Keep every existing line that is not a .mcpb sum. read drops the delimiter
# and keeps the rest, including a trailing CR; printf puts the newline back,
# which also separates an unterminated final line from the bundle sums.
if [ -f "$sums" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    if mcpb_sum_line "$line"; then
      continue
    fi
    printf '%s\n' "$line"
  done < "$sums" > "$tmp"
fi

(
  cd -- "$dir" || exit 1
  sha256sum -- "${names[@]}"
) >> "$tmp"

if [ -f "$sums" ]; then
  chmod --reference="$sums" -- "$tmp"
else
  chmod 644 -- "$tmp"
fi

# Verify the temporary file from DIR before mv. A failed sha256sum -c must
# leave an existing SUMS byte for byte as it was.
if ! grep -E '^\\?[[:xdigit:]]{64}  .*\.mcpb$' -- "$tmp" | (
  cd -- "$dir" || exit 1
  sha256sum -c --strict -
); then
  echo "mcpb-checksums: sha256sum -c failed for .mcpb lines" >&2
  exit 1
fi

mv -f -- "$tmp" "$sums"
tmp=""
