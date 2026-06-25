# ── Colonius group website ──────────────────────────────────────────────────
# Content is fetched from the published Google Sheet at build time, so most
# updates need no code changes — just rebuild locally and/or push to GitHub.
#
#   make            → rebuild everything locally (CV PDF + site) into docs/
#   make site       → rebuild just the HTML site (fast; fetches the sheet)
#   make cv         → regenerate + compile the CV PDF, copy into docs/
#   make serve      → build the site and preview at http://localhost:8000
#   make deploy     → commit changed files (images/code) and push (CI deploys)
#   make redeploy   → force a GitHub rebuild after a SHEET-ONLY edit
#   make clean      → remove local LaTeX build artifacts
#   make help       → list targets
# ─────────────────────────────────────────────────────────────────────────────

# MacTeX bin (prepended onto the latexmk commands so latexmk and the tools it
# calls — pdflatex, biber — are found even from a non-login shell).
TEXBIN := /Library/TeX/texbin
MSG ?= Update site content

.PHONY: help all site cv serve deploy redeploy clean

help:            ## List targets
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed -E 's/:.*## / — /'

all: cv site     ## Rebuild CV PDF + website locally (docs/)

site:            ## Build the HTML site into docs/ (fetches the sheet)
	python3 build.py

cv:              ## Regenerate CV from the sheet, compile PDF, copy to docs/cv.pdf
	python3 gen_cv_lists.py
	# -gg: wipe intermediates and rebuild from scratch, so biblatex defernumbers
	# always renumbers cleanly when entries are added/removed (avoids stale "C0").
	PATH="$(TEXBIN):$$PATH" latexmk -gg -r cv/latexmkrc -cd -pdf -interaction=nonstopmode -file-line-error cv/Colonius.tex
	cp cv/Colonius.pdf docs/cv.pdf

serve: site      ## Build the site and preview at http://localhost:8000
	@echo "Serving docs/ at http://localhost:8000  (Ctrl+C to stop)"
	@cd docs && python3 -m http.server 8000

deploy:          ## Sync with GitHub, commit changes, and push -> builds & deploys
	git add -A
	@if git diff --cached --quiet; then \
	  echo "(no file changes to commit — for a sheet-only edit use 'make redeploy')"; \
	else \
	  git commit -m "$(MSG)"; \
	fi
	git pull --rebase origin main
	git push

redeploy:        ## Force a GitHub rebuild after a sheet-only edit (empty commit)
	git commit --allow-empty -m "Rebuild from updated spreadsheet"
	git push

clean:           ## Remove local LaTeX build artifacts
	PATH="$(TEXBIN):$$PATH" latexmk -C -cd cv/Colonius.tex
